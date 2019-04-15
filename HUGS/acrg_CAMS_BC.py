#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:47:07 2018

@author: lw13938

Function makeCAMS_BC() creates a boundary conditions ncdf file 
using ECMWF CAMS data. 
Relies on getCAMSdata, interpheight and interplonlat.

To download new CAMS data you will have to: 
  (1) Sign up for an ECMWF account here: https://apps.ecmwf.int/registration 
      and sign in.
  (2) Retrieve your key from https://api.ecmwf.int/v1/key/
  (3) Copy the contents into a file called .ecmwfapirc in your home directory,
      e.g. /home/lw13938/.ecmwfapirc
      
  If you don't have access to the ECMWF library then:
  (4) From the command line run:
      pip install --user https://software.ecmwf.int/wiki/download/attachments/56664858/ecmwf-api-client-python.tgz

"""
from __future__ import print_function
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
import xarray as xr
import numpy as np
import os
import glob
import getpass
from acrg_name import name
from datetime import datetime as dt
from acrg_tdmcmc.tdmcmc_post_process import molar_mass

data_path = os.getenv("DATA_PATH")

def getCAMSdata(st_date, end_date, gridsize, NESW, species, outputname, nearrealtime = False,
                timeframe="daily"):
    """
    Used by makeCAMS_BC to download ECMWF CAMS data 
    
    Args:
        st_date (string): Start date of form "YYYY-MM-dd"
        end_date (string): End date of form "YYYY-MM-dd". 
            For 1 month use last day of month. 
        gridsize (int/float): Resolution of CAMS output in degrees.
            Possible are: 0.125, 0.25, 0.4, 0.5, 0.75, 1, 1.125, 1.5, 2, 2.5, 3
        NESW (list?) : TODO (should be NWSE?)
        species (string): The species (currently only 'ch4' or 'co') 
        outputname (string): The ECMWF CAMS data output file name
        nearrealtime (bool) : TODO
        timeframe (string) : Extract "daily" or "3hourly" data.
        
    Returns:
        Creates a netcdf file containing CAMS data in data_path/ECMWF_CAMS
        
    NOTES:
        If you want to download data other than ch4 then find the corresponding 
        parameter number in the ECMWF MARS request and add to the 'params' 
        dictionary.
        
    """
    from ecmwfapi import ECMWFDataServer
    area = "%s/%s/%s/%s" % (NESW[0], NESW[2], NESW[4], NESW[6])
    params = {'ch4' : '4.217','co': '123.210'}     #Dictionary of species' paramater number 
    if nearrealtime == True:
        dataset = "cams_nrealtime"
        expver = "0001"
    else:
        dataset = "cams_reanalysis"
        expver = "eac4"

    if timeframe == "daily":
        time = "00:00:00"
    elif timeframe == "3hourly":
        time = "00:00:00/03:00:00/06:00:00/09:00:00/12:00:00/15:00:00/18:00:00/21:00:00"

    server = ECMWFDataServer()
    server.retrieve({
        "class": "mc",
        "dataset": dataset,
        "date": st_date+"/to/"+end_date,
        "expver": expver,
        "levelist": "1/2/3/5/7/10/20/30/50/70/100/150/200/250/300/400/500/600/700/800/850/900/925/950/1000",
        "levtype": "pl",
        "param": params[species]+"/129.128",
        "step": "0",
        "stream": "oper",
        "grid" : str(gridsize)+"/"+str(gridsize),
        #"time": "00:00:00",
        "time": time,
        "type": "an",
        "format" : "netcdf",
        "area" : area,                     #NWSE
        "target": outputname,
    })
    
def interpheight(nesw, fp_height, species, lonorlat=None):
    """
    Interpolates the CAMS data to the NAME heights
    
    Args:
        nesw (dataset) : The N, E, S or W BC CAMS boundary data
        fp_height (array) : NAME footprint heights
        species (string) :  The species of interest
        lonorlat (string) : Whether you're interpolating along the 'longitude' 
            (N or S) or the 'latitude' (E or W).
            
    Returns:
        dataset : CAMS BC data interpolated to NAME heights
        
    """
    if lonorlat == 'longitude':     
        interp = np.zeros((len(fp_height),len(nesw.longitude) ))
    elif lonorlat == 'latitude':
        interp = np.zeros((len(fp_height),len(nesw.latitude) ))
    else:
        print("Please specify either lonorlat='longitude' or 'latitude'")
        return None
    for j in range(len(nesw['z'][0,:])):
        interp[:,j] = np.interp(fp_height, nesw['z'][:,j][::-1], nesw[species][:,j][::-1])
            
    ds2 = xr.DataArray(interp, coords=[fp_height, nesw[lonorlat].values], dims=['height', lonorlat])
    ds2 = ds2.to_dataset(name=species)
    return ds2

def interplonlat(nesw, fp_lonorlat, species, lonorlat=None):
    """
    Interpolates the CAMS data to the NAME longitudes and latitudes
    
    Args:
        nesw (dataset) : The N, E, S or W BC CAMS boundary data
        fp_lonorlat (array) : NAME footprint longitudes or latitudes
        species (string) :  The species of interest
        lonorlat (string) : Whether you're interpolating along the 'longitude' 
            (N or S) or the 'latitude' (E or W).
            
    Returns:
        dataset : CAMS BC data interpolated to NAME longitudes or latitudes
        
    """
    interp = np.zeros(( len(nesw.height),len(fp_lonorlat) ))
    for j in range(len(nesw.height)):
        if lonorlat == 'latitude':
            interp[j, :] = np.interp(fp_lonorlat, nesw[lonorlat].values[::-1], nesw[species][j,:][::-1])
        else:
            interp[j, :] = np.interp(fp_lonorlat, nesw[lonorlat].values, nesw[species][j,:])
            
    ds2 = xr.DataArray(interp, coords=[nesw.height.values, fp_lonorlat], dims=['height', lonorlat[0:3]])
    ds2 = ds2.to_dataset(name=species)
    return ds2

def write_CAMS_BC_tonetcdf(vmr_n, vmr_e, vmr_s, vmr_w, st_date, species, domain, outdir):
    """
    Writes the CAMS BC data to a ncdf file.
    
    Args:
        vmr_n (array): Molar ratio at northern boundary
        vmr_e (array): Molar ratio at eastern boundary
        vmr_s (array): Molar ratio at western boundary
        vmr_w (array): Molar ratio at southern boundary
        st_date (string): Start date of form "YYYY-MM-dd"
        species (string): The species 
        domain (string): The domain which you want the boundary conditions for.
    
    Returns
        netcdf file: Boundary conditions at domain boundaries
    """
    BC_edges = vmr_n.merge(vmr_e).merge(vmr_s).merge(vmr_w)
    BC_edges.expand_dims('time',2)
    BC_edges.coords['time'] = (dt.strptime(st_date, '%Y-%m-%d'))
    
    BC_edges.attrs['title'] = "ECMWF CAMS "+species+" volume mixing ratios at domain edges"
    BC_edges.attrs['author'] = getpass.getuser()
    BC_edges.attrs['date_created'] = np.str(dt.today())
    
    if os.path.isdir(outdir+"/NAME/bc/%s/" % domain) == False:
        os.makedirs(outdir+"/NAME/bc/%s/" % domain)
    
    BC_edges.to_netcdf(path = outdir+"/NAME/bc/%s/%s_%s_%s.nc"
                       %(domain,species.lower(),domain,dt.strptime(st_date, '%Y-%m-%d').strftime('%Y%m')), mode = 'w')

def makeCAMS_BC(domain, species, st_date, end_date, gridsize, outdir=None):
    """
    This function makes boundary conditions ncdf file for a given NAME domain. 
    The boundary conditions are the mean of daily estimates at midnight for the 
    defined time period.
    
    Args:
        domain (string): The domain which you want the boundary conditions for.
        species (string): The species 
        st_date (string): Start date of form "YYYY-MM-dd"
        end_date (string): End date of form "YYYY-MM-dd". 
            For 1 month use last day of month (see example). 
        gridsize (int/float): Resolution of CAMS output in degrees.
            Possible are: 0.125, 0.25, 0.4, 0.5, 0.75, 1, 1.125, 1.5, 2, 2.5, 3
        
    Returns
        netcdf file: Boundary conditions at domain boundaries
        
    Example:
        makeCAMS_BC('EUROPE', 'ch4', '2017-08-01', '2017-08-31', 3)
        
    NOTES:
        If working with a species other than ch4 or co then you'll have to update 
        the molar masses and getCAMSdata().
    """
    
    
    if outdir == None:
        outdir = data_path
    
    #data_path = os.getenv("DATA_PATH")
    pathtoBCs = data_path+'/ECMWF_CAMS/'
    
    #Set-up a few things and do some checks
    species = species.lower()
    domain = domain.upper()
    gridsize = float(gridsize)
    
    if os.path.isfile(outdir+"/NAME/bc/%s/%s_%s_%s.nc"
                       %(domain,species,domain,dt.strptime(st_date, '%Y-%m-%d').strftime('%Y%m'))):
        print('Boundary condition file %s_%s_%s.nc already exists.' %(species,domain,dt.strptime(st_date, '%Y-%m-%d').strftime('%Y%m'))) 
        print('Delete old one first to replace it.')
        return(None)
    
    if gridsize not in [0.125, 0.25, 0.4, 0.5, 0.75, 1, 1.125, 1.5, 2, 2.5, 3]:
        print("'gridsize' must be either:")
        print(0.125, 0.25, 0.4, 0.5, 0.75, 1, 1.125, 1.5, 2, 2.5, 3)
        print(" Change it and try again")
        return(None)
        
    if os.path.isdir(data_path+"NAME/fp/" + domain) == False:
        print("No footprint file for domain %s" % domain)
        print("Make this first and then generate the BCs")
        return(None)
    
    #Get NAME lats/lons and heights
    listoffiles = glob.glob(data_path+"/NAME/fp/" + domain + "/*")
    with xr.open_dataset(listoffiles[0]) as temp:
        fields_ds = temp.load()
    fp_lat = fields_ds["lat"].values
    fp_lon = fields_ds["lon"].values #+ 180
    fp_height = fields_ds["height"].values
    
    #Check to see if BC file already exists. If not then download data
    NESW = [str(int(np.ceil(max(fp_lat)))), ".", str(int(np.floor(max(fp_lon+180)))), 
                ".", str(int(np.floor(min(fp_lat)))),".", str(int(np.ceil(min(fp_lon+180))))]
    outputname = "BC_CAMS_"+species+"_"+"".join(NESW)+"_"+str(gridsize)+"x"+str(gridsize)+"_"+st_date+".nc"
    if os.path.isfile(pathtoBCs+outputname) == False: 
        #Download data
        getCAMSdata(st_date, end_date, gridsize, NESW, species, pathtoBCs+outputname)
    
    #Open CAM dataset and average over the month 
    fn = pathtoBCs+outputname
    #ds = xr.open_dataset(fn)
    ds = name.open_ds(fn)
    ds = ds.mean('time')
       
    #if species == 'ch4':
    #    speciesmm = 16.0425
    speciesmm = molar_mass(species)
    airmm = 28.9644 #Molar mass of air g/mol
    ds['z'] = ds.z/9.80665   #Convert to height (N.B. this is geopotential height!)
    if species == 'ch4':
        ds = ds.rename({species+'_c' :  species})   #ECMWF seemed to change their naming convention – quick fix
    ds[species] = old_div(ds[species] *airmm,speciesmm) #Convert into mol/mol
    
    #Select the gridcells closest to the edges of the  domain and make sure outside of fp
    #lat_n = min( (np.abs(ds.coords['latitude'].values - max(fp_lat))).argmin()+1, len(ds.coords['latitude'].values)-1)
    lat_n =(np.abs(ds.coords['latitude'].values - max(fp_lat))).argmin()
    if ds.coords['latitude'].values[lat_n] < np.max(fp_lat) and lat_n != 0:
        lat_n -= 1
    #lat_s = max( (np.abs(ds.coords['latitude'].values - min(fp_lat))).argmin()-1, 0)
    lat_s = (np.abs(ds.coords['latitude'].values - min(fp_lat))).argmin()
    if ds.coords['latitude'].values[lat_s] > np.min(fp_lat) and lat_s != (len(ds.coords['latitude'].values)-1):
        lat_s += 1
    #lon_e = min( (np.abs(ds.coords['longitude'].values - max(fp_lon))).argmin()+1, len(ds.coords['longitude'].values)-1)
    lon_e =  (np.abs(ds.coords['longitude'].values - max(fp_lon))).argmin()
    if ds.coords['longitude'].values[lon_e] < max(fp_lon) and lon_e != (len(ds.coords['longitude'].values)-1):
        lon_e += 1
    #lon_w = max( (np.abs(ds.coords['longitude'].values - min(fp_lon))).argmin()-1, 0)
    lon_w =  (np.abs(ds.coords['longitude'].values - min(fp_lon))).argmin()
    if ds.coords['longitude'].values[lon_w] > min(fp_lon) and lon_w != 0:
        lon_e -= 1
    
    #Cut to these and then interpolate
    north = ds.sel(latitude = ds.coords['latitude'][lat_n],
                   longitude = slice(ds.coords['longitude'][lon_w],ds.coords['longitude'][lon_e])).drop(['latitude'])
    south = ds.sel(latitude = ds.coords['latitude'][lat_s],
                   longitude = slice(ds.coords['longitude'][lon_w],ds.coords['longitude'][lon_e])).drop(['latitude'])
    east = ds.sel(longitude = ds.coords['longitude'][lon_e],
                  latitude = slice(ds.coords['latitude'][lat_n],ds.coords['latitude'][lat_s])).drop(['longitude'])
    west = ds.sel(longitude = ds.coords['longitude'][lon_w],
                  latitude = slice(ds.coords['latitude'][lat_n],ds.coords['latitude'][lat_s])).drop(['longitude'])
     
    vmr_n = interplonlat(interpheight(north, fp_height, species, lonorlat='longitude'), fp_lon, species, lonorlat='longitude').rename({species : 'vmr_n'})   
    vmr_s = interplonlat(interpheight(south, fp_height, species, lonorlat='longitude'), fp_lon, species, lonorlat='longitude').rename({species : 'vmr_s'}) 
    vmr_e = interplonlat(interpheight(east, fp_height, species, lonorlat='latitude'), fp_lat, species, lonorlat='latitude').rename({species : 'vmr_e'}) 
    vmr_w = interplonlat(interpheight(west, fp_height, species, lonorlat='latitude'), fp_lat, species, lonorlat='latitude').rename({species : 'vmr_w'})      
    
    write_CAMS_BC_tonetcdf(vmr_n, vmr_e, vmr_s, vmr_w, st_date, species, domain, outdir)
    

