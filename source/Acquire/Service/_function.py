
import json as _json

try:
    import pycurl as _pycurl
except:
    _pycurl = None

from io import BytesIO as _BytesIO

from Acquire.Crypto import PublicKey as _PublicKey
from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from ._errors import PackingError, UnpackingError, RemoteFunctionCallError

__all__ = ["call_function", "pack_arguments", "unpack_arguments",
           "create_return_value", "pack_return_value", "unpack_return_value"]


def _get_signing_certificate():
    """Return the signing certificate for this service"""
    from ._service_account import get_service_private_certificate \
        as _get_service_private_certificate
    return _get_service_private_certificate()


def _get_key(key):
    """The user may pass the key in multiple ways. It could just be
       a key. Or it could be a function that gets the key on demand.
       Or it could be a dictionary that has the key stored under
       "encryption_public_key"
    """
    if key is None:
        return None
    elif isinstance(key, _PublicKey):
        return key
    elif isinstance(key, dict):
        try:
            key = key["encryption_public_key"]
        except:
            return None

        key = _PublicKey.read_bytes(_string_to_bytes(key))
    else:
        try:
            key = key()
        except:
            pass

    return key


def create_return_value(status, message, log=None, error=None):
    """Convenience functiont that creates the start of the
       return_value dictionary, setting the "status" key
       to the value of 'status', the "message" key to the
       value of 'message' and the "log" key to the value
       of 'log'. If 'error' is passed, then this signifies
       an exception, which will be packed and returned.
       This returns a simple dictionary, which
       is ready to be packed into a json string
    """

    if error:
        if isinstance(error, Exception):
            import traceback as _traceback

            status = -2
            message = "%s: %s\nTraceback:\n%s" % (
                str(error.__class__.__name__),
                " : ".join(error.args),
                "".join(_traceback.format_tb(error.__traceback__)))
        else:
            status = -1
            message = str(error)

    return_value = {}
    return_value["status"] = status
    return_value["message"] = message

    if log:
        return_value["log"] = log

    return return_value


def pack_return_value(result, key=None, response_key=None, public_cert=None):
    """Pack the passed result into a json string, optionally
       encrypting the result with the passed key, and optionally
       supplying a public response key, with which the function
       being called should encrypt the response. If public_cert is
       provided then we will ask the service to sign their response.
       Note that you can only ask the service to sign their response
       if you provide a 'reponse_key' for them to encrypt it with too
    """

    try:
        sign_result = key["sign_with_service_key"]
    except:
        sign_result = False

    key = _get_key(key)
    response_key = _get_key(response_key)

    if response_key:
        result["encryption_public_key"] = _bytes_to_string(
                                            response_key.bytes())

        if public_cert:
            result["sign_with_service_key"] = True

    elif public_cert:
        raise PackingError(
            "You cannot ask the service to sign the response "
            "without also providing a key to encrypt it with too")

    result = _json.dumps(result).encode("utf-8")

    if key:
        response = {}

        result_data = key.encrypt(result)

        if sign_result:
            # sign using the signing certificate for this service
            signature = _get_signing_certificate().sign(result_data)
            response["signature"] = _bytes_to_string(signature)

        response["data"] = _bytes_to_string(result_data)
        response["encrypted"] = True
        result = _json.dumps(response).encode("utf-8")

    return result


def pack_arguments(args, key=None, response_key=None, public_cert=None):
    """Pack the passed arguments, optionally encrypted using the passed key"""
    return pack_return_value(args, key, response_key, public_cert)


def unpack_arguments(args, key=None, public_cert=None):
    """Call this to unpack the passed arguments that have been encoded
       as a json string, packed using pack_arguments. This will always
       return a dictionary. If there are no arguments, then an empty
       dictionary will be returned. If 'public_cert' is supplied then
       a signature of the result will be verified using 'public_cert'
    """
    if not (args and len(args) > 0):
        return {}

    # args should be a json-encoded utf-8 string
    try:
        data = _json.loads(args)
    except Exception as e:
        raise UnpackingError("Cannot decode json from '%s' : %s" %
                             (data, str(e)))

    while not isinstance(data, dict):
        if not (data and len(data) > 0):
            return {}

        try:
            data = _json.loads(data)
        except Exception as e:
            raise UnpackingError(
                "Cannot decode a json dictionary from '%s' : %s" %
                (data, str(e)))

    if len(data) == 1 and "error" in data:
        raise RemoteFunctionCallError(
            "Server returned the error string: '%s'" % (data["error"]))

    if "status" in data:
        if data["status"] != 0:
            raise RemoteFunctionCallError(
                "Function exited with status %d: %s" % (data["status"],
                                                        data["message"]))

    try:
        is_encrypted = data["encrypted"]
    except:
        is_encrypted = False

    if public_cert:
        if not is_encrypted:
            raise UnpackingError(
                "Cannot unpack the result as it should be "
                "signed, but it isn't! (only encrypted results are signed) "
                "Response == %s" % _json.dumps(data))

        try:
            signature = _string_to_bytes(data["signature"])
        except:
            signature = None

        if signature is None:
            raise UnpackingError(
                "We requested that the data was signed "
                "but a signature was not provided!")

    if is_encrypted:
        encrypted_data = _string_to_bytes(data["data"])

        if public_cert:
            try:
                public_cert.verify(signature, encrypted_data)
            except Exception as e:
                raise UnpackingError(
                    "The signature of the returned data "
                    "is incorrect and does not match what we "
                    "know! %s" % str(e))

        decrypted_data = _get_key(key).decrypt(encrypted_data)
        return unpack_arguments(decrypted_data.decode("utf-8"))
    else:
        return data


def unpack_return_value(return_value, key=None, public_cert=None):
    """Call this to unpack the passed arguments that have been encoded
       as a json string, packed using pack_arguments"""
    return unpack_arguments(return_value, key, public_cert)


def call_function(service_url, function=None, args_key=None, response_key=None,
                  public_cert=None, args=None, **kwargs):
    """Call the remote function called 'function' at 'service_url' passing
       in named function arguments in 'kwargs'. If 'args_key' is supplied,
       then encrypt the arguments using 'args'. If 'response_key'
       is supplied, then tell the remote server to encrypt the response
       using the public version of 'response_key', so that we can
       decrypt it in the response. If 'public_cert' is supplied then
       we will ask the service to sign their response using their
       service signing certificate, and we will validate the
       signature using 'public_cert'
    """
    if _pycurl is None:
        raise RemoteFunctionCallError(
            "Cannot call remote functions as "
            "the pycurl module cannot be imported! It needs "
            "to be installed into this python session...")

    response_key = _get_key(response_key)

    if args is None:
        args = {}

    if function is not None:
        args["function"] = function

    for key, value in kwargs.items():
        args[key] = value

    if response_key:
        args_json = pack_arguments(args, args_key, response_key.public_key(),
                                   public_cert=public_cert)
    else:
        args_json = pack_arguments(args, args_key)

    buffer = _BytesIO()
    c = _pycurl.Curl()
    c.setopt(c.URL, service_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.POSTFIELDS, args_json)

    args = None
    args_json = None
    args_key = None

    try:
        c.perform()
        c.close()
    except _pycurl.error as e:
        raise RemoteFunctionCallError(
            "Cannot call remote function '%s' at  '%s' because of a possible "
            "network issue: curl errorcode %s, message '%s'" %
            (function, service_url, e.args[0], e.args[1]))
    except Exception as e:
        raise RemoteFunctionCallError(
            "Cannot call remote function '%s' at '%s' because of a possible "
            "nework issue: %s" % (function, service_url, str(e)))

    result = buffer.getvalue().decode("utf-8")

    # Now unpack the results
    try:
        result = unpack_return_value(result, response_key, public_cert)
    except Exception as e:
        raise RemoteFunctionCallError(
            "Error calling '%s' at '%s': %s" % (function, service_url, str(e)))

    if len(result) == 1 and "error" in result:
        raise RemoteFunctionCallError(
            "Error calling '%s' at '%s': '%s'" % (function, service_url,
                                                  result["error"]))
    elif "status" in result:
        if result["status"] != 0:
            raise RemoteFunctionCallError(
                "Error calling '%s' at '%s'. Server returned "
                "error code '%d' with message '%s'" %
                (function, service_url, result["status"], result["message"]))

    return result
