
from Acquire.Service import get_service_account_bucket
from Acquire.Service import create_return_value
from Acquire.Service import Service, get_this_service

from Acquire.ObjectStore import ObjectStore

from Acquire.Identity import UserAccount

from Acquire.Crypto import PublicKey, PrivateKey, OTP


class ExistingAccountError(Exception):
    pass


class RegisterAccountError(Exception):
    pass


def run(args):
    """This function will allow a user to register an account with a
       username and password"""

    status = 0
    message = None
    provisioning_uri = None

    username = args["username"]
    password = args["password"]

    # generate a sanitised version of the username
    user_account = UserAccount(username)

    # generate the encryption keys and otp secret
    privkey = PrivateKey()
    pubkey = privkey.public_key()
    otp = OTP()

    # save the encrypted private key (encrypted using the user's password)
    # and encrypted OTP secret (encrypted using the public key)
    user_account.set_keys(privkey.bytes(password), pubkey.bytes(),
                          otp.encrypt(pubkey))

    # now log into the central identity account to either register
    # the user, or to update to a new password
    bucket = get_service_account_bucket()
    account_key = "identity/accounts/%s" % user_account.sanitised_name()

    service_info = get_this_service()

    try:
        provisioning_uri = otp.provisioning_uri(
                username, issuer="%s@%s" %
                (service_info.service_type(), service_info.hostname()))
    except Exception as e:
        raise RegisterAccountError(
            "Cannot generate a provisioning_uri to register "
            "an account %s on service %s. Error equals %s"
            % (username, str("HELLO"), str(e)))

    try:
        existing_data = ObjectStore.get_object_from_json(bucket,
                                                         account_key)
    except:
        existing_data = None

    message = "Created a new account for '%s'" % username
    status = 0

    if existing_data is None:
        # save the new account details
        ObjectStore.set_object_from_json(bucket, account_key,
                                         user_account.to_data())

        # need to update the "whois" database with the uuid of this user
        ObjectStore.set_string_object(bucket,
                                      "identity/whois/%s" %
                                      user_account.uuid(),
                                      user_account.username())
    else:
        # The account already exists. See if this is a password change
        # request
        old_password = None

        try:
            old_password = args["old_password"]
        except:
            raise ExistingAccountError(
                "An account by this name already exists!")

        if old_password != password:
            # this is a change of password request - validate that
            # the existing password unlocks the existing key
            user_account = UserAccount.from_data(existing_data)

            testkey = PrivateKey.read_bytes(user_account.private_key(),
                                            old_password)

            # decrypt the old secret
            old_secret = testkey.decrypt(user_account.otp_secret())

            # now encrypt the secret with the new key
            new_key = PublicKey.read_bytes(pubkey)
            new_secret = new_key.encrypt(old_secret)

            user_account.set_keys(privkey, pubkey, new_secret)

            # save the new account details
            ObjectStore.set_object_from_json(bucket, account_key,
                                             user_account.to_data())

            message = "Updated the password for '%s'" % username
        else:
            message = "No need to change account '%s'" % username

    return_value = create_return_value(status, message)

    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri

    return return_value
