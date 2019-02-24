
__all__ = ["Accounts"]


class Accounts:
    """This class provides the interface to grouping and ungrouping
       accounts, and associating them with users and services. An account
       can belong to multiple groups. Authorisation of access to accounts
       is based on which group they are in. Typically the groups will
       refer to users, e.g. all of the accounts for a user will be in the
       user's group, and can then be authorised by authorising the user
    """
    def __init__(self, group=None):
        """Construct an interface to the group of accounts called 'group'.
           If the group is not specified, then it will default to 'default'
        """
        if group is None:
            group = "default"

        self._group = str(group)

    def __str__(self):
        return "Accounts(group=%s)" % self.group()

    def _root(self):
        """Return the root key for this group in the object store"""
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded
        return "accounting/account_groups/%s" % \
            _string_to_encoded(self._group)

    def _account_key(self, name):
        """Return the key for the account called 'name' in this group"""
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded
        return "%s/%s" % (self._root(),
                          _string_to_encoded(str(name)))

    def group(self):
        """Return the name of the group that this set of accounts refers to"""
        return self._group

    def list_accounts(self, bucket=None):
        """Return the names of all of the accounts in this group"""
        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import encoded_to_string \
            as _encoded_to_string

        keys = _ObjectStore.get_all_object_names(bucket, self._root())
        root_len = len(self._root())

        accounts = []

        for key in keys:
            try:
                account_key = key[root_len:]
                while account_key.startswith("/"):
                    account_key = account_key[1:]

                accounts.append(_encoded_to_string(account_key))
            except Exception as e:
                from Acquire.Accounting import AccountError
                raise AccountError(
                    "Unable to identify the account associated with key "
                    "'%s', equals '%s': %s" %
                    (key, account_key, str(e)))

        return accounts

    def get_account(self, name, bucket=None):
        """Return the account called 'name' from this group"""
        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        try:
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            account_uid = _ObjectStore.get_string_object(
                            bucket, self._account_key(name))
        except:
            account_uid = None

        if account_uid is None:
            # ensure that the user always has a "main" account
            if name == "main":
                return self.create_account("main", "primary user account",
                                           overdraft_limit=0, bucket=bucket)

            from Acquire.Accounting import AccountError
            raise AccountError("There is no account called '%s' in the "
                               "group '%s'" % (name, self.group()))

        from Acquire.Accounting import Account as _Account
        return _Account(uid=account_uid, bucket=bucket)

    def contains(self, account, bucket=None):
        """Return whether or not this group contains the passed account"""
        from Acquire.Accounting import Account as _Account
        if not isinstance(account, _Account):
            raise TypeError("The passed account must be of type Account")

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        # read the UID of the account in this group that matches the
        # passed account's name
        try:
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            account_uid = _ObjectStore.get_string_object(
                            bucket, self._account_key(account.name()))
        except:
            account_uid = None

        return account.uid() == account_uid

    def create_account(self, name, description=None,
                       overdraft_limit=None, bucket=None):
        """Create a new account called 'name' in this group. This will
           return the existing account if it already exists
        """
        if name is None:
            raise ValueError("You must pass a name of the new account")

        account_key = self._account_key(name)

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import Account as _Account

        try:
            account_uid = _ObjectStore.get_string_object(bucket, account_key)
        except:
            account_uid = None

        if account_uid is not None:
            # this account already exists - just return it
            account = _Account(uid=account_uid, bucket=bucket)

            if overdraft_limit is not None:
                account.set_overdraft_limit(overdraft_limit, bucket=bucket)

            return account

        # make sure that no-one has created this account before
        from Acquire.ObjectStore import Mutex as _Mutex
        m = _Mutex(account_key, timeout=600, lease_time=600, bucket=bucket)

        try:
            account_uid = _ObjectStore.get_string_object(bucket, account_key)
        except:
            account_uid = None

        if account_uid is not None:
            m.unlock()
            # this account already exists - just return it
            account = _Account(uid=account_uid, bucket=bucket)

            if overdraft_limit is not None:
                account.set_overdraft_limit(overdraft_limit, bucket=bucket)

            return account

        # write a temporary UID to the object store so that we
        # can ensure we are the only function to create it
        try:
            _ObjectStore.set_string_object(bucket, account_key,
                                           "under_construction")
        except:
            m.unlock()
            raise

        m.unlock()

        # ok - we are the only function creating this account. Let's try
        # to create it properly
        try:
            account = _Account(name=name, description=description,
                               bucket=bucket)
        except:
            try:
                _ObjectStore.delete_object(bucket, account_key)
            except:
                pass

            raise

        if overdraft_limit is not None:
            account.set_overdraft_limit(overdraft_limit, bucket=bucket)

        _ObjectStore.set_string_object(bucket, account_key, account.uid())

        return account
