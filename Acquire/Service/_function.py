
import json as _json
from io import BytesIO as _BytesIO

__all__ = ["call_function", "pack_arguments", "unpack_arguments",
           "create_return_value", "pack_return_value", "unpack_return_value",
           "exception_to_safe_exception", "exception_to_string"]


def _get_signing_certificate(fingerprint=None):
    """Return the signing certificate for this service"""
    from ._service_account import get_service_private_certificate \
        as _get_service_private_certificate
    return _get_service_private_certificate(fingerprint=fingerprint)


def _get_key(key, fingerprint=None):
    """The user may pass the key in multiple ways. It could just be
       a key. Or it could be a function that gets the key on demand.
       Or it could be a dictionary that has the key stored under
       "encryption_public_key"
    """
    from Acquire.Crypto import PublicKey as _PublicKey
    from Acquire.Crypto import PrivateKey as _PrivateKey

    if key is None:
        return None
    elif isinstance(key, _PublicKey) or isinstance(key, _PrivateKey):
        key = key
    elif isinstance(key, dict):
        try:
            key = key["encryption_public_key"]
        except:
            key = None

        if key is not None:
            from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
            key = _PublicKey.read_bytes(_string_to_bytes(key))
    else:
        key = key(fingerprint=fingerprint)

    if fingerprint is not None:
        if key is None:
            from Acquire.Crypto import KeyManipulationError
            raise KeyManipulationError(
                "Cannot find the key with fingerprint %s!" % fingerprint)
        elif key.fingerprint() != fingerprint:
            from Acquire.Crypto import KeyManipulationError
            raise KeyManipulationError(
                "Cannot find a key with the required fingerprint (%s). "
                "The only key has fingerprint %s" %
                (fingerprint, key.fingerprint()))

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

    from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
    from Acquire.ObjectStore import get_datetime_now_to_string \
        as _get_datetime_now_to_string

    if response_key:
        result["encryption_public_key"] = _bytes_to_string(
                                            response_key.bytes())

        if public_cert:
            result["sign_with_service_key"] = public_cert.fingerprint()

    elif sign_result and (key is None):
        from Acquire.Service import PackingError
        raise PackingError(
            "You cannot ask the service to sign the response "
            "without also providing a key to encrypt it with too")

    if key is None:
        result["synctime"] = _get_datetime_now_to_string()

    result = _json.dumps(result).encode("utf-8")

    if key is not None:
        response = {}

        result_data = key.encrypt(result)

        if sign_result:
            # sign using the signing certificate for this service
            signature = _get_signing_certificate(
                            fingerprint=sign_result).sign(result_data)
            response["signature"] = _bytes_to_string(signature)

        response["data"] = _bytes_to_string(result_data)
        response["encrypted"] = True
        response["fingerprint"] = key.fingerprint()
        response["synctime"] = _get_datetime_now_to_string()
        result = _json.dumps(response).encode("utf-8")

    elif sign_result:
        from Acquire.Service import PackingError
        raise PackingError(
            "The service must encrypt the response before it "
            "can be signed.")

    return result


def pack_arguments(args, key=None, response_key=None, public_cert=None):
    """Pack the passed arguments, optionally encrypted using the passed key"""
    return pack_return_value(args, key, response_key, public_cert)


def exception_to_safe_exception(e):
    """Convert the passed exception to a "safe" exception - this is one
       that can be copied because it does not hold references to any
       local data
    """
    if not issubclass(e.__class__, Exception):
        return TypeError(str(e))

    import tblib as _tblib
    tb = _tblib.Traceback(e.__traceback__)
    e.__traceback__ = tb.as_traceback()

    return e


def unpack_arguments(args, key=None, public_cert=None, is_return_value=False,
                     function=None, service=None):
    """Call this to unpack the passed arguments that have been encoded
       as a json string, packed using pack_arguments. This will always
       return a dictionary. If there are no arguments, then an empty
       dictionary will be returned. If 'public_cert' is supplied then
       a signature of the result will be verified using 'public_cert'

       This function is also called as unpack_return_value, in which
       case is_return_value is set as True. The 'function' on 'service'
       that was called (or to be called) can also be passed. These
       are used to help provide more context for error messages.
    """
    if not (args and len(args) > 0):
        return {}

    # args should be a json-encoded utf-8 string
    try:
        data = _json.loads(args)
    except Exception as e:
        from Acquire.Service import UnpackingError
        raise UnpackingError("Cannot decode json from '%s' : %s" %
                             (data, str(e)))

    while not isinstance(data, dict):
        if not (data and len(data) > 0):
            return {}

        try:
            data = _json.loads(data)
        except Exception as e:
            from Acquire.Service import UnpackingError
            raise UnpackingError(
                "Cannot decode a json dictionary from '%s' : %s" %
                (data, str(e)))

    if is_return_value:
        # extra checks if this is a return value of a function rather
        # than the arguments
        if len(data) == 1 and "error" in data:
            from Acquire.Service import RemoteFunctionCallError
            raise RemoteFunctionCallError(
                "Calling %s on %s resulted in error: '%s'" %
                (function, service, data["error"]))

        if "status" in data:
            if data["status"] != 0:
                if "exception" in data:
                    _unpack_and_raise(function, service, data["exception"])
                else:
                    raise RemoteFunctionCallError(
                        "Calling %s on %s exited with status %d: %s" %
                        (function, service, data["status"], data["message"]))

    try:
        is_encrypted = data["encrypted"]
    except:
        is_encrypted = False

    from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

    if public_cert:
        if not is_encrypted:
            raise UnpackingError(
                "Cannot unpack the result of %s on %s as it should be "
                "signed, but it isn't! (only encrypted results are signed) "
                "Response == %s" % (function, service, _json.dumps(data)))

        try:
            signature = _string_to_bytes(data["signature"])
        except:
            signature = None

        if signature is None:
            raise UnpackingError(
                "We requested that the data was signed "
                "when calling %s on %s, but a signature was not provided!" %
                (function, service))

    if is_encrypted:
        encrypted_data = _string_to_bytes(data["data"])

        try:
            fingerprint = data["fingerprint"]
        except:
            fingerprint = None

        if public_cert:
            try:
                public_cert.verify(signature, encrypted_data)
            except Exception as e:
                raise UnpackingError(
                    "The signature of the returned data "
                    "from calling %s on %s "
                    "is incorrect and does not match what we "
                    "know! %s" % (function, service, str(e)))

        decrypted_data = _get_key(key, fingerprint).decrypt(encrypted_data)
        return unpack_arguments(decrypted_data,
                                is_return_value=is_return_value,
                                function=function, service=service)
    else:
        return data


def unpack_return_value(return_value, key=None, public_cert=None,
                        function=None, service=None):
    """Call this to unpack the passed arguments that have been encoded
       as a json string, packed using pack_arguments"""
    return unpack_arguments(return_value, key, public_cert,
                            is_return_value=True, function=function,
                            service=service)


class _UnicodeDecodeError(Exception):
    """Fake UnicodeDecodeError as the real one has a strange
       constructor syntax
    """
    pass


def _unpack_and_raise(function, service, exdata):
    """This function unpacks the exception whose data is in 'exdata',
       and raises it in the current thread. Additional information
       is added to the error message to include the remote function
       that was called (function) and the service on which it
       was called.

       The exdata should be a dictionary containing:

       class: class name of the exception
       module: module containing the exception
       traceback: json-serialised traceback (dumped using tbblib)
       error: error message of the exception
    """
    try:
        import importlib as _importlib
        import tblib as _tblib

        if exdata["class"] == "UnicodeDecodeError":
            exclass = _UnicodeDecodeError
        else:
            mod = _importlib.import_module(exdata["module"])
            exclass = getattr(mod, exdata["class"])

        ex = exclass("Error calling '%s' on '%s': %s" %
                     (function, service, exdata["error"]))
        ex.__traceback__ = _tblib.Traceback.from_dict(
                                    exdata["traceback"]).as_traceback()
    except Exception as e:
        from Acquire.Service import RemoteFunctionCallError
        from Acquire.Service import exception_to_string \
            as _exception_to_string
        raise RemoteFunctionCallError(
            "An exception occurred while calling '%s' on '%s'\n\n"
            "CAUSE: %s\n\nEXDATA: %s" %
            (function, service, _exception_to_string(e), exdata))

    raise ex


def exception_to_string(e):
    """This function returns a simple string that represents the exception,
       including the first line of the traceback.
    """
    import traceback as _traceback
    lines = _traceback.format_exception(e.__class__, e, e.__traceback__,
                                        limit=2)

    return "".join(lines)


def _call_local_function(service, function=None, args_key=None,
                         response_key=None, public_cert=None, args=None):
    """This is an internal version of call_function which short-cuts
       the whole process if the function is being called in the local
       service
    """
    response_key = _get_key(response_key)

    if function is not None:
        args["function"] = function

    if response_key:
        args_json = pack_arguments(args, args_key, response_key.public_key(),
                                   public_cert=public_cert)
    else:
        args_json = pack_arguments(args, args_key)

    result = service._call_local_function(function, args_json)

    # Now unpack the results
    return unpack_return_value(result, response_key, public_cert,
                               function=function, service=service)


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
    if args is None:
        args = {}

    for key, value in kwargs.items():
        args[key] = value

    from Acquire.Service import is_running_service as _is_running_service
    from Acquire.ObjectStore import get_datetime_now_to_string \
        as _get_datetime_now_to_string

    service = None

    if _is_running_service():
        from Acquire.Service import get_this_service as _get_this_service
        try:
            service = _get_this_service(need_private_access=True)
        except:
            pass

        if service is not None:
            if service.canonical_url() == service_url:
                return _call_local_function(service, function, args_key,
                                            response_key, public_cert, args)

    response_key = _get_key(response_key)

    if function is not None:
        args["function"] = function

    if response_key:
        args_json = pack_arguments(args, args_key, response_key.public_key(),
                                   public_cert=public_cert)
    else:
        args_json = pack_arguments(args, args_key)

    response = None
    try:
        from Acquire.Stubs import requests as _requests
        response = _requests.post(service_url, data=args_json, timeout=15.0)
    except Exception as e:
        from Acquire.Service import RemoteFunctionCallError
        raise RemoteFunctionCallError(
            "Cannot call remote function '%s' at '%s' because of a possible "
            "network issue: requests exeption = '%s'" %
            (function, service_url, str(e)))

    args = None
    args_json = None
    args_key = None

    if response.status_code != 200:
        from Acquire.Service import RemoteFunctionCallError
        raise RemoteFunctionCallError(
            "Cannot call remote function '%s' as '%s'. Invalid error code "
            "%d returned. Message:\n%s" %
            (function, service_url,
             response.status_code, str(response.content)))

    if response.encoding == "utf-8" or response.encoding is None:
        result = response.content.decode("utf-8")
    else:
        from Acquire.Service import RemoteFunctionCallError
        raise RemoteFunctionCallError(
            "Cannot call remote function '%s' as '%s'. Invalid data encoding "
            "%s returned. Message:\n%s" %
            (function, service_url,
             response.encoding, str(response.content)))

    return unpack_return_value(result, response_key, public_cert,
                               function=function, service=service_url)
