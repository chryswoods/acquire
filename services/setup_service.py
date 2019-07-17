import sys
import json
import argparse
import os
import getpass

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from Acquire.Crypto import PrivateKey, Hash
from Acquire.ObjectStore import bytes_to_string, string_to_bytes

parser = argparse.ArgumentParser(
            description="Set up and configure an Acquire function "
                        "service (generate and upload keys, connect "
                        "to the cloud object store etc.)",
            epilog="setup_service is created to support Acquire, and "
                   "is distributed under the APACHE license",
            prog="setup_service.py")

parser.add_argument('-c', '--config', nargs=1,
                    help="The yaml configuration file that is used to "
                         "describe and configure the service")

parser.add_argument('-d', '--dry-run', action="store_true",
                    help="Don't do anything (dry run only)")

parser.add_argument('-v', '--verbose', action="store_true",
                    help="Verbose output")

args = parser.parse_args()

try:
    config_file = args.config[0]
except:
    config_file = None

dryrun = args.dry_run
verbose = args.verbose

service_file = "service.json"

if os.path.exists(service_file):
    with open(service_file, "r") as FILE:
        service_info = json.load(FILE)
        service_salt = service_info["salt"]

    while True:
        password = getpass.getpass(
                    prompt="Please enter the service primary password: ")

        password = Hash.multi_md5(password, service_salt)

        try:
            service_key = PrivateKey.from_data(service_info["key"],
                                               passphrase=password)
            break
        except:
            print("Password incorrect. Try again.")

    old_config = service_key.decrypt(string_to_bytes(service_info["config"]))
    old_config = json.loads(old_config)
    keep = True
else:
    while True:
        password = getpass.getpass(
            prompt="Please enter the service primary password: ")
        password2 = getpass.getpass(
            prompt="Please enter the password again: ")

        if password == password2:
            break

        print("Passwords not equal - please try again")

    service_salt = PrivateKey.random_passphrase()
    password = Hash.multi_md5(password, service_salt)

    old_config = None
    service_key = PrivateKey()
    service_key_data = service_key.to_data(passphrase=password)

with open(config_file, "r") as FILE:
    config = load(FILE, Loader=Loader)

if old_config is not None:
    if old_config["service"] != config["service"]:
        for key in config["service"].keys():
            if old_config["service"][key] != config["service"][key]:
                print("\nDisagree key = %s\n%s\n%s" %
                      (key, old_config["service"][key],
                       config["service"][key]))

        raise PermissionError("Config disagreement: %s vs %s" %
                              (config["service"], old_config["service"]))

    config = old_config

elif config is None:
    raise PermissionError("No service config loaded!")

if "credentials" not in config:
    config["credentials"] = {}

service_name = config["service"]["name"]
service_type = config["service"]["type"]
bucket = config["service"]["bucket"]

provider = config["service"]["provider"]["backend"]

try:
    provider_config = config["service"]["provider"][provider]
except:
    provider_config = {}


def run_command(cmd):
    if verbose:
        print(cmd)

    if not dryrun:
        os.system(cmd)


def generate_ssl_key(name, passphrase):
    """Generate a private/public pair of SSH keys called
       {name}.pem and {name}_public.pem, with the private
       key encrypted using the supplied passphrase. The
       names of the keys are returned
    """
    privkey = "%s.pem" % name
    pubkey = "%s_public.pem" % name

    cmd = "openssl genrsa -out %s -aes128 -passout pass:%s 2048" % (
                                            privkey, passphrase)
    run_command(cmd)

    cmd = "openssl rsa -pubout -in %s -out %s -passin pass:%s" % (
                                            privkey, pubkey, passphrase)
    run_command(cmd)

    if not (os.path.exists(privkey) and os.path.exists(pubkey)):
        raise PermissionError("Cannot find the necessary SSH keys!")

    # now get the fingerprint of the key
    cmd = "openssl rsa -in %s -passin pass:%s -pubout -outform DER | " \
          "openssl md5 -c" % (privkey, passphrase)
    lines = os.popen(cmd, "r").readlines()
    fingerprint = lines[0][0:-1]
    fingerprint = fingerprint.split(" ")[-1]

    return (privkey, pubkey, fingerprint)

if provider == "gcp":
    key = provider_config["key"]
    del provider_config["key"]
    with open(key, "r") as FILE:
        key = json.load(FILE)
    project = key["project_id"]
    unique_suffix = provider_config["suffix"]
    unique_salt = "%s%s" % (project, unique_suffix)

elif provider == "oci":
    # generate the key encrypted using an auto-generated password
    try:
        passphrase = config["credentials"]["passphrase"]
    except:
        passphrase = PrivateKey.random_passphrase()
        config["credentials"]["passphrase"] = passphrase

    try:
        key = config["credentials"]["key"]
        fingerprint = config["credentials"]["fingerprint"]
        generate_key = False
    except Exception as e:
        generate_key = True

    if generate_key:
        print("Generating new keys...")
        (privkey, pubkey, fingerprint) = generate_ssl_key("oci_key",
                                                          passphrase)
        with open(privkey, "r") as FILE:
            key = FILE.readlines()
        config["credentials"]["key"] = key
        config["credentials"]["fingerprint"] = fingerprint
        print("\n****\nPlease make sure you upload %s to OCI\n****\n" % pubkey)

    unique_salt = str(fingerprint)

else:
    raise TypeError("Cannot recognise the type of service that "
                    "is being configured. This should be either "
                    "gcp or oci")

# now save the configuration to disk
d = {}
d["key"] = service_key.to_data(passphrase=password)
d["salt"] = service_salt
d["config"] = bytes_to_string(service_key.encrypt(json.dumps(config)))
with open(service_file, "w") as FILE:
    FILE.write(json.dumps(d))

# package all of the config data into a dictionary
data = {}

login = {}

login["service_type"] = service_type
login["bucket"] = bucket

if provider == "gcp":
    login["credentials"] = key
    login["project"] = project
    login["unique_suffix"] = unique_suffix
elif provider == "oci":
    login["user"] = provider_config["user"]
    login["key_lines"] = key
    login["pass_phrase"] = passphrase
    login["fingerprint"] = fingerprint
    login["tenancy"] = provider_config["tenancy"]
    login["region"] = provider_config["region"]

data["LOGIN"] = login

bucket = {"bucket": bucket}

if provider == "oci":
    bucket["compartment"] = provider_config["compartment"]

data["BUCKET"] = bucket

if provider == "oci" and service_type == "storage":
    data["STORAGE_COMPARTMENT"] = provider_config["compartment"]

# password used to verify that the Acquire function is able to
# decrypt the skeleton key for the Acquire service in this object store
data["PASSWORD"] = password
data["CLOUD_BACKEND"] = provider

if verbose:
    print("\nUploaded config\n%s" % data)

# Create a key to encrypt the config
config_key = PrivateKey()

secret_config = config_key.encrypt(json.dumps(data).encode("utf-8"))
secret_config = bytes_to_string(secret_config)

passphrase = PrivateKey.random_passphrase()

secret_key = json.dumps(config_key.to_data(passphrase=passphrase))

with open("secret_key", "w") as FILE:
    FILE.write("%s\n" % passphrase)

print("\n************************************************")
print("Have written the new secret key to 'secret_key'.")
print("Please remember to rebuild the docker container so ")
print("so that it can be packaged into the function.")
print("************************************************\n")

# Now update the application with this information
cmd = "fn config app %s SECRET_CONFIG '%s'" % (service_name, secret_config)
run_command(cmd)

cmd = "fn config app %s SECRET_KEY '%s'" % (service_name, secret_key)
run_command(cmd)
