
__all__ = ["DriveInfo"]

_drive_root = "storage/drive"

_fileinfo_root = "storage/file"

_upload_par_root = "storage/upload_par"


class DriveInfo:
    """This class provides a service-side handle to the information
       about a particular cloud drive
    """
    def __init__(self, drive_uid=None, user_guid=None,
                 is_authorised=False, parent_drive_uid=None):
        """Construct a DriveInfo for the drive with UID 'drive_uid',
           and optionally the GUID of the user making the request
           (and whether this was authorised). If this drive
           has a parent then it is a sub-drive and not recorded
           in the list of top-level drives
        """
        self._drive_uid = drive_uid
        self._parent_drive_uid = parent_drive_uid
        self._user_guid = user_guid
        self._is_authorised = is_authorised

        if self._drive_uid is not None:
            self.load()

    def is_null(self):
        return self._drive_uid is None

    def _drive_key(self):
        """Return the key for this drive in the object store"""
        return "%s/%s/info" % (_drive_root, self._drive_uid)

    def uid(self):
        """Return the UID of this drive"""
        return self._drive_uid

    def _get_metadata_bucket(self):
        """Return the bucket that contains all of the metadata about
           the files for this drive
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.Service import get_this_service as _get_this_service

        service = _get_this_service()
        bucket = _get_service_account_bucket()
        bucket_name = "user_metadata"

        try:
            return _ObjectStore.get_bucket(
                            bucket=bucket, bucket_name=bucket_name,
                            compartment=service.storage_compartment(),
                            create_if_needed=True)
        except Exception as e:
            from Acquire.ObjectStore import RequestBucketError
            raise RequestBucketError(
                "Unable to open the bucket '%s': %s" % (bucket_name, str(e)))

    def _get_file_bucket(self):
        """Return the bucket that contains all of the files for this
           drive
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.Service import get_this_service as _get_this_service

        service = _get_this_service()
        bucket = _get_service_account_bucket()
        bucket_name = "user_files"

        try:
            return _ObjectStore.get_bucket(
                            bucket=bucket, bucket_name=bucket_name,
                            compartment=service.storage_compartment(),
                            create_if_needed=True)
        except Exception as e:
            from Acquire.ObjectStore import RequestBucketError
            raise RequestBucketError(
                "Unable to open the bucket '%s': %s" % (bucket_name, str(e)))

    def upload_complete(self, par_uid, authorisation):
        """Call this function to signify that the file associated with
           the PAR with UID 'par_uid' has been uploaded (must have matching
           authorisation)
        """
        from Acquire.Client import PAR as _PAR
        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Client import FileMeta as _FileMeta

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be of type Authorisation")

        authorisation.verify("uploaded %s" % par_uid)

        acl = self.get_acl(authorisation.user_guid())

        if not acl.is_writeable():
            raise PermissionError(
                "You do not have permission to write to this drive")

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        par_key = "%s/%s" % (_upload_par_root, par_uid)
        file_bucket = self._get_file_bucket()
        metadata_bucket = self._get_metadata_bucket()

        data = _ObjectStore.get_object_from_json(metadata_bucket, par_key)

        par = _PAR.from_data(data["par"])
        file_key = data["file_key"]
        filemeta = _FileMeta.from_data(data["filemeta"])

        # check that the file uploaded matches what was promised
        (objsize, checksum) = _ObjectStore.get_size_and_checksum(file_bucket,
                                                                 file_key)

        if filemeta.filesize() != objsize or filemeta.checksum() != checksum:
            from Acquire.Storage import FileValidationError
            raise FileValidationError(
                "The file uploaded for %s does not match what was promised. "
                "size: %s versus %s, checksum: %s versus %s. Please try "
                "to upload the file again." %
                (filemeta.filename(), filemeta.filesize(), objsize,
                 filemeta.checksum(), checksum))

            # probably should delete the broken object here...

        # SHOULD HERE RECEIPT THE STORAGE TRANSACTION

        _ObjectStore.delete_par(bucket=file_bucket, par=par)
        _ObjectStore.delete_object(bucket=metadata_bucket, key=par_key)

        # return the handle to the uploaded file
        return filemeta

    def upload_file(self, filehandle, authorisation, encrypt_key=None):
        """Upload the file associated with the passed filehandle.
           If the filehandle has the data embedded, then this uploads
           the file data directly and returns a FileMeta for the
           result. Otherwise, this returns a PAR which should
           be used to upload the data. The PAR will be encrypted
           using 'encrypt_key'
        """
        from Acquire.Client import FileHandle as _FileHandle
        from Acquire.Storage import FileInfo as _FileInfo
        from Acquire.Identity import Authorisation as _Authorisation
        from Acquire.Crypto import PublicKey as _PublicKey
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded

        if not isinstance(filehandle, _FileHandle):
            raise TypeError("The fileinfo must be of type FileInfo")

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be of type Authorisation")

        if encrypt_key is not None:
            if not isinstance(encrypt_key, _PublicKey):
                raise TypeError("The encryption key must be of type PublicKey")

        authorisation.verify("upload %s" % filehandle.fingerprint())

        acl = self.get_acl(authorisation.user_guid())

        if not acl.is_writeable():
            raise PermissionError(
                "You do not have permission to write to this drive")

        # now generate a FileInfo for this FileHandle
        fileinfo = _FileInfo(drive_uid=self._drive_uid,
                             filehandle=filehandle,
                             user_guid=authorisation.user_guid())

        file_bucket = self._get_file_bucket()
        metadata_bucket = self._get_metadata_bucket()

        file_key = fileinfo.latest_version()._file_key()

        filedata = None

        if filehandle.is_localdata():
            # the filehandle already contains the file, so save it
            # directly
            filedata = filehandle.local_filedata()

        _ObjectStore.set_object(bucket=file_bucket,
                                key=file_key,
                                data=filedata)

        if filedata is None:
            # the file is too large to include in the filehandle so
            # we need to use a PAR to upload
            par = _ObjectStore.create_par(bucket=file_bucket,
                                          encrypt_key=encrypt_key,
                                          key=file_key,
                                          readable=False,
                                          writeable=True)

            par_key = "%s/%s" % (_upload_par_root, par.uid())

            data = {"par": par.to_data(),
                    "file_key": file_key,
                    "filemeta": fileinfo.get_filemeta().to_data()}

            _ObjectStore.set_object_from_json(bucket=metadata_bucket,
                                              key=par_key,
                                              data=data)
        else:
            par = None

        # now save the fileinfo to the object store
        fileinfo.save()

        if par:
            return par
        else:
            return fileinfo.get_filemeta()

    def is_opened_by_owner(self):
        """Return whether or not this drive was opened and authorised
           by one of the drive owners
        """
        if self._user_guid is None or (not self._is_authorised):
            return False

        try:
            return self._acls[self._user_guid].is_owner()
        except:
            return False

    def num_owners(self):
        """Return the number of users who have ownership permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_owner()

        return n

    def num_readers(self):
        """Return the number of users who have read permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_readable()

        return n

    def num_writers(self):
        """Return the number of users who have write permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_writeable()

        return n

    def get_acl(self, user_guid):
        """Return the ACL on this drive for the user with passed
           GUID - this returns ACLRule.null() if the user does
           not have permission to read this drive
        """
        try:
            return self._acls[user_guid]
        except:
            from Acquire.Storage import ACLRule as _ACLRule
            return _ACLRule.null()

    def set_permission(self, user_guid, aclrule):
        """Set the permission for the user with the passed user_guid
           to 'aclrule". Note that you can only do this if you are the
           owner and this drive was opened in an authorised way. Also
           note that you cannot remove your own ownership permission
           if this would leave the drive without any owners
        """
        if self.is_null():
            return

        from Acquire.Storage import ACLRule as _ACLRule
        if not isinstance(aclrule, _ACLRule):
            raise TypeError("The aclrule must be type ACLRule")

        # make sure we have the latest version
        self.load()

        if not self.is_opened_by_owner():
            raise PermissionError(
                "You cannot change user permissions as you are either "
                "not the owner of this drive or you failed to provide "
                "authorisation when you opened the drive")

        try:
            old_acl = self._acls[user_guid]
        except:
            old_acl = _ACLRule()

        if self.num_owners() == 1 and old_acl.is_owner():
            raise PermissionError(
                "You cannot remove ownership permissions from the only "
                "owner of the drive")

        if aclrule.is_null():
            del self._acls[user_guid]
        else:
            self._acls[user_guid] = aclrule

        self.save()
        self.load()

        if self.num_owners() == 0:
            # race-condition of two people removing their ownership
            # at the same time - restore old permissions and raise an
            # error
            self._acls[user_guid] = old_acl
            self.save()
            self.load()
            raise PermissionError(
                "You cannot stop yourself being an owner as this would "
                "leave the drive with no owners!")

    def list_files(self, authorisation=None):
        """Return the list of FileMeta data for the files contained
           in this Drive. The passed authorisation is needed in case
           the list contents of this drive is not publi
        """
        user_guid = None

        if authorisation is not None:
            from Acquire.Client import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError(
                    "The authorisation must be of type Authorisation")

            authorisation.verify("list_files")

            user_guid = authorisation.user_guid()

        acl = self.get_acl(user_guid)

        if not acl.is_readable():
            raise PermissionError(
                "You don't have permission to read this Drive")

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import encoded_to_string as _encoded_to_string
        from Acquire.Storage import FileMeta as _FileMeta

        metadata_bucket = self._get_metadata_bucket()

        names = _ObjectStore.get_all_object_names(
                    metadata_bucket, "%s/%s" % (_fileinfo_root,
                                                self._drive_uid))

        files = []
        for name in names:
            filename = _encoded_to_string(name.split("/")[-1])
            files.append(_FileMeta(filename=filename))

        return files

    def load(self):
        """Load the metadata about this drive from the object store"""
        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        bucket = _get_service_account_bucket()

        drive_key = self._drive_key()

        try:
            data = _ObjectStore.get_object_from_json(bucket, drive_key)
        except:
            data = None

        if data is None:
            if self._user_guid is None:
                # we cannot create the drive as we don't know who
                # requested it
                raise PermissionError(
                    "Cannot create the DriveInfo for a new drive as the "
                    "original request did not specify the creating user")
            elif not self._is_authorised:
                # we cannot create the drive if the request was not
                # authorised
                raise PermissionError(
                    "Cannot create the DriveInfo for a new drive as the "
                    "original request was not authorised by the user")

            # create a new drive and save it...
            from Acquire.Storage import ACLRule as _ACLRule

            self._acls = {self._user_guid: _ACLRule.owner()}
            data = self.to_data()

            data = _ObjectStore.set_ins_object_from_json(bucket, drive_key,
                                                         data)

        from copy import copy as _copy
        other = DriveInfo.from_data(data)

        user_guid = self._user_guid
        is_authorised = self._is_authorised

        self.__dict__ = _copy(other.__dict__)

        self._user_guid = user_guid
        self._is_authorised = is_authorised

    def save(self):
        """Save the metadata about this drive to the object store"""
        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        bucket = _get_service_account_bucket()

        drive_key = self._drive_key()

        data = self.to_data()
        _ObjectStore.set_object_from_json(bucket, drive_key, data)

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import dict_to_string as _dict_to_string
            data["uid"] = self._drive_uid
            data["acls"] = _dict_to_string(self._acls)

        return data

    @staticmethod
    def from_data(data):
        """Return a DriveInfo constructed from the passed json-deserialised
           dictionary
        """
        info = DriveInfo()

        if data is None or len(data) == 0:
            return info

        from Acquire.Storage import ACLRule as _ACLRule
        from Acquire.ObjectStore import string_to_dict as _string_to_dict

        info._acls = _string_to_dict(data["acls"], _ACLRule)
        info._drive_uid = str(data["uid"])

        return info