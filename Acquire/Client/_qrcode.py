
__all__ = ["create_qrcode", "has_qrcode"]


def has_qrcode():
    """ Return whether or not we support creating QR codes
    
        Returns:
            None
    """
    try:
        import qrcode as _qrcode
        return _qrcode is not None
    except:
        return False


def create_qrcode(uri):
    """ Return a QR code for the passed URI
    
        Args:
            uri (str): URI for which to create QR code
        Returns:
            Image: Image containing QR code
    """
    try:
        import qrcode as _qrcode
    except:
        from Acquire.Client import QRCodeError
        raise QRCodeError("Cannot find the qrcode library needed to generate "
                          "QR codes. Please install and try again.")

    return _qrcode.make(uri)
