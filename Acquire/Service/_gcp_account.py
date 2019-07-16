
import os as _os
import uuid as _uuid

__all__ = ["GCPAccount"]


class GCPAccount:
    """This class abstracts all interaction with GCP login accounts. This
       is a low-level account that allows us to connect to the object
       store at a low-level and to call GCP functions
    """

    @staticmethod
    def _assert_valid_login_dict(login):
        """This function validates that the passed login dictionary
           contains all of the keys needed to login"""

        if login is None:
            from Acquire.Service import AccountError
            raise AccountError("You need to supply login credentials!")

        if not isinstance(login, dict):
            from Acquire.Service import AccountError
            raise AccountError(
                "You need to supply a valid login credential dictionary!")

        needed_keys = ["credentials", "project"]

        missing_keys = []

        for key in needed_keys:
            if key not in login:
                missing_keys.append(key)

        if len(missing_keys) > 0:
            from Acquire.Service import AccountError
            raise AccountError(
                "Cannot log in as the login dictionary "
                "is missing the following data: %s" % str(missing_keys))

    @staticmethod
    def get_login(login):
        """This function turns the passed login details into
           a valid oci login
        """

        # validate that all of the information is held in the
        # 'login' dictionary
        GCPAccount._assert_valid_login_dict(login)
        return login

    @staticmethod
    def _sanitise_bucket_name(bucket_name):
        """This function sanitises the passed bucket name. It will always
           return a valid bucket name. If "None" is passed, then a new,
           unique bucket name will be generated"""

        if bucket_name is None:
            return str(_uuid.uuid4())

        return "_".join(bucket_name.split())

    @staticmethod
    def create_and_connect_to_bucket(login_details, bucket_name=None):
        """Connect to the object store using the passed 'login_details', and
           create a bucket called 'bucket_name". Return a handle to the
           created bucket. If the bucket already exists this will return
           a handle to the existing bucket
        """
        return GCPAccount.connect_to_bucket(login_details, bucket_name)

    @staticmethod
    def connect_to_bucket(login_details, bucket_name):
        """Connect to the object store compartment 'compartment'
           using the passed 'login_details', returning a handle to the
           bucket associated with 'bucket
        '"""
        try:
            from google.oauth2 import service_account as _service_account
            from google.cloud import storage as _storage
        except:
            raise ImportError(
                "Cannot import GCP. Please install GCP, e.g. via "
                "'pip install google-cloud-storage' so that you can "
                "connect to the Google Cloud Platform")

        login = GCPAccount.get_login(login_details)
        bucket = {}
        client = None

        creds = _service_account.Credentials.from_service_account_info(
                                                    login["credentials"])

        client = _storage.Client(credentials=creds,
                                 project=login["project"])

        try:
            b = client.get_bucket(bucket_name)
        except Exception as e:
            from Acquire.Service import ServiceAccountError
            raise ServiceAccountError(
                "Cannot connect to GCP - invalid credentials for bucket %s" %
                bucket_name, e)

        bucket["client"] = client
        bucket["credentials"] = creds
        bucket["bucket"] = b
        bucket["bucket_name"] = bucket_name
        bucket["unique_suffix"] = login["unique_suffix"]

        return bucket
