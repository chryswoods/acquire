
__all__ = ["DriveInfo"]

_drive_root = "storage/drive"

_fileinfo_root = "storage/file"

_par_root = "storage/file_pars"


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

    def __str__(self):
        if self.is_null():
            return "Drive::null"
        else:
            return "Drive(%s)" % self._drive_uid

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

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        par_key = "%s/%s" % (_par_root, par_uid)
        file_bucket = self._get_file_bucket()
        metadata_bucket = self._get_metadata_bucket()

        data = _ObjectStore.get_object_from_json(metadata_bucket, par_key)

        par = _PAR.from_data(data["par"])
        file_key = data["file_key"]
        user_guid = data["user_guid"]
        expected_objsize = data["filesize"]
        expected_checksum = data["checksum"]

        # the same user who requested the PAR must signify that the upload
        # has completed
        if authorisation.user_guid() != user_guid:
            raise PermissionError(
                "Only the user with GUID %s can signify that the "
                "upload is complete. Not user with GUID %s" %
                (user_guid, authorisation.user_guid()))

        # check that the file uploaded matches what was promised
        (objsize, checksum) = _ObjectStore.get_size_and_checksum(file_bucket,
                                                                 file_key)

        if expected_objsize != objsize or expected_checksum != checksum:
            from Acquire.Storage import FileValidationError
            raise FileValidationError(
                "The file uploaded does not match what was promised. "
                "size: %s versus %s, checksum: %s versus %s. Please try "
                "to upload the file again." %
                (expected_objsize, objsize,
                 expected_checksum, checksum))

            # probably should delete the broken object here...

        # SHOULD HERE RECEIPT THE STORAGE TRANSACTION

        _ObjectStore.delete_par(bucket=file_bucket, par=par)
        _ObjectStore.delete_object(bucket=metadata_bucket, key=par_key)

    def upload(self, filehandle, authorisation, encrypt_key=None):
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

        user_guid = authorisation.user_guid()

        drive_acl = self.aclrules().resolve(user_guid=user_guid)

        if not drive_acl.is_writeable():
            raise PermissionError(
                "You do not have permission to write to this drive. "
                "Your permissions are %s" % str(drive_acl))

        # now generate a FileInfo for this FileHandle
        fileinfo = _FileInfo(drive_uid=self._drive_uid,
                             filehandle=filehandle,
                             user_guid=authorisation.user_guid())

        # resolve the ACL for the file from this FileHandle
        file_acl = fileinfo.aclrules().resolve(upstream=drive_acl,
                                               user_guid=user_guid)

        if not file_acl.is_writeable():
            raise PermissionError(
                "Despite having write permission to the drive, you "
                "do not have write permission for the file. Your file "
                "permissions are %s" % str(file_acl))

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

            par_key = "%s/%s" % (_par_root, par.uid())

            data = {"par": par.to_data(),
                    "file_key": file_key,
                    "user_guid": user_guid,
                    "objsize": fileinfo.filesize(),
                    "checksum": fileinfo.checksum()}

            _ObjectStore.set_object_from_json(bucket=metadata_bucket,
                                              key=par_key,
                                              data=data)
        else:
            par = None

        # now save the fileinfo to the object store
        fileinfo.save()

        # return the PAR if we need to have a second-stage of upload
        return (fileinfo.get_filemeta(resolved_acl=file_acl), par)

    def download_complete(self, par_uid, authorisation):
        """Call this function to signify that the file associated with
           the PAR with UID 'par_uid' has been downloaded (must have matching
           authorisation)
        """
        from Acquire.Client import PAR as _PAR
        from Acquire.Client import Authorisation as _Authorisation

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be of type Authorisation")

        authorisation.verify("downloaded %s" % par_uid)

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        par_key = "%s/%s" % (_par_root, par_uid)
        file_bucket = self._get_file_bucket()
        metadata_bucket = self._get_metadata_bucket()

        data = _ObjectStore.get_object_from_json(metadata_bucket, par_key)

        par = _PAR.from_data(data["par"])
        file_key = data["file_key"]
        user_guid = data["user_guid"]

        # the same user who requested the PAR must signify that the upload
        # has completed
        if authorisation.user_guid() != user_guid:
            raise PermissionError(
                "Only the user with GUID %s can signify that the "
                "upload is complete. Not user with GUID %s" %
                (user_guid, authorisation.user_guid()))

        if par.is_writeable():
            expected_objsize = data["filesize"]
            expected_checksum = data["checksum"]

            # check that use of the PAR has not changed the file...
            (objsize, checksum) = _ObjectStore.get_size_and_checksum(
                                            file_bucket, file_key)

            if expected_objsize != objsize or expected_checksum != checksum:
                from Acquire.Storage import FileValidationError
                raise FileValidationError(
                    "The file downloaded does not match what was promised. "
                    "size: %s versus %s, checksum: %s versus %s. This "
                    "suggests that the PAR has been used incorrectly!" %
                    (expected_objsize, objsize,
                     expected_checksum, checksum))

                # probably should delete the broken object here...

        _ObjectStore.delete_par(bucket=file_bucket, par=par)
        _ObjectStore.delete_object(bucket=metadata_bucket, key=par_key)

    def download(self, filename, authorisation,
                 version=None, encrypt_key=None):
        """Download the file called filename. This will return a
           FileHandle that describes the file. If the file is
           sufficiently small, then the filedata will be embedded
           into this handle. Otherwise a PAR will be generated and
           also returned to allow the file to be downloaded
           separately. The PAR will be encrypted with 'encrypt_key'
        """
        from Acquire.Client import FileHandle as _FileHandle
        from Acquire.Storage import FileInfo as _FileInfo
        from Acquire.Identity import Authorisation as _Authorisation
        from Acquire.Crypto import PublicKey as _PublicKey
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be of type Authorisation")

        if not isinstance(encrypt_key, _PublicKey):
            raise TypeError("The encryption key must be of type PublicKey")

        authorisation.verify("download %s %s" % (self._drive_uid,
                                                 filename))

        user_guid = authorisation.user_guid()

        drive_acl = self.aclrules().resolve(user_guid=user_guid)

        # even if the drive_acl is not readable by this user, they
        # may have read permission for the file...

        # now get the FileInfo for this FileHandle
        fileinfo = _FileInfo.load(drive=self,
                                  filename=filename, version=version)

        # resolve the ACL for the file from this FileHandle
        file_acl = fileinfo.aclrules().resolve(upstream=drive_acl,
                                               user_guid=user_guid)

        if not file_acl.is_readable():
            raise PermissionError(
                "You do not have read permissions for the file. Your file "
                "permissions are %s" % str(file_acl))

        file_bucket = self._get_file_bucket()
        metadata_bucket = self._get_metadata_bucket()

        file_key = fileinfo.latest_version()._file_key()
        filedata = None
        par = None

        if fileinfo.filesize() < 1048576:
            # one-trip download of files that are less than 1 MB
            filedata = _ObjectStore.get_object(file_bucket, file_key)
        else:
            # the file is too large to include in the download so
            # we need to use a PAR to download
            par = _ObjectStore.create_par(bucket=file_bucket,
                                          encrypt_key=encrypt_key,
                                          key=file_key,
                                          readable=True,
                                          writeable=False)

            par_key = "%s/%s" % (_par_root, par.uid())

            data = {"par": par.to_data(),
                    "file_key": file_key,
                    "user_guid": user_guid,
                    "objsize": fileinfo.filesize(),
                    "checksum": fileinfo.checksum()}

            _ObjectStore.set_object_from_json(bucket=metadata_bucket,
                                              key=par_key,
                                              data=data)

        # return the filemeta, and either the filedata or par
        return (fileinfo.get_filemeta(resolved_acl=file_acl), filedata, par)

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

    def aclrules(self):
        """Return the acl rules for this drive"""
        try:
            return self._aclrules
        except:
            from Acquire.Storage import ACLRules as _ACLRules
            return _ACLRules()

    def set_permission(self, user_guid, aclrule):
        """Set the permission for the user with the passed user_guid
           to 'aclrule". Note that you can only do this if you are the
           owner and this drive was opened in an authorised way. Also
           note that you cannot remove your own ownership permission
           if this would leave the drive without any owners
        """
        if self.is_null():
            return

        from Acquire.Storage import create_aclrules as _create_aclrules
        aclrules = _create_aclrules(aclrule=aclrule, user_guid=user_guid)

        # make sure we have the latest version
        self.load()

        if not self.is_opened_by_owner():
            raise PermissionError(
                "You cannot change user permissions as you are either "
                "not the owner of this drive or you failed to provide "
                "authorisation when you opened the drive")

        # this will append the new rules, ensuring that the change
        # does not leave the drive ownerless
        self._aclrules.append(aclrules, ensure_owner=True)

        self.save()
        self.load()

    def list_files(self, authorisation=None, include_metadata=False):
        """Return the list of FileMeta data for the files contained
           in this Drive. The passed authorisation is needed in case
           the list contents of this drive is not public
        """
        user_guid = None

        if authorisation is not None:
            from Acquire.Client import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError(
                    "The authorisation must be of type Authorisation")

            authorisation.verify("list_files")

            user_guid = authorisation.user_guid()

        drive_acl = self.aclrules().resolve(user_guid=user_guid)

        if not drive_acl.is_readable():
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

        if include_metadata:
            # we need to load all of the metadata info for this file to
            # return to the user
            from Acquire.Storage import FileInfo as _FileInfo

            for name in names:
                data = _ObjectStore.get_object_from_json(metadata_bucket,
                                                         name)
                fileinfo = _FileInfo.from_data(data)
                filemeta = fileinfo.get_filemeta()
                file_acl = filemeta.resolve_acl(upstream=drive_acl,
                                                user_guid=user_guid)

                if file_acl.is_readable() or file_acl.is_writeable():
                    files.append(filemeta)
        else:
            for name in names:
                filename = _encoded_to_string(name.split("/")[-1])
                files.append(_FileMeta(filename=filename))

        return files

    def list_versions(self, filename, authorisation=None,
                      include_metadata=False, **kwargs):
        """Return the list of versions of the file with specified
           filename. If 'include_metadata' is true then this will
           load full metadata for each version. This will return
           a sorted list of FileMeta objects. The passed authorisation
           is needed in case the version info is not public
        """
        user_guid = None

        if authorisation is not None:
            from Acquire.Client import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError(
                    "The authorisation must be of type Authorisation")

            authorisation.verify("list_versions %s" % filename)

            user_guid = authorisation.user_guid()

        drive_acl = self.aclrules().resolve(user_guid=user_guid, **kwargs)

        if not drive_acl.is_readable():
            raise PermissionError(
                "You don't have permission to read this Drive")

        from Acquire.Storage import FileInfo as _FileInfo
        versions = _FileInfo.list_versions(drive=self,
                                           filename=filename,
                                           include_metadata=include_metadata)

        result = []

        for version in versions:
            if version.aclrules() is not None:
                acl = version.resolve_acl(upstream=drive_acl,
                                          user_guid=user_guid,
                                          **kwargs)

                if acl.is_readable() or acl.is_writeable():
                    result.append(version)
            else:
                result.append(version)

        # return the versions sorted in upload order
        versions.sort(key=lambda x: x.uploaded_when())

        return versions

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
            from Acquire.Storage import create_aclrules as _create_aclrules

            # by default this user is the drive's owner
            self._aclrules = _create_aclrules(user_guid=self._user_guid,
                                              aclrule=_ACLRule.owner())

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

            if self._aclrules is not None:
                data["aclrules"] = self._aclrules.to_data()

        return data

    @staticmethod
    def from_data(data):
        """Return a DriveInfo constructed from the passed json-deserialised
           dictionary
        """
        info = DriveInfo()

        if data is None or len(data) == 0:
            return info

        info._drive_uid = str(data["uid"])

        if "aclrules" in data:
            from Acquire.Storage import ACLRules as _ACLRules
            info._aclrules = _ACLRules.from_data(data["aclrules"])

        return info
