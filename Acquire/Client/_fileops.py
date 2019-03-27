
__all__ = ["create_new_file", "compress", "uncompress"]


def compress(inputfile=None, outputfile=None,
             inputdata=None, compression_type="bz2"):
    """Compress either the passed filename or filedata using the
       specified compression type. This will compress either to the
       file called 'outputfile', or to a tmpfile. The name of the
       file will be returned. If this is compressing data,
       then it will return the compressed data
    """
    import os as _os

    if compression_type == "bz2":
        import bz2 as _bz2

        if inputfile is not None:
            IFILE = open(inputfile, "rb")

            # compress to a tmpfile and then move to outputfile later...
            import tempfile as _tempfile
            (fd, bz2file) = _tempfile.mkstemp(dir=".")
            _os.close(fd)

            try:
                OFILE = _bz2.BZ2File(bz2file, "wb", compresslevel=9)

                # compress data in MB blocks
                data = IFILE.read(1048576)

                while data:
                    OFILE.write(data)
                    data = IFILE.read(1048576)

                IFILE.close()
                OFILE.close()
            except Exception as e:
                print(e)
                # make sure we delete the temporary bz2file
                _os.unlink(bz2file)
                raise

            if outputfile is None:
                return bz2file

            try:
                # move the bz2file to the correct output name
                _os.rename(bz2file, outputfile)
                return outputfile
            except Exception as e:
                print(e)
                # we can't rename the file - just return the bz2 name
                return bz2file

        elif inputdata is not None:
            # compress the passed data and return
            return _bz2.compress(inputdata)
    else:
        raise ValueError("Unrecognised compression type '%s'" %
                         compression_type)


def uncompress(inputfile=None, outputfile=None,
               inputdata=None, compression_type="bz2"):
    """Uncompress either the passed filename or filedata using the
       specified compression type. This will uncompress either to the
       file called 'outputfile', or to a tmpfile. The name of the
       file will be returned. If this is uncompressing data,
       then it will return the uncompressed data
    """
    import os as _os

    if compression_type == "bz2":
        import bz2 as _bz2

        if inputfile is not None:
            IFILE = _bz2.BZ2File(inputfile, "rb")

            # compress to a tmpfile and then move to outputfile later...
            import tempfile as _tempfile
            (fd, bz2file) = _tempfile.mkstemp(dir=".")
            _os.close(fd)

            try:
                OFILE = open(bz2file, "wb")

                # compress data in MB blocks
                data = IFILE.read(1048576)

                while data:
                    OFILE.write(data)
                    data = IFILE.read(1048576)

                IFILE.close()
                OFILE.close()
            except Exception as e:
                print(e)
                # make sure we delete the temporary bz2file
                _os.unlink(bz2file)
                raise

            if outputfile is None:
                return bz2file

            try:
                # move the bz2file to the correct output name
                _os.rename(bz2file, outputfile)
                return outputfile
            except Exception as e:
                print(e)
                # we can't rename the file - just return the bz2 name
                return bz2file

        elif inputdata is not None:
            # compress the passed data and return
            return _bz2.decompress(inputdata)
    else:
        raise ValueError("Unrecognised compression type '%s'" %
                         compression_type)


def create_new_file(filename, dir=None):
    """Create a new file in directory 'dir' (default current directory)
       called 'filename'. If the file already exists, then create a new
       file with name derived from 'filename'
    """
    import os as _os

    filename = _os.path.split(filename)[1]

    if filename.find(".") != -1:
        parts = filename.split(".")
        base = ".".join(parts[0:-1])
        ext = parts[-1]
        if len(ext) == 0:
            ext = None
    else:
        base = filename
        ext = None

    if dir is not None:
        filebase = _os.path.join(dir, base)
    else:
        filebase = base

    if ext is None:
        filename = filebase
    else:
        filename = "%s.%s" % (filebase, ext)

    while True:
        idx = 1
        while _os.path.exists(filename):
            filename = "%s_%s.%s" % (filebase, idx, ext)
            idx += 1

        try:
            # open in "x" move should prevent race condition
            FILE = open(filename, "x")
            FILE.close()
            return _os.path.realpath(filename)
        except:
            pass
