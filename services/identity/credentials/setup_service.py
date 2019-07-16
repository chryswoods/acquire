
import sys
import json
import argparse

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from Acquire.Crypto import PrivateKey
from Acquire.ObjectStore import bytes_to_string

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

args = parser.parse_args()

config_file = args.config

with open(config_file, "r") as FILE:
    config = load(FILE, Loader=Loader)

service_name = config["service"]["name"]
service_type = config["service"]["type"]
bucket = config["service"]["bucket"]

provider = config["service"]["provider"]["backend"]

try:
    provider_config = config["service"]["provider"][provider]
except:
    provider_config = {}

def generate_ssl_key(name, passphrase):
    cmd = "openssl genrsa -out %s.pem -aes128 -passout pass:%s 2048" % (name,passphrase)
    os.system(cmd)
    cmd = "openssl rsa -pubout -in %s.pem -out %s_public.pem -passin pass:%s" % (name,name,passphrase)
    os.system(cmd)

    return ("%s.pem" % name, "%s_public.pem" % name)

if provider == "gcp":
    key = provider_config["key"]
    del provider_config["key"]
    with open(key, "r") as FILE:
        key = json.load(FILE)
    passphrase = None

elif provider == "oci":
    # generate the key encrypted using an auto-generated password
    passphrase = PrivateKey.random_passphrase()
    (privkey, pubkey) = generate_ssl_key("oci_key", passphrase)
    with open(privkey, "r") as FILE:
        key = FILE.readlines()

    # make sure that the private key can be read using
    # this passphrase
    testkey = PrivateKey.read(privkey, passphrase)

    print("Please make sure you upload %s to OCI" % pubkey)

else:
    raise TypeError("Cannot recognise the type of service that "
                    "is being configured. This should be either "
                    "gcp or oci")

# package all of the config data into a dictionary
data = {}

data["service_type"] = service_type
data["bucket"] = bucket
data["key"] = key
data["passphrase"] = None

for key in provider_config.keys():
    data[key] = provider_config[key]

## Create a key to encrypt the config
config_key = PrivateKey()

secret_config = config_key.encrypt(json.dumps(data).encode("utf-8"))
secret_config = bytes_to_string(secret_config)

passphrase = PrivateKey.random_passphrase()

secret_key = config_key.to_data(passphrase=passphrase)

with open("../secret_key", "w") as FILE:
    FILE.write("%s\n" % passphrase)

print("Have written the secret key to ../secret_key so that it "
      "can be packaged into the function using Docker")

def run_command(cmd):
    if verbose:
        print(cmd)

    if not dryrun:
        os.system(cmd)

# Now update the application with this information
cmd = "fn config app %s SECRET_CONFIG '%s'" % (service_name, secret_config)
run_command(cmd)

cmd = "fn config app %s SECRET_KEY '%s'" % (service_name, secret_key)
run_command(cmd)