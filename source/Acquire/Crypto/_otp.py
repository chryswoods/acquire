
from ._keys import PublicKey as _PublicKey

from ._errors import OTPError

__all__ = ["OTP"]


class OTP:
    """This class handles everything to do with obtaining and
       verifying a one-time-password"""
    def __init__(self):
        """This creates a new one-time-password"""
        try:
            import pyotp as _pyotp
        except:
            raise OTPError(
                "Cannot create a one-time-password as the "
                "pyotp module is not available. Please install and try again")

        self._secret = _pyotp.random_base32()

    def __str__(self):
        """Return a string representation of this OTP"""
        return "OTP()"

    @staticmethod
    def decrypt(secret, key):
        """Construct a OTP from the passed encrypted secret
           that will be decrypted with the passed private key"""
        otp = OTP()
        otp._secret = key.decrypt(secret).decode("utf-8")

        return otp

    def encrypt(self, key):
        """This uses the passed public key to encrypt and return the
           secret"""
        return key.encrypt(self._secret.encode("utf-8"))

    def _totp(self):
        """Return the time-based one-time-password based on this secret"""
        try:
            import pyotp as _pyotp
            return _pyotp.totp.TOTP(self._secret)
        except:
            raise OTPError("You cannot get a null OTP - create one first!")

    def provisioning_uri(self, username, issuer="Acquire"):
        """Return the provisioning URI, assuming this secret is
           for the user called 'username' and is issued by 'issuer'"""
        return self._totp().provisioning_uri(username, issuer_name=issuer)

    def verify(self, code):
        """Verify that the passed code is correct. This raises an exception
           if the code is incorrect, or does nothing if the code is correct"""

        # the OTP is valid for 1 minute. We will extend this so that
        # it is valid for 3 minutes (1 minute before and after). This
        # improves usability and tolerance for clock drift with only
        # minor increase in OTP validity time
        if not self._totp().verify(code, valid_window=1):
            raise OTPError("The passed OTP code is incorrect")

        # note that, ideally, we need to save whether or not this code
        # has been used, as we need to prevent the case of someone
        # eves-dropping on the password and code and using it again
        # within the 3-minute window. We will leave this to the caller
        # of this function to record!
