

def storage_functions(function, args):
    """This function routes calls to all of the storage service's
       extra functions
    """
    if function == "list_files":
        from storage.list_files import run as _list_files
        return _list_files(args)
    elif function == "list_drives":
        from storage.list_drives import run as _list_drives
        return _list_drives(args)
    elif function == "open":
        from storage.open import run as _open
        return _open(args)
    elif function == "open_drive":
        from storage.open_drive import run as _open_drive
        return _open_drive(args)
    elif function == "upload_file":
        from storage.upload_file import run as _upload_file
        return _upload_file(args)
    elif function == "uploaded_file":
        from storage.uploaded_file import run as _uploaded_file
        return _uploaded_file(args)
    else:
        return None

if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(storage_functions))
