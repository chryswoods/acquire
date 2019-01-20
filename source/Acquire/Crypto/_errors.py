

__all__ = ["WeakPassphraseError", "KeyManipulationError",
           "SignatureVerificationError",
           "DecryptionError", "OTPError"]


class WeakPassphraseError(Exception):
    pass


class KeyManipulationError(Exception):
    pass


class SignatureVerificationError(Exception):
    pass


class DecryptionError(Exception):
    pass


class OTPError(Exception):
    pass
