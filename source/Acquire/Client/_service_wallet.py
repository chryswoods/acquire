
import os as _os
import sys as _sys
import getpass as _getpass
import glob as _glob
import re as _re
import base64 as _base64

import lazy_import as _lazy_import

from Acquire.Service import call_function as _call_function
from Acquire.Service import pack_arguments as _pack_arguments
from Acquire.Service import unpack_arguments as _unpack_arguments
from Acquire.Service import Service as _Service

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import OTP as _OTP
from Acquire.Crypto import get_private_key as _get_private_key

from ._errors import LoginError

_pyotp = _lazy_import.lazy_module("pyotp")

__all__ = ["ServiceWallet"]


class ServiceWallet:
    """This class holds a wallet that can be used to simplify
       sending passwords and one-time-password (OTP) codes
       to administer one of the Acquire services

       This holds a wallet of passwords and (optionally)
       OTP secrets that are encrypted using a local keypair
       that is unlocked by a password supplied by the user locally.
    """
    def __init__(self):
        self._wallet_key = None
        self._get_wallet_key()
        self._cache = {}
        self._service_info = {}
        self._manual_password = False
        self._manual_otpcode = False

    @staticmethod
    def _wallet_dir():
        """Directory containing all of the wallet files"""
        homedir = _os.path.expanduser("~")

        walletdir = "%s/.acquire_services" % homedir

        if not _os.path.exists(walletdir):
            _os.mkdir(walletdir)

        return walletdir

    def _create_wallet_key(self, filename):
        """Create a new wallet key for the user"""

        password = _getpass.getpass(
                     prompt="Please enter a password to encrypt your wallet: ")

        key = _PrivateKey()

        bytes = key.bytes(password)

        password2 = _getpass.getpass(prompt="Please confirm the password: ")

        if password != password2:
            print("The passwords don't match. Please try again.")
            self._create_wallet_key(filename)
            return

        # the passwords match - write this to the file
        with open(filename, "wb") as FILE:
            FILE.write(bytes)

        return key

    def _get_wallet_key(self):
        """Return the private key used to encrypt everything in the wallet.
           This will ask for the users password
        """
        if self._wallet_key:
            return self._wallet_key

        wallet_dir = ServiceWallet._wallet_dir()

        keyfile = "%s/wallet_key.pem" % wallet_dir

        if not _os.path.exists(keyfile):
            self._wallet_key = self._create_wallet_key(keyfile)
            return self._wallet_key

        # read the keyfile and decrypt
        with open(keyfile, "rb") as FILE:
            bytes = FILE.read()

        # get the user password
        wallet_key = None
        while not wallet_key:
            password = _getpass.getpass(
                            prompt="Please enter your wallet password: ")

            try:
                wallet_key = _PrivateKey.read_bytes(bytes, password)
            except:
                print("Invalid password. Please try again.")

        self._wallet_key = wallet_key
        return wallet_key

    @staticmethod
    def _get_service_file(service_url):
        """Return the servicefile for the passed service"""
        return "%s/service_%s_encrypted" % (
                ServiceWallet._wallet_dir(),
                _base64.b64encode(service_url.encode("utf-8")).decode("utf-8"))

    @staticmethod
    def remove_service_info(service_url):
        """Call this function to remove the service_info associated
           with the service at 'service_url'
        """
        service_file = ServiceWallet._get_service_file(service_url)

        if _os.path.exists(service_file):
            _os.unlink(service_file)

    def _read_service_file(self, filename):
        """Read all info from the passed service_file"""
        try:
            return self._cache[filename]
        except:
            pass

        if not _os.path.exists(filename):
            return

        with open(filename, "rb") as FILE:
            data = _unpack_arguments(FILE.read())

            try:
                data["password"] = _string_to_bytes(data["password"])
            except:
                pass

            try:
                data["otpsecret"] = _string_to_bytes(data["otpsecret"])
            except:
                pass

            self._cache[filename] = data
            return data

    def _read_service_info(self, service_url):
        """Read all info for the passed service_url"""
        return self._read_service_file(
                    ServiceWallet._get_service_file(service_url))

    def _get_service_url(self):
        """Function to find a service_url automatically, of if that fails,
           to ask the user
        """
        wallet_dir = ServiceWallet._wallet_dir()

        service_files = _glob.glob("%s/service_*_encrypted" % wallet_dir)

        service_infos = {}

        for service_file in service_files:
            try:
                service_info = self._read_service_file(service_file)
                service_infos[service_info["service_url"]] = service_info
            except:
                pass

        service_urls = list(service_infos.keys())
        service_urls.sort()

        if len(service_urls) == 1:
            return service_urls[0]

        if len(service_urls) == 0:
            print("Please type the service_url: ", end="")
            _sys.stdout.flush()
            return _sys.stdin.readline()[0:-1]

        print("Please choose the service by typing in its number, "
              "or type a new service_url if you want a different service.")

        for (i, service_url) in enumerate(service_urls):
            print("[%d] %s" % (i+1, service_url))

        service_url = None

        while not service_url:
            print("Make your selection: ", end="")
            _sys.stdout.flush()

            input = _sys.stdin.readline()[0:-1]

            try:
                input = int(input) - 1
                if input < 0 or input >= len(service_urls):
                    print("Invalid service. Try again...")
                else:
                    service_url = service_urls[input]
            except:
                service_url = input

        return service_url

    def _get_admin_password(self, service_url):
        """Get the admin password of the passed service.
           If remember_device then save the
           password in the wallet if it is not already there
        """
        try:
            service_info = self._read_service_info(service_url)

            if service_info:
                password = service_info["password"]
                self._manual_password = False

                # this needs to be decrypted
                return self._wallet_key.decrypt(password).decode("utf-8")
        except:
            pass

        self._manual_password = True
        return _getpass.getpass(prompt="Please enter the admin password: ")

    def _get_otpcode(self, service_url):
        """Get the OTP code for the admin account of the service"""
        try:
            service_info = self._read_service_info(service_url)

            if service_info:
                secret = self._wallet_key.decrypt(
                                service_info["otpsecret"]).decode("utf-8")
                self._manual_otpcode = False
                return _pyotp.totp.TOTP(secret).now()
        except:
            pass

        self._manual_otpcode = True
        return _getpass.getpass(
                    prompt="Please enter the one-time-password code: ")

    @staticmethod
    def remove_service(service):
        """Remove the cached service data for the passed service"""
        service_file = "%s/service_%s" % (
                ServiceWallet._wallet_dir(),
                _base64.b64encode(service.encode("utf-8")).decode("utf-8"))

        if _os.path.exists(service_file):
            _os.unlink(service_file)

    def _get_service(self, service_url):
        """Return the service data for the passed service"""
        try:
            return self._service_info[service_url]
        except:
            pass

        # can we read this from a file?
        service_file = "%s/certs_%s" % (
            ServiceWallet._wallet_dir(),
            _base64.b64encode(service_url.encode("utf-8")).decode("utf-8"))

        try:
            with open(service_file, "rb") as FILE:
                service_info = _Service.from_data(
                                    _unpack_arguments(FILE.read()))
                self._service_info[service_url] = service_info
                return service_info
        except:
            pass

        try:
            key = _get_private_key("function")
            response = _call_function(service_url, response_key=key)
            service = _Service.from_data(response["service_info"])
        except Exception as e:
            service = None

            if str(e).find(
                    "You haven't yet created the service account for "
                    "this service. Please create an account first") != -1:
                return None

            raise LoginError(
                "Error connecting to the service %s: Error = %s" %
                (service, str(e)))

        if service is None:
            raise LoginError("Error connecting to the service %s. "
                             "Has it been setup?" % service_url)

        self._service_info[service_url] = service

        # save this for future reference
        with open(service_file, "wb") as FILE:
            FILE.write(_pack_arguments(service.to_data()))

        return service

    def _get_service_key(self, service_url):
        """Return the public encryption key for the passed service"""
        service = self._get_service(service_url)

        if service:
            return service.public_key()
        else:
            return None

    def _get_service_cert(self, service_url):
        """Return the public signing certificate for the passed service"""
        service = self._get_service(service_url)

        if service:
            return service.public_certificate()
        else:
            return None

    def call_admin_function(self, function, args={}, service_url=None,
                            remember_password=True, remember_device=None):
        """Call the admin function 'function' using supplied arguments 'args',
           on the service at 'service_url'
        """

        self._manual_password = False
        self._manual_otpcode = False

        if not remember_password:
            remember_device = False

        if not service_url:
            # choose a service_url from any existing files...
            service_url = self._get_service_url()

        # get the public key of this identity service
        service_key = self._get_service_key(service_url)
        service_cert = self._get_service_cert(service_url)

        password = self._get_admin_password(service_url)
        otpcode = self._get_otpcode(service_url)

        strargs = str(args)

        args["password"] = password
        args["otpcode"] = otpcode
        args["remember_device"] = remember_device

        print("\nCalling '%s' with %s... " % (function, strargs), end="")
        _sys.stdout.flush()

        try:
            key = _get_private_key("function")
            response = _call_function(service_url, function,
                                      args_key=service_key, response_key=key,
                                      public_cert=service_cert,
                                      args=args)
            print("SUCCEEDED!")
            _sys.stdout.flush()
        except Exception as e:
            print("FAILED!")
            _sys.stdout.flush()
            raise LoginError("Failed to log in: %s" % str(e))

        if remember_password:
            try:
                provisioning_uri = response["provisioning_uri"]
            except:
                provisioning_uri = None

            otpsecret = None

            if provisioning_uri:
                try:
                    otpsecret = _re.search(r"secret=([\w\d+]+)&issuer",
                                           provisioning_uri).groups()[0]
                except:
                    pass

            try:
                service_info = self._read_service_info(service_url)
            except:
                service_info = {}

            if service_info is None:
                service_info = {}

            pubkey = self._wallet_key.public_key()

            must_write = self._manual_password

            if otpsecret:
                if self._manual_otpcode:
                    must_write = True

            if must_write:
                service_info["service_url"] = service_url.encode(
                                                "utf-8").decode("utf-8")
                service_info["password"] = _bytes_to_string(
                                              pubkey.encrypt(
                                                  password.encode("utf-8")))

                if otpsecret:
                    service_info["otpsecret"] = _bytes_to_string(
                                                pubkey.encrypt(
                                                   otpsecret.encode("utf-8")))

                packed_data = _pack_arguments(service_info)

                with open(ServiceWallet._get_service_file(
                                            service_url), "wb") as FILE:
                    FILE.write(packed_data)

        self._manual_password = False
        self._manual_otpcode = False

        return response
