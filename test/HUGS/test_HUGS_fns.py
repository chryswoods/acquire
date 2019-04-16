# Testing ACRG codes with the Acquire object store
# These two functions proces test data and convert it into
# NetCDF files


# import acrg_obs
import HUGS
import pytest
import numpy as np
import pandas as pd
import xarray as xr
import os
import shutil
import glob

import hashlib

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service

test_dir = os.path.dirname(os.path.abspath(__file__))
obj_store_dir = os.path.normpath("/tmp/object_store_testing/")

# These are currently needed for the acrg_obs code to function correctly

@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    push_is_running_service()
    bucket = get_service_account_bucket(str(d))
    pop_is_running_service()
    return bucket





# def test_writing_netcdfs(bucket):

#     gc_files_directory = os.path.join(test_dir,
#                                       "files/obs/GC")

#     obj_store_path = os.path.join(obj_store_dir, "obj_store")

#     HUGS.process_gcwerks.gc("CGO", "medusa", "AGAGE",
#                                 input_directory=gc_files_directory,
#                                 output_directory=gc_files_directory,
#                                 version="TEST")




# def test_objstore(bucket):
#     keys = []

#     print("Output dir " + test_dir)

#     message = "ƒƒƒ Hello World ∂∂∂"

#     ObjectStore.set_string_object(bucket, "test", message)
#     keys.append("test")

#     assert(message == ObjectStore.get_string_object(bucket, "test"))

#     message = "€€#¢∞ Hello ˚ƒ´πµçµΩ"

#     ObjectStore.set_string_object(bucket, "test/something", message)
#     keys.append("test/something")

#     assert(message == ObjectStore.get_string_object(bucket, "test/something"))

#     data = {"cat": "mieow",
#             "dog": "woof",
#             "sounds": [1, 2, 3, 4, 5],
#             "flag": True}

#     ObjectStore.set_object_from_json(bucket, "test/object", data)
#     keys.append("test/object")

#     assert(data == ObjectStore.get_object_from_json(bucket, "test/object"))

#     names = ObjectStore.get_all_object_names(bucket)

#     assert(len(names) == len(keys))

#     names = ObjectStore.get_all_object_names(bucket, "test")

#     assert(len(names) == 3)

#     names = ObjectStore.get_all_object_names(bucket, "test/")

#     assert(len(names) == 2)

#     names = ObjectStore.get_all_object_names(bucket, "test/some")

#     assert(len(names) == 1)

#     for name in names:
#         assert(name in keys)

#     new_bucket = ObjectStore.create_bucket(bucket, "new_bucket")

#     ObjectStore.set_object_from_json(new_bucket, "test/objecnetcdfst2", data)
#     assert(data == ObjectStore.get_object_from_json(new_bucket,
#                                                     "test/object2"))

#     with pytest.raises(ObjectStoreError):
#         new_bucket = ObjectStore.create_bucket(bucket, "testing_objstore")

#     with pytest.raises(ObjectStoreError):
#         new_bucket = ObjectStore.create_bucket(bucket, "new_bucket")

#     with pytest.raises(ObjectStoreError):
#         new_bucket = ObjectStore.get_bucket(bucket, "get_bucket",
#                                             create_if_needed=False)

#     new_bucket = ObjectStore.get_bucket(bucket, "get_bucket",
#                                         create_if_needed=True)

#     test_key = "test_string"
#     test_value = "test_string_value"

#     ObjectStore.set_string_object(new_bucket, test_key, test_value)

#     new_bucket2 = ObjectStore.get_bucket(bucket, "get_bucket",
#                                          create_if_needed=False)

#     test_value2 = ObjectStore.get_string_object(new_bucket2, test_key)

#     assert(test_value == test_value2)

def get_abs_filepaths(directory):
    full_filepaths = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            full_filepaths.append(os.path.abspath(os.path.join(dirpath, f)))

    return full_filepaths

def get_md5(filename):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    md5 = hashlib.md5()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    
    return md5.hexdigest()


def hash_files(file_list):
    ''' Helper function to hash all the files in
        file_list using MD5
    '''
    # Create a list of tuples for the original files
    hashes = []

    for filepath in file_list:
        md5_hash = get_md5(filepath)
        filename = filepath.split("/")[-1]
        hashes.append((filename, md5_hash))
   
    return hashes


def test_netcdf_to_objstore(bucket):
    # Read from the files we've uploaded,
    # process them and write to object store

    # Create a bucket for the files
    # Get the ACRG code to write all the .nc files
    # Add them to the bucket in the object store

    # print("Output dir " + test_dir)
    test_bucket = ObjectStore.create_bucket(bucket, "test_bucket")

    # Clear out the bucket
    ObjectStore.delete_all_objects(test_bucket)
    
    # message = "ƒƒƒ Hello World ∂∂∂"
    # ObjectStore.set_string_object(test_bucket, "test", message)

    gc_files_directory = os.path.join(test_dir, "files/obs/GC")

    # ACRG process that processes data and creates 56 NetCDF files
    HUGS.process_gcwerks.gc("CGO", "medusa", "AGAGE",
                                input_directory=gc_files_directory,
                                output_directory=gc_files_directory,
                                version="TEST")

    # Location of the NetCDF files created by ACRG code
    output_location = os.path.join(gc_files_directory, "CGO")
    # Test if CGO directory has been created
    assert(os.path.exists(output_location))

    # Get number *.nc files written - this feels a bit clunky
    n_files_written = len([x for x in os.listdir(output_location) if x.endswith("nc")])

    files_to_obj = get_abs_filepaths(output_location)

    # Hashes of originally output files
    original_hashes = hash_files(files_to_obj)

    # Write the files into the object store
    for filename in files_to_obj:
        # Create a key from the filename
        file_key = filename.split("/")[-1].rstrip(".nc")
        # Place files in object store
        ObjectStore.set_object_from_file(test_bucket, file_key, filename)

    # Get the names of all the objects in the test_bucket
    obj_in_bucket = ObjectStore.get_all_object_names(test_bucket)

    # print(obj_in_bucket)

    # Ensure the correct number of files are in the test_bucket
    assert(len(obj_in_bucket) == n_files_written)

    # Test that the files that go into the
    # object store and the files that come out are the same
    temp_dir = "_tmp_test"
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    for key in obj_in_bucket:
        file_to_write = temp_dir + "/" + key + ".nc"
        ObjectStore.take_object_as_file(test_bucket, key, file_to_write)
        # ObjectStore.delete_object(test_bucket, file_key)

    stored_files = get_abs_filepaths(temp_dir)
    # Check that the MD5s match
    obj_store_hashes = hash_files(stored_files)

    assert(obj_store_hashes == original_hashes)

    # Cleanup the NetCDF files created
    shutil.rmtree(temp_dir)







    # Check the bucket has the correct files in it


    # # Check that enough files have been created
    # assert len(glob.glob(os.path.join(gc_files_directory, "CGO/*.nc"))) == 56

    # # As an example, get CF4 data
    # cf4_file = os.path.join(gc_files_directory,
    #                         "CGO/AGAGE-GCMSMedusa_CGO_20180101_cf4-70m-TEST.nc")
    # # Check if file exists
    # assert os.path.exists(cf4_file)

    # # Open dataset
    # with xr.open_dataset(cf4_file) as f:
    #     gc_files_directory
    #     ds = f.load()

    # # Check a particular value (note that time stamp is 10 minutes before analysis time,
    # # because in GCWerks files, times are at the beginning of the sampling period)
    # assert np.allclose(ds.sel(time=slice("2018-01-01 04:33", "2018-01-01 04:35")).cf4.values,
    #                    np.array(83.546))

    # assert np.allclose(ds.sel(time=slice("2018-01-20", "2018-01-20"))["cf4 repeatability"].values[0:1],
    #                    np.array(0.03679))

    # clean up
    # shutil.rmtree(os.path.join(gc_files_directory, "CGO"))

    
# def test_obs_process_crds():

#     gc_files_directory = os.path.join(test_dir,
#                                       "files/obs/CRDS")

#     HUGS.process_gcwerks.crds("BSD", "DECC",
#                                   input_directory=gc_files_directory,
#                                   output_directory=gc_files_directory,
#                                   version="TEST")

#     # Test if CGO directory has been created
#     assert os.path.exists(os.path.join(gc_files_directory, "BSD"))

#     # Check that enough files have been created
#     assert len(glob.glob(os.path.join(gc_files_directory, "BSD/*.nc"))) == 3

#     # As an example, get CF4 data
#     ch4_file = os.path.join(gc_files_directory,
#                             "BSD/DECC-CRDS_BSD_20140130_ch4-248m-TEST.nc")
#     # Check if file exists
#     assert os.path.exists(ch4_file)

#     # Open dataset
#     with xr.open_dataset(ch4_file) as f:
#         ds = f.load()

#     # Check a particular value (note that time stamp is 10 minutes before analysis time,
#     # because in GCWerks files, times are at the beginning of the sampling period)
#     assert np.allclose(ds.sel(time=slice("2014-01-30 14:00:00", "2014-01-30 14:01:00")).ch4.values,
#                        np.array(1953.88))
#     assert np.allclose(ds.sel(time=slice("2014-01-30 14:00:00", "2014-01-30 14:01:00"))["ch4 variability"].values,
#                        np.array(0.398))

#     # clean up
#     # shutil.rmtree(os.path.join(gc_files_directory, "BSD"))
