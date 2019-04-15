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

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service

test_dir = os.path.dirname(os.path.abspath(__file__))

# These are currently needed for the acrg_obs code to function correctly

# @pytest.fixture(scope="session")
# def bucket(tmpdir_factory):
#     d = tmpdir_factory.mktemp("simple_objstore")
#     push_is_running_service()
#     bucket = get_service_account_bucket(str(d))
#     pop_is_running_service()
#     return bucket

def test_obs_process_gc():

    # Read from the files we've uploaded,
    # process them and write to object store

    # Create a bucket for the files
    # Get the ACRG code to write all the .nc files
    # Add them to the bucket in the object store
    

    # def set_object_from_file(bucket, key, filename):
    #     """Set the value of 'key' in 'bucket' to equal the contents
    #        of the file located by 'filename'"""
    #     ObjectStore.set_object(bucket, key,
    #                            open(filename, 'rb').read())

    gc_files_directory = os.path.join(test_dir,
                                      "files/obs/GC")

    HUGS.process_gcwerks.gc("CGO", "medusa", "AGAGE",
                                input_directory=gc_files_directory,
                                output_directory=gc_files_directory,
                                version="TEST")

    # Test if CGO directory has been created
    assert os.path.exists(os.path.join(gc_files_directory, "CGO"))

    # Check that enough files have been created
    assert len(glob.glob(os.path.join(gc_files_directory, "CGO/*.nc"))) == 56

    # As an example, get CF4 data
    cf4_file = os.path.join(gc_files_directory,
                            "CGO/AGAGE-GCMSMedusa_CGO_20180101_cf4-70m-TEST.nc")
    # Check if file exists
    assert os.path.exists(cf4_file)

    # Open dataset
    with xr.open_dataset(cf4_file) as f:
        ds = f.load()

    # Check a particular value (note that time stamp is 10 minutes before analysis time,
    # because in GCWerks files, times are at the beginning of the sampling period)
    assert np.allclose(ds.sel(time=slice("2018-01-01 04:33", "2018-01-01 04:35")).cf4.values,
                       np.array(83.546))

    assert np.allclose(ds.sel(time=slice("2018-01-20", "2018-01-20"))["cf4 repeatability"].values[0:1],
                       np.array(0.03679))

    # clean up
    # shutil.rmtree(os.path.join(gc_files_directory, "CGO"))


def test_obs_process_crds():

    gc_files_directory = os.path.join(test_dir,
                                      "files/obs/CRDS")

    HUGS.process_gcwerks.crds("BSD", "DECC",
                                  input_directory=gc_files_directory,
                                  output_directory=gc_files_directory,
                                  version="TEST")

    # Test if CGO directory has been created
    assert os.path.exists(os.path.join(gc_files_directory, "BSD"))

    # Check that enough files have been created
    assert len(glob.glob(os.path.join(gc_files_directory, "BSD/*.nc"))) == 3

    # As an example, get CF4 data
    ch4_file = os.path.join(gc_files_directory,
                            "BSD/DECC-CRDS_BSD_20140130_ch4-248m-TEST.nc")
    # Check if file exists
    assert os.path.exists(ch4_file)

    # Open dataset
    with xr.open_dataset(ch4_file) as f:
        ds = f.load()

    # Check a particular value (note that time stamp is 10 minutes before analysis time,
    # because in GCWerks files, times are at the beginning of the sampling period)
    assert np.allclose(ds.sel(time=slice("2014-01-30 14:00:00", "2014-01-30 14:01:00")).ch4.values,
                       np.array(1953.88))
    assert np.allclose(ds.sel(time=slice("2014-01-30 14:00:00", "2014-01-30 14:01:00"))["ch4 variability"].values,
                       np.array(0.398))

    # clean up
    # shutil.rmtree(os.path.join(gc_files_directory, "BSD"))
