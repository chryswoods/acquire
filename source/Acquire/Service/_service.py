
import uuid as _uuid
import json as _json
from copy import deepcopy as _deepcopy
import datetime as _datetime

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
from Acquire.ObjectStore import get_datetime_now as _get_datetime_now
from Acquire.ObjectStore import datetime_to_string as _datetime_to_string
from Acquire.ObjectStore import string_to_datetime as _string_to_datetime

from ._function import call_function as _call_function

__all__ = ["Service"]


class ServiceError(Exception):
    pass


class Service:
    """This class represents a service in the system. Services
       will either be identity services, access services,
       storage services or accounting services.
    """
    def __init__(self, service_type=None, service_url=None):
        """Construct a new service of the specified type, with
           the specified URL."""
        self._service_type = service_type
        self._service_url = service_url
        self._canonical_url = service_url
        self._skeleton_key = None
        self._uid = None
        self._pubcert = None
        self._pubkey = None

        if self._service_type:
            if self._service_type not in ["identity", "access",
                                          "accounting", "storage"]:
                raise ServiceError("Services of type '%s' are not allowed!" %
                                   self._service_type)

            self._uid = str(_uuid.uuid4())
            self._skeleton_key = _PrivateKey()

            self._privkey = _PrivateKey()
            self._privcert = _PrivateKey()

            self._pubkey = self._privkey.public_key()
            self._pubcert = self._privcert.public_key()

            # generate 'dummy' old keys - these will be replaced as
            # the real keys are updated
            self._lastkey = _PrivateKey()
            self._lastcert = self._lastkey.public_key()

            self._last_key_update = _get_datetime_now()
            self._key_update_interval = 3600 * 24 * 7  # update keys weekly

    def __str__(self):
        return "%s(url=%s, uid=%s)" % (self.__class__.__name__,
                                       self.canonical_url(),
                                       self.uid())

    def uuid(self):
        """Synonym for uid"""
        return self.uid()

    def uid(self):
        """Return the uuid of this service. This MUST NEVER change, as
           the UID uniquely identifies this service to all other
           services
        """
        if self._uid is None:
            self.refresh_keys()

        return self._uid

    def service_type(self):
        """Return the type of this service"""
        return self._service_type

    def is_locked(self):
        """Return whether or not this service object is locked. Locked
           service objects don't contain copies of any private keys,
           and can be safely shared as a means of distributing public
           keys and certificates
        """
        return self._skeleton_key is None

    def is_unlocked(self):
        """Return whether or not this service object is unlocked. Unlocked
           service objects have access to the skeleton key and other private
           keys. They should only run on the service. Locked service objects
           are what are returned by services to provide public keys and
           public certificates
        """
        return self._skeleton_key is not None

    def assert_unlocked(self):
        """Assert that this service object is unlocked"""
        if self.is_locked():
            raise ServiceError(
                "Cannot complete operation as the service account '%s' "
                "is locked" % str(self))

    def last_key_update(self):
        """Return the datetime when the key and certificate of this
           service were last updated
        """
        try:
            return self._last_key_update
        except:
            return None

    def key_update_interval(self):
        """Return the time delta between server key updates"""
        try:
            return _datetime.timedelta(seconds=self._key_update_interval)
        except:
            return _datetime.timedelta(seconds=1)

    def should_refresh_keys(self):
        """Return whether the keys and certificates need to be refreshed
           - i.e. more than 'key_update_interval' has passed since the last
           key update
        """
        try:
            return _get_datetime_now() > (self._last_key_update +
                                          self.key_update_interval())
        except:
            return True

    def refresh_keys(self):
        """Refresh the keys and certificates"""
        if self.is_unlocked():
            # actually regenerate keys for the service - first save
            # the old private key (so we can decrypt data decrypted using
            # the old public key) and the old public certificate, so we
            # can verify data signed using the old private certificate
            self._lastkey = self._privkey
            self._lastcert = self._pubcert

            # now generate a new key and certificate
            self._privkey = _PrivateKey()
            self._privcert = _PrivateKey()
            self._pubkey = self._privkey.public_key()
            self._pubcert = self._privcert.public_key()

            # update the refresh time
            self._last_key_update = _get_datetime_now()
        else:
            # if our keys are old then pull the new ones from the server
            if self._pubcert is None:
                # we are initialising from scratch - hope this is over https
                response = _call_function(self._service_url,
                                          response_key=_PrivateKey())
            else:
                # ask for an updated Service, ensuring the service responds
                # with a signature that we know was (once) valid
                response = _call_function(self._service_url,
                                          response_key=_PrivateKey(),
                                          public_cert=self._pubcert)

            service = Service.from_data(response["service_info"])

            if service.uid() != self.uid():
                raise ServiceError(
                    "Cannot update the service as the UID has changed. We "
                    "cannot move from %s to %s. Contact an administrator." %
                    (str(self), str(service)))

            # everything should be ok. Update this object with the new
            # keys and data
            self.__dict__ = _deepcopy(service.__dict__)

    def can_identify_users(self):
        """Return whether or not this service can identify users.
           Most services can, at a minimum, identify their admin
           users. However, only true Identity Services can register
           and manage normal users
        """
        return True

    def is_identity_service(self):
        """Return whether or not this is an identity service"""
        if self._service_type:
            return self._service_type == "identity"
        else:
            return False

    def is_access_service(self):
        """Return whether or not this is an access service"""
        if self._service_type:
            return self._service_type == "access"
        else:
            return False

    def is_accounting_service(self):
        """Return whether or not this is an accounting service"""
        if self._service_type:
            return self._service_type == "accounting"
        else:
            return False

    def is_storage_service(self):
        """Return whether or not this is a storage service"""
        if self._service_type:
            return self._service_type == "storage"
        else:
            return False

    def service_url(self):
        """Return the URL used to access this service"""
        return self._service_url

    def canonical_url(self):
        """Return the canonical URL for this service (this is the URL the
           service thinks it has, and which it has used to register itself
           with all other services)
        """
        return self._canonical_url

    def update_service_url(self, service_url):
        """Update the service url to be 'service_url'"""
        self._service_url = str(service_url)

    def skeleton_key(self):
        """Return the skeleton key used by this service. This is an
           unchanging key which is stored internally, should never be
           shared outside the service, and which is used to encrypt
           all data. Unlocking the service involves loading and
           decrypting this skeleton key
        """
        self.assert_unlocked()
        return self._skeleton_key

    def private_key(self):
        """Return the private key (if it has been unlocked)"""
        self.assert_unlocked()
        return self._privkey

    def private_certificate(self):
        """Return the private signing certificate (if it has been unlocked)"""
        self.assert_unlocked()
        return self._privcert

    def public_key(self):
        """Return the public key for this service"""
        return self._pubkey

    def public_certificate(self):
        """Return the public signing certificate for this service"""
        return self._pubcert

    def last_key(self):
        """Return the old private key for this service (if it has
           been unlocked). This was the key used before the last
           key update, and we store it in case we have to decrypt
           data that was recently encrypted using the old public key
        """
        self.assert_unlocked()
        return self._lastkey

    def last_certificate(self):
        """Return the old public certificate for this service. This was the
           certificate used before the last key update, and we store it
           in case we need to verify data signed using the old private
           certificate
        """
        return self._lastcert

    def call_function(self, func, args=None):
        """Call the function 'func' on this service, optionally passing
           in the arguments 'args'. This is a simple wrapper around
           Acquire.Service.call_function which automatically
           gets the correct URL, encrypts the arguments using the
           service's public key, and supplies a key to encrypt
           the response (and automatically then decrypts the
           response)
        """
        return _call_function(self.canonical_url(), function=func,
                              args_key=self.public_key(),
                              public_cert=self.public_certificate(),
                              response_key=_PrivateKey())

    def sign(self, message):
        """Sign the specified message"""
        return self.private_certificate().sign(message)

    def verify(self, signature, message):
        """Verify that this service signed the message"""
        self.public_certificate().verify(signature, message)

    def encrypt(self, message):
        """Encrypt the passed message"""
        return self.public_key().encrypt(message)

    def decrypt(self, message):
        """Decrypt the passed message"""
        return self.private_key().decrypt(message)

    def sign_data(self, data):
        """Sign the passed data, ready for transport. Data should be
           a json-serialisable dictionary. This will return a new
           json-serialisable dictionary, which will contain the
           signature and json-serialised original data, e.g. as;

           data = {"service_uid" : "SERVICE_UID",
                   "fingerprint" : "KEY_FINGERPRINT",
                   "signed_data" : "JSON_ENCODED_DATA",
                   "signature" : "SIG OF JSON_ENCODED_DATA"}
        """
        data = _json.dumps(data)

        return {"service_uid": str(self.uid()),
                "canonical_url": str(self.canonical_url()),
                "fingerprint": str(self.private_certificate().fingerprint()),
                "signed_data": data,
                "signature": _bytes_to_string(self.sign(data))
                }

    def verify_data(self, data):
        """Verify the passed data has been signed by this service. The
           passed data should have the same format as that produced
           by 'sign_data'. If the data is verified then this will
           return a json-deserialised dictionary of the verified data.
           Note that the 'service_uid' should match the UID of this
           service. The data should also contain the fingerprint of the
           key used to encrypt the data, enabling the service to
           perform key rotation and management.
        """
        try:
            service_uid = data["service_uid"]
            fingerprint = data["fingerprint"]
            signature = _string_to_bytes(data["signature"])
            data = data["signed_data"]
        except Exception as e:
            raise ServiceError(
                "The signed data is not of the correct format: %s" % str(e))

        if service_uid != self.uid():
            raise ServiceError(
                "Cannot verify the data as it wasn't signed for this "
                "service - unmatched service UID: %s versus %s" %
                (service_uid, self.uid()))

        if fingerprint != self.public_certificate().fingerprint():
            raise ServiceError(
                "Cannot verify the data as we don't recognise the "
                "fingerprint of the signing key: %s versus %s" %
                (fingerprint, self.public_certificate().fingerprint()))

        self.verify(signature, data)
        return _json.loads(data)

    def encrypt_data(self, data):
        """Encrypt the passed data, ready for transport to the service.
           Data should be a json-serialisable dictionary. This will
           return a new json-serialisable dictionary, which will contain
           the UID of the service this should be sent to (together with
           the canonical URL, which enables this data to be forwarded
           to where it needs to go), and the encrypted
           data, e.g. as;

           data = {"service_uid" : "SERVICE_UID",
                   "canonical_url" : "CANONICAL_URL",
                   "fingerprint" : "KEY_FINGERPRINT",
                   "encrypted_data" : "ENCRYPTED_DATA"}
        """
        return {"service_uid": str(self.uid()),
                "canonical_url": str(self.canonical_url()),
                "fingerprint": str(self.public_key().fingerprint()),
                "encrypted_data": _bytes_to_string(
                                    self.encrypt(_json.dumps(data)))
                }

    def decrypt_data(self, data):
        """Decrypt the passed data that has been encrypted and sent to
           this service (encrypted via the 'encrypt_data' function).
           This will return a json-deserialisable dictionary. Note that
           the 'service_uid' should match the UID of this
           service. The data should also contain the fingerprint of the
           key used to encrypt the data, enabling the service to
           perform key rotation and management.
        """
        try:
            service_uid = data["service_uid"]
            fingerprint = data["fingerprint"]
            data = _string_to_bytes(data["encrypted_data"])
        except Exception as e:
            raise ServiceError(
                "The encrypted data is not of the correct format: %s" % str(e))

        if service_uid != self.uid():
            raise ServiceError(
                "Cannot decrypt the data as it wasn't encrypted for this "
                "service - unmatched service UID: %s versus %s" %
                (service_uid, self.uid()))

        if fingerprint != self.private_key().fingerprint():
            raise ServiceError(
                "Cannot decrypt the data as we don't recognise the "
                "fingerprint of the encryption key: %s versus %s" %
                (fingerprint, self.private_key().fingerprint()))

        data = self.decrypt(data)
        return _json.loads(data)

    def dump_keys(self):
        """Return a dump of the current key and certificate, so that
           we can keep a record of all keys that have been used. The
           returned json-serialisable dictionary contains the keys,
           their fingerprints, and the datetime when they were
           generated. If this is run on the service, then the keys
           are encrypted the password which is encrypted using the
           master key
        """
        dump = {}
        dump["datetime"] = _datetime_to_string(self._last_key_update)

        if self.is_unlocked():
            ranpas = _PrivateKey.random_passphrase()
            dump[self._privkey.fingerprint()] = self._privkey.to_data(ranpas)
            dump[self._privcert.fingerprint()] = self._privcert.to_data(ranpas)
            ranpas = _bytes_to_string(self._skeleton_key.encrypt(ranpas))
            dump["encrypted_passphrase"] = ranpas
        else:
            dump[self._pubkey.fingerprint()] = self._pubkey.to_data()
            dump[self._pubcert.fingerprint()] = self._pubcert.to_data()

        return dump

    def load_keys(self, data):
        """Return the keys that were dumped by 'self.dump_keys()'.
           This returns a dictionary of the keys and datetime that
           they were created, indexed by their key fingerprints
        """
        # get all of the key fingerprints in this dictionary
        fingerprints = []
        for key in data.keys():
            if key not in ["datetime", "encrypted_passphrase"]:
                fingerprints.append(key)

        # now unpack everything
        result = {}
        result["datetime"] = _string_to_datetime(data["datetime"])

        if self.is_unlocked():
            ranpas = self._skeleton_key.decrypt(
                            _string_to_bytes(data["encrypted_passphrase"]))

            for fingerprint in fingerprints:
                result[fingerprint] = _PrivateKey.from_data(data[fingerprint],
                                                            ranpas)
        else:
            for fingerprint in fingerprints:
                result[fingerprint] = _PublicKey.from_data(data[fingerprint])

        return result

    def to_data(self, password=None):
        """Serialise this key to a dictionary, using the supplied
           password to encrypt the private key and certificate"""

        data = {}

        data["uid"] = self._uid
        data["service_type"] = self._service_type
        data["service_url"] = self._service_url

        data["public_certificate"] = self._pubcert.to_data()
        data["public_key"] = self._pubkey.to_data()

        data["last_certificate"] = self._lastcert.to_data()

        data["last_key_update"] = _datetime_to_string(self._last_key_update)
        data["key_update_interval"] = self._key_update_interval

        if (self.is_unlocked()) and (password is not None):
            # only serialise private data if a password was provided
            secret_passphrase = _PrivateKey.random_passphrase()
            key_data = self._privkey.to_data(secret_passphrase)
            lastkey_data = self._lastkey.to_data(secret_passphrase)
            cert_data = self._privcert.to_data(secret_passphrase)

            secret_data = {"passphrase": secret_passphrase,
                           "private_key": key_data,
                           "last_key": lastkey_data,
                           "private_certificate": cert_data}

            secret_data = self._skeleton_key.encrypt(_json.dumps(secret_data))

            data["secret_data"] = _bytes_to_string(secret_data)
            data["skeleton_key"] = self._skeleton_key.to_data(password)

        return data

    @staticmethod
    def from_data(data, password=None):
        """Deserialise this object from the passed data. This will
           only deserialise the private key and private certificate
           if the password is supplied
        """

        service = Service()

        if password:
            # get the private info...
            service._skeleton_key = _PrivateKey.from_data(data["skeleton_key"],
                                                          password)

            secret = service._skeleton_key.decrypt(_string_to_bytes(
                                                   data["secret_data"]))

            secret = _json.loads(secret)

            passphrase = secret["passphrase"]
            service._privkey = _PrivateKey.from_data(secret["private_key"],
                                                     passphrase)
            service._lastkey = _PrivateKey.from_data(secret["last_key"],
                                                     passphrase)
            service._privcert = _PrivateKey.from_data(
                                            secret["private_certificate"],
                                            passphrase)
        else:
            service._skeleton_key = None
            service._privkey = None
            service._privcert = None
            service._lastkey = None

        service._uid = data["uid"]
        service._service_type = data["service_type"]
        service._service_url = data["service_url"]
        service._canonical_url = service._service_url

        service._pubkey = _PublicKey.from_data(data["public_key"])
        service._pubcert = _PublicKey.from_data(data["public_certificate"])
        service._lastcert = _PublicKey.from_data(data["last_certificate"])

        service._last_key_update = _string_to_datetime(data["last_key_update"])
        service._key_update_interval = float(data["key_update_interval"])

        if service.is_identity_service():
            from Acquire.Identity import IdentityService as _IdentityService
            return _IdentityService(service)
        elif service.is_access_service():
            from Acquire.Access import AccessService as _AccessService
            return _AccessService(service)
        elif service.is_storage_service():
            from Acquire.Storage import StorageService as _StorageService
            return _StorageService(service)
        elif service.is_accounting_service():
            from Acquire.Accounting import AccountingService \
                                        as _AccountingService
            return _AccountingService(service)
        else:
            return service
