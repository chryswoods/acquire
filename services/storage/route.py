

def storage_functions(function, args):
    """This function routes calls to all of the storage service's
       extra functions
    """
    if function == "create_par":
        from storage.create_par import run as _create_par
        return _create_par(args)
    elif function == "close_ospar":
        from storage.close_ospar import run as _close_ospar
        return _close_ospar(args)
    elif function == "close_downloader":
        from storage.close_downloader import run as _close_downloader
        return _close_downloader(args)
    elif function == "close_uploader":
        from storage.close_uploader import run as _close_uploader
        return _close_uploader(args)
    elif function == "download":
        from storage.download import run as _download
        return _download(args)
    elif function == "download_chunk":
        from storage.download_chunk import run as _download_chunk
        return _download_chunk(args)
    elif function == "list_files":
        from storage.list_files import run as _list_files
        return _list_files(args)
    elif function == "list_drives":
        from storage.list_drives import run as _list_drives
        return _list_drives(args)
    elif function == "list_versions":
        from storage.list_versions import run as _list_versions
        return _list_versions(args)
    elif function == "open_drive":
        from storage.open_drive import run as _open_drive
        return _open_drive(args)
    elif function == "open_uploader":
        from storage.open_uploader import run as _open_uploader
        return _open_uploader(args)
    elif function == "resolve_par":
        from storage.resolve_par import run as _resolve_par
        return _resolve_par(args)
    elif function == "upload":
        from storage.upload import run as _upload
        return _upload(args)
    elif function == "upload_chunk":
        from storage.upload_chunk import run as _upload_chunk
        return _upload_chunk(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(storage_functions))
