# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 15:17:02 2015

Code to get MOZART volume mixing ratios at the edges of a domain,
for including boundary conditions in inversions.

Call MOZART_BC_nc which does the following:

Uses "MOZART_vmr" to find an xray dataset of MOZART vmr with the altitude
of each gridcell.

Uses "MOZART_boundaries" to find an xray dataset with the vmrs on the 4
edges of the specified domain. This is interpolated in height and lat/lon to
agree with NAME output.

@author: ew14860
"""
from __future__ import print_function
from __future__ import division

from builtins import str
from builtins import range
from past.utils import old_div
import xarray as xray
import numpy as np
import bisect
from scipy import interpolate
import acrg_MOZART as mz
import os
import pandas as pd
import glob
import datetime as dt
import getpass
import collections as c
import pdb
from os.path import join

acrg_path = os.getenv("ACRG_PATH")
data_path = os.getenv("DATA_PATH")

if acrg_path is None:
    acrg_path = os.getenv("HOME")
    print("Default ACRG directory is assumed to be home directory. Set path in .bashrc as \
            export ACRG_PATH=/path/to/acrg/repository/ and restart python terminal")
if data_path is None:
    data_path = "/data/shared/"
    print("Default Data directory is assumed to be /data/shared/. Set path in .bashrc as \
            export DATA_PATH=/path/to/data/directory/ and restart python terminal")

mzt_dir = join(data_path, 'MOZART/model/mzt_output/')
#filename = mzt_dir + 'CH4/FWDModelComparison_NewEDGAR.mz4.h2.2014-01.nc'


def MOZART_filenames(species, start = "2010-01-01", end = "2016-01-01", runname ='NewEDGAR'):
    """
    Gets a list of files given a species, start date and end date.
    """
    
    baseDirectory = mzt_dir
    
    months = pd.DatetimeIndex(start = start, end = end, freq = "M").to_pydatetime()
    yearmonth = [str(d.year) + '-' + str(d.month).zfill(2) for d in months]

    files = []
    for ym in yearmonth:
        f=glob.glob(baseDirectory + \
            species.upper() + "/" + "*" +runname+'*'+ ym + "*.nc")
        if len(f) > 0:
            files += f

    files.sort()

    if len(files) == 0:
        print("Can't find file: " + baseDirectory + \
            species.upper() + "/" + "*" + ym + "*.nc")
    
    return  files


def convert_lon(DS, data_var):
    """
    Converts variables with a longitude dimension to the -180-180 convention
    rather than the 0-360 convention.
    WARNING: variable must have dimensions ('height','lat','lon','time') in that order.
    """
    DS.coords['lon'] = DS.coords['lon'] - 180
    L = old_div(len(DS.coords['lon']),2)
    var0 = DS[data_var]
    var = np.zeros(np.shape(var0))
    if 'height' in DS[data_var].dims:
        var[:,:,:L,:] = var0[:,:,L:,:]
        var[:,:,L:,:] = var0[:,:,:L,:]  
        DS.update({data_var: (['height', 'lat', 'lon','time'], var)})
    elif 'height' not in DS[data_var].dims:
        var[:,:L,:] = var0[:,L:,:]
        var[:,L:,:] = var0[:,:L,:] 
        DS.update({data_var: (['lat', 'lon','time'], var)})


def interp_heights(DS,vmr_var_name, interp_height):
    """
    Created to convert MOZART heights to NAME heights at boundaries.
    Interpolates the heights of the VMR variable 'vmr_var_name' in the xray dataset
    'DS' to the heights specified in 'interp_heights'. The variable must have dimensions
    (height, lat_or_lon, time) in that order. The dataset DS must also contain a variable
    of altitudes for each value of the VMR variable.
    Returns a new dataset with the VMRs recalculated at interpolated heights, a 'height'
    dimension replaced with the interpolated values and the 'Alt' variable removed.
    """
    vmr = np.zeros((len(interp_height),len(DS[vmr_var_name][0,:,0]),len(DS.coords['time'])))
    for j in range(len(DS['Alt'][0,0,:])):
        for i in range(len(DS['Alt'][0,:,0])):
            x = DS['Alt'][:,i,j]
            y = DS[vmr_var_name][:,i,j]
            f = interpolate.interp1d(x,y, bounds_error = False, fill_value = np.max(y))
            vmr[:,i,j] = f(interp_height)
    DS2 = DS.drop(['Alt'])
    DS2.update({vmr_var_name : (DS[vmr_var_name].dims, vmr),
               'height' : (interp_height)})
    return DS2
    
    
def interp_lonlat(DS,vmr_var_name, lat_or_lon):
    """
    Created to convert MOZART lons/lats to NAME lons/lats at boundaries.
    Make sure that the heights have already been interpolated using 'interp_heights'.
    Interpolates the heights of the VMR variable 'vmr_var_name' in the xray dataset
    'DS' to the longitude or latitude specified in 'lon_or_lat'. The variable must
    have dimensions (height, lat_or_lon, time) in that order.    
    """
    
    vmr = np.zeros((len(DS.coords['height']),len(lat_or_lon),len(DS.coords['time'])))
    for j in range(len(DS[vmr_var_name][0,0,:])):
        for i in range(len(DS[vmr_var_name][:,0,0])):
            y = DS[vmr_var_name][i,:,j]    
            if 'lon' in DS[vmr_var_name].dims:
                x = DS['lon']
            elif 'lat' in DS[vmr_var_name].dims:
                x = DS['lat']
            f = interpolate.interp1d(x,y)
            vmr[i,:,j] = f(lat_or_lon)
        
    if 'lon' in DS[vmr_var_name].dims:
        DS.update({vmr_var_name : (DS[vmr_var_name].dims, vmr),
               'lon' : (lat_or_lon)})
    elif 'lat' in DS[vmr_var_name].dims:
        DS.update({vmr_var_name : (DS[vmr_var_name].dims, vmr),
               'lat' : (lat_or_lon)})
    return DS


def MOZART_vmr(species, filename=None, start = "2010-01-01", end = "2016-01-01", freq='M', runname='NewEDGAR'):
    """
    Returns an xray dataset with (height,lat,lon,time) coordinates and 2 data variables:
    concentration of species (SPECIES_vmr_mozart) and an array of altitudes calculated
    from the pressure levels given in the original MOZART file (Alt). The lons are converted
    from the 0 - 360 convention used in MOZART to the -180 to 180 convention used in NAME.
    """
    species = species.upper()
    if filename is not None:
        if not '/' in filename:
            files = [os.path.join(mzt_dir+'/'+species, filename)]
        else:
            files=[filename]
    else:
        files = MOZART_filenames(species, start, end, runname)
            
    if len(files) == 0:
        print("Can't find files, exiting")
        return None
    else:
        files.sort()
        mzt = []
        
        
        for fi in files:
            f = mz.read(fi)
            Alt = mz.calc_altitude(f.pressure,f.P0)
            conc = np.reshape(f.conc, (len(f.lev),len(f.lat),len(f.lon),len([f.start_date])))
            Alt = np.reshape(Alt,np.shape(conc))
            vmr_var_name = 'vmr'
            
            # change timestamp to occur in the beginning of the month.
#            if freq is 'M':
#                timestamp = f.start_date + dt.timedelta(days=14)
#            else:
#                timestamp = f.start_date
            timestamp = f.start_date

            MZ = xray.Dataset({vmr_var_name : (['height', 'lat', 'lon','time'], conc),
                   'Alt' : (['height', 'lat', 'lon','time'], Alt)},
                            coords = {'height' : f.lev,
                                        'lat' : f.lat,
                                        'lon' : f.lon,
                                        'time': [timestamp]})
            #Change longitude from being 0 - 360 to being -180 - 180.
            convert_lon(MZ,vmr_var_name)
            mzt.append(MZ)
        mzt = xray.concat(mzt, dim = 'time')
        attributes = {"title":"MOZART volume mixing ratios",
                      "author" : getpass.getuser(),
                        "date_created" : np.str(dt.datetime.today()),
                        "species" : "%s" %species.upper(),
                        "run name": "%s" %runname}
        mzt.attrs = c.OrderedDict(attributes)
        return mzt


#def MOZART_boundaries(MZ, FPfile = FPfilename):
def MOZART_boundaries(MZ, domain):
    """
    Gets an xray dataset with 4 variables, each of one side of the domain boundary
    (n,e,s,w) and with height and lat/lon interpolated to the NAME grid.
    MZ is a mozart xray dataset created using MOZART_vmr.
    """

#    listoffiles = glob.glob("/shared_data/air/shared/NAME/fp/" + domain + "/*")
    listoffiles = glob.glob(join(data_path, "NAME/fp/" + domain + "/*"))
    
    with xray.open_dataset(listoffiles[0]) as temp:
        fields_ds = temp.load()
    
    fp_lat = fields_ds["lat"].values
    fp_lon = fields_ds["lon"].values
    fp_height = fields_ds["height"].values
    vmr_var_name = 'vmr'
    
    if any(n<0 for n in fp_lon):
        pass
    else:
#       convert MOZART lons to be on 0 to 360 for consistency with footprints
        new_coords = MZ.coords["lon"].values
        new_coords[new_coords < 0] = new_coords[new_coords < 0] + 360
        MZ = MZ.assign_coords(lon=new_coords)
        MZ = MZ.sortby("lon")

    #Select the gidcells closest to the edges of the  domain and make sure outside of fp
    lat_n = (np.abs(MZ.coords['lat'].values - max(fp_lat))).argmin()+1
    lat_s = (np.abs(MZ.coords['lat'].values - min(fp_lat))).argmin()-1
    lon_e = (np.abs(MZ.coords['lon'].values - max(fp_lon))).argmin()+1
    lon_w = (np.abs(MZ.coords['lon'].values - min(fp_lon))).argmin()-1
    

    north = MZ.sel(lat = MZ.coords['lat'][lat_n],
                   lon = slice(MZ.coords['lon'][lon_w],MZ.coords['lon'][lon_e])).drop(['lat'])
    south = MZ.sel(lat = MZ.coords['lat'][lat_s],
                   lon = slice(MZ.coords['lon'][lon_w],MZ.coords['lon'][lon_e])).drop(['lat'])
    east = MZ.sel(lon = MZ.coords['lon'][lon_e],
                  lat = slice(MZ.coords['lat'][lat_s],MZ.coords['lat'][lat_n])).drop(['lon'])
    west = MZ.sel(lon = MZ.coords['lon'][lon_w],
                  lat = slice(MZ.coords['lat'][lat_s],MZ.coords['lat'][lat_n])).drop(['lon'])
              
    interp_height = fp_height
    N = interp_lonlat(interp_heights(north, vmr_var_name,interp_height),vmr_var_name,fp_lon).rename({vmr_var_name : vmr_var_name+'_n'})        
    S = interp_lonlat(interp_heights(south, vmr_var_name,interp_height),vmr_var_name,fp_lon).rename({vmr_var_name : vmr_var_name+'_s'})     
    E = interp_lonlat(interp_heights(east, vmr_var_name,interp_height),vmr_var_name,fp_lat).rename({vmr_var_name : vmr_var_name+'_e'})     
    W = interp_lonlat(interp_heights(west, vmr_var_name,interp_height),vmr_var_name,fp_lat).rename({vmr_var_name : vmr_var_name+'_w'}) 

    MZT_edges = N.merge(E).merge(S).merge(W)
    MZT_edges.attrs['title'] = "MOZART volume mixing ratios at domain edges"
    MZT_edges.attrs['author'] = getpass.getuser()
    MZT_edges.attrs['date_created'] = np.str(dt.datetime.today())
    
    return MZT_edges
    

def MOZART_BC_nc(start = '2012-01-01', end = "2014-09-01", species = 'CH4', filename = None, domain = 'EUROPE', freq = 'M', runname = 'NewEDGAR', output_dir = data_path):   
    """
    Specify end date as 2 months after the month of the last file
    (because the date specified is actually the first day of the next month and
    the range goes up to but doesn't include the last date). Only monthly
    frequency because this is the frequency of the mozart files we have so far.
    
    """
    start_dates = pd.DatetimeIndex(start=start, end = end, freq=freq, closed='left')

    for i in start_dates:
        MZ = MOZART_vmr(species, start = i, end = i, freq=freq, filename = filename)
        MZ_edges = MOZART_boundaries(MZ, domain)
        yearmonth = str(i.year) + str(i.month).zfill(2)
        MZ_edges.to_netcdf(path = join(output_dir, "NAME/bc/%s/%s_%s_%s.nc")
                                                    %(domain,species.lower(),domain,yearmonth), mode = 'w')