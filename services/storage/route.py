

def storage_functions(function, args):
    """This function routes calls to all of the storage service's
       extra functions
    """
    if function == "download":
        from storage.download import run as _download
        return _download(args)
    elif function == "downloaded":
        from storage.downloaded import run as _downloaded
        return _downloaded(args)
    elif function == "list_files":
        from storage.list_files import run as _list_files
        return _list_files(args)
    elif function == "list_drives":
        from storage.list_drives import run as _list_drives
        return _list_drives(args)
    elif function == "list_versions":
        from storage.list_versions import run as _list_versions
        return _list_versions(args)
    elif function == "open":
        from storage.open import run as _open
        return _open(args)
    elif function == "open_drive":
        from storage.open_drive import run as _open_drive
        return _open_drive(args)
    elif function == "upload":
        from storage.upload import run as _upload
        return _upload(args)
    elif function == "uploaded":
        from storage.uploaded import run as _uploaded
        return _uploaded(args)
    else:
        return None

if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(storage_functions))
