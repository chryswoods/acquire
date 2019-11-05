
from Acquire.Service import get_this_service

from Acquire.Identity import Authorisation


def run(args):
    """This function is called by a user to recover or reset their primary
       one-time-password secret. This is used, e.g. if a user has changed
       their phone, or if they think the secret has been compromised, or
       if they have lost the secret completely (in which case they will
       need to log in using a backup method and then call this function
       from that login)

       The user will need to pass in a validated Authorisation, meaning
       they must have a login by at least one method (e.g. a pre-approved
       device or a one-time-login requested via backup codes or via
       an admin-authorised login)
    """

    auth = Authorisation.from_data(args["authorisation"])

    try:
        reset_otp = bool(args["reset_otp"])
    except:
        reset_otp = False

    auth.verify(resource="recover_otp")

    identity_uid = auth.identity_uid()

    service = get_this_service(need_private_access=False)

    if service.uid() != identity_uid:
        raise PermissionError(
            "You can only reset the OTP on the identity service on "
            "which the user is registered! %s != %s" %
            (service.uid(), identity_uid))

    user_uid = auth.user_uid()

    # move all of below into UserCredentials
    from Acquire.ObjectStore import ObjectStore as _ObjectStore
    from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
    from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
    from Acquire.Crypto import PrivateKey as _PrivateKey
    from Acquire.Crypto import OTP as _OTP

    key = "%s/credentials/%s/%s" % (_user_root, user_uid, user_uid)
    secrets = _ObjectStore.get_object_from_json(bucket=bucket, key=key)

    privkey = _PrivateKey.from_data(data=secrets["private_key"],
                                    passphrase=password)

    data = _string_to_bytes(secrets["otpsecret"])
    otpsecret = privkey.decrypt(data)

    # all ok - we have validated we have the right password and can
    # see the original otpsecret

    if reset_otp:
        otp = _OTP()
        otpsecret = otp.encrypt(privkey.public_key())
        secrets["otpsecret"] = _bytes_to_string(otpsecret)
        _ObjectStore.set_object_from_json(bucket=bucket, key=key, data=secrets)
    else:
        otp = _OTP(secret=otpsecret)

    return otp
