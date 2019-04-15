# -*- coding: utf-8 -*-
"""


File to read in standard MOZART output file
Output will contain the timestamp, lat, lon, surface emissions and concentrations
If you want any other fields then you'll need to add them in
    import acrg_MOZART as mozart    
    data=mozart.read('filename')
    print(data.time
    
Can also extract data for sites given lats and lons
sitefile = a text file with the site acronym, lat and then lon separated by spaces or tabs
    import acrg_MOZART as mozart
    data=mozart.filter('filename', 'sitefile')

    

"""
from __future__ import print_function
from __future__ import division
from builtins import str
from past.utils import old_div
from builtins import object
import netCDF4
import numpy as np
import datetime as dt
from acrg_grid.hybridcoords import hybridcoords as hybrid_coords
import bisect
import os
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap
from matplotlib import ticker
import pandas as pd
#import dateutil.relativedelta
#import sys
# ___________________________________________________________________________________________________________________
# CODE TO READ THE DIFFERENT DATA TYPES
# ___________________________________________________________________________________________________________________

 # Class to read in the MOZART output data
 
 # Filename: the full name and file path of the file you want to read in
 # conc_tag: the suffix of the variable of interest that you want to read in.
 # e.g for the variable CO2_VMR_avrg the suffix is '_VMR_avrg' 
 
 # Please not this DOES NOT read in all the variables.
 # If you want a variable that it doesn't read in then add it!
class read(object):
    def __init__(self, filename, conc_tag = '_VMR_avrg'):
    
        print('Reading file : ' + filename)
        
        if type(filename) == tuple:
            filename = filename[0]
        
        data=netCDF4.Dataset(filename)
        

        # Might be multiple tracers
        conc_varname = [i for i in list(data.variables.keys()) if conc_tag in i]      

        # Check that the conc_tag is actually in the list of variables
        if len(conc_varname) == 0:
            print('The concentration tag you gave was not found in the given file')
            print('Please retry using one of the below variables:')
            for i in list(data.variables.keys()):
                print(i)
        
        else:

            conc = []
            conc_units = []
            
            for i in conc_varname:     
                conc.append(data.variables[i][:]) 
                conc_units.append(data.variables[i].getncattr('units'))
            
            
            if 'h0' in filename:
                # Might be multiple tracers
                emis_varname = [i for i in list(data.variables.keys()) if '_SRF_EMIS_avrg' in i]      
        
                emis = []
                emis_units = []
                for i in emis_varname:        
                    emis.append(data.variables[i][:]) 
                    emis_units.append(data.variables[i].getncattr('units'))
                
                
            date = data.variables['date'][:] # Date YYYYMMDD
            secs = data.variables['datesec'][:] # Seconds to be added to above date to make date-time variable
            lon = data.variables['lon'][:].astype('float')
            lat = data.variables['lat'][:].astype('float')
            lev = data.variables['lev'][:].astype('int')
            PS=data.variables['PS'][:].astype('float')
            P0=data.variables['P0'][:].astype('float')
            hyai=data.variables['hyai'][:].astype('float')
            hybi=data.variables['hybi'][:].astype('float')
                    
            # Split up the date using datetime.strptime
            dt_time = [dt.timedelta(seconds=int(secs[i])) for i in np.arange(len(date))]
            dt_date = [dt.datetime.strptime(str(date[i]),'%Y%m%d') for i in np.arange(len(date))]
            
            time_t = [dt_time[i] + dt_date[i] for i in np.arange(len(date))]
            
            P = np.empty((len(date), len(hyai)-1, len(lat), len(lon)))
    
            for i in np.arange(len(date)):         
                P_i = hybrid_coords(hyai, PS[i,:,:],  B=hybi, P0=P0, half=1)
                P[i,:,:,:] = P_i
                print('date ' + str(date[i]) + ' processed')
             
            self.time = time_t
            self.conc = conc
            self.lon = lon
            self.lat = lat
            self.lev = lev
            self.P0 =P0
            self.PS =PS
            self.hyai=hyai
            self.hybi=hybi
            self.pressure = P
            self.date = date
            self.filename = filename     
            
            self.species = str(data.__getattribute__('title')).strip()
            self.case = str(data.__getattribute__('case')).strip()
            self.concunits = conc_units
            self.pressureunits = data.variables['P0'].getncattr('units')
            self.concnames = conc_varname
            
            if 'h0' in filename:
                self.emis = emis             
                self.emissunits = emis_units
                self.emisnames = emis_varname
            
            if 'h2' in filename:
            #if 'h0' in filename:
            
                start_date = data.variables['nbdate'][:]
                dt_start_date = dt.datetime.strptime(str(start_date),'%Y%m%d')
    #            start_date = data.variables['date'][:]
    #            dt_start_date = dt.datetime.strptime(str(start_date[0]),'%Y%m%d')\
    #            - dateutil.relativedelta.relativedelta(months=1)
                self.start_date = dt_start_date
            data.close()
        
# Class to read in the data
"""
format
dimensions:
	lon = 144 ;
	lat = 96 ;
	time = UNLIMITED ; // (24 currently)
variables:
	double lon(lon) ;
		lon:long_name = "longitude" ;
		lon:units = "degrees_east" ;
	double lat(lat) ;
		lat:long_name = "latitude" ;
		lat:units = "degrees_north" ;
	int date(time) ;
		date:long_name = "Date" ;
		date:units = "YYYYMMDD" ;
	double time(time) ;
		time:long_name = "Time" ;
		time:units = "days since 0000-01-01 00:00:00" ;
	double ch4emissions(time, lat, lon) ;
		ch4emissions:long_name = "CH4 emission rate" ;
		ch4emissions:units = "molecules/cm2/s" ;

// global attributes:
		:Title = "CH4_emissions" ;
		:Author = "Ann Stavert" ;
		:Created = "Sun Apr 27 15:22:18 2014" ;
"""
 # Class to read in the MOZART input emissions data file
 
 # Filename: the full name and file path of the file you want to read in
 # emissions_tag: the suffix of the emissions variable
 # time_tag: the name of the time variable
 # emiss_varname: name of the gas of interest e.g. CO2 or CH4 (optional)
     
 # Please not this DOES NOT read in all the variables.
 # If you want a variable that it doesn't read in then add it!
class read_flux(object):
    def __init__(self, filename, emissions_tag_ncdf = 'emissions', time_tag = 'time', emiss_varname = None):
    
        print('Reading file : ' + filename)
        
        if type(filename) == tuple:
            filename = filename[0]
        
        data=netCDF4.Dataset(filename)
        
        if emiss_varname is None:
            emiss_varname = (str(data.__getattribute__('Title'))).strip()[0:3]
        
        # convert from upper to lowercase
        name_dict = {'CO2' : 'co2',\
                    'CH4' :'ch4',\
                    'N2O' : 'n2o'}
        emiss_varname = name_dict[emiss_varname]
        
        emiss = data.variables[emissions_tag_ncdf][:]
        date = data.variables['date'][:] # Date YYYYMMDD
        lon = data.variables['lon'][:].astype('float')
        lat = data.variables['lat'][:].astype('float')
        time = data.variables[time_tag][:].astype('float')
        
        # Split up the date based on position        
        if (date[0] == 1) and (len(date) == 12):
            # we're dealing with a climatology 
            print('This appears to be a climatology. Using 2000 as a default year.')
            year = np.arange(12)
            year[:] = 2000
            month = date
            day = np.arange(12)
            day[:] = 15
            
            dt_date = [dt.datetime(year[i],month[i],day[i]) for i in np.arange(len(date))]
            
        else:
            year = np.asarray([int(((date.astype('str'))[i])[0:4]) for i in np.arange(len(date))])
            month = np.asarray([int(((date.astype('str'))[i])[4:6]) for i in np.arange(len(date))])
            day = np.asarray([int(((date.astype('str'))[i])[6:8]) for i in np.arange(len(date))])
            
            dt_date = [dt.datetime(year[i],month[i],day[i]) for i in np.arange(len(date))]
        
        
        # Calculate monthly means use xray
        import xray
        
        x_data = xray.DataArray(emiss, [('date', dt_date), ('lat', lat), ('lon', lon)])
        monthly_means = x_data.resample('MS', dim='date', how='mean')
        
        # Convert the xray datetime to a normal datetime        
        dt_monthly = [pd.to_datetime(str(i)).replace(tzinfo=None) for i in monthly_means.date.values]        
        
        self.time = time
        self.time_units = data.variables[time_tag].__getattribute__('units')
        self.dt_date = dt_date
        self.year = year
        self.month = month
        self.day = day
        self.emiss = emiss
        self.monthly_time = dt_monthly
        self.monthly_means = monthly_means.values
        self.species = emiss_varname
        self.emis_units = data.variables[emissions_tag_ncdf].__getattribute__('units')  
        self.lon = lon
        self.lat = lat
        self.filename = filename     
        
                 
             



 # Class to read in the netcdf site file written by matt listing the fixed sites 

# sitefile: full name and file path of the file you want to read in
# species: the gas species of interest.
# dir: file path to file of interest

class read_fixed_sitefile_nc(object):
    def __init__(self, sitefile = None, species = 'CH4', dir = '/shared_data/snowy/shared/GAUGE/'):
        
        if sitefile == None:
            sitefile = dir + species.upper() + '/global_obs_stationary.nc'
            if species in ['CH4','ch4']:
                sitefile = dir + species.upper() + '/global_obs_stationary_ch4.nc'
            
        print('Using site file : ' + sitefile)
        
        data=netCDF4.Dataset(sitefile, 'r')

        
        # Extract the data    
        time = data.variables['time'][:] # "seconds since 2004-01-01 00:00:00" ;
        site = data.variables['site'][:]
        network = data.variables['network'][:]
        lon = data.variables['longitude'][:]
        lat = data.variables['latitude'][:]
        alt = data.variables['altitude'] # "m  above 1.9x2.5 MOZART surface level (m)" ;
        conc = data.variables[species.lower()]
        repeatability = data.variables[species.lower()+'_repeatability']
	      
        # Create the time variable
        dateunits = data.variables['time'].getncattr('units')
        sincedate = dateunits[dateunits.find('seconds since ') +14:-1] # seconds since 2014-01-01 00:00:00
                
        time_dt = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in time]
        #time_dt = [dt.datetime(2009,1,1,0,0,0) + dt.timedelta(seconds=(i).astype('int')) for i in time]
        

        self.time = time_dt
        self.lat = lat
        self.lon = lon
        self.alt = alt[:]
        self.alt_units = alt.units
        self.site = site
        self.species = species
        self.species_lc = species.lower()
        self.conc = conc[:]
        self.repeatability = repeatability[:]
        self.units = conc.units
        self.network = network
        self.sitefile = sitefile


 # Class to read in the netcdf site file written by matt listing the column sites (satelite + TCON)  
 
 # sitefile: full name and file path of the file you want to read in
 # species: the gas species of interest.
 # dir: file path to file of interest
 # month: the number month file you want to read in e.g. for Jan set = 1
 # year: the year you want to read in 
class read_column_sitefile_nc(object):
    def __init__(self, sitefile = 0, species = 'CH4', dir = '/shared_data/snowy/shared/GAUGE/', month = 1, year = 2009):
        
        if type(sitefile) == int:
            #sitefile = dir + species + '/global_obs_column_CH4' + str(month).zfill(2) +str(year)+ '.nc'
            sitefile = dir + species.upper() + '/global_obs_column_'+ species.upper() +'/global_obs_column_'+species.upper() + '_'+ str(year)+ str(month).zfill(2) +'.nc'
        
        data=netCDF4.Dataset(sitefile, 'r')
        
        # Extract the data    
        time = data.variables['time'][:] # "seconds since 2004-01-01 00:00:00" ;
        network = data.variables['network'][:]
        lon = data.variables['longitude'][:]
        lat = data.variables['latitude'][:]
        gas_data = data.variables[species.lower()]
        gas_repeatability = data.variables[species.lower()+'_repeatability']
        averaging_kernel = data.variables['averaging_kernel'][:]
        pressure = data.variables['pressure']
       
        # Create the time variable
        dateunits = data.variables['time'].getncattr('units')
        sincedate = dateunits[dateunits.find('seconds since ') +14:-1] # seconds since 2009-01-01 00:00:00
                
        time_dt = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in time]
        #time_dt = [dt.datetime(2009,1,1,0,0,0) + dt.timedelta(seconds=(i).astype('int')) for i in time]

        self.time = time_dt
        self.time_secs = time
        self.lat = lat
        self.lon = lon
        self.no_lev = np.shape(pressure[:])[1]
        self.gasname = species.lower()
        self.conc = gas_data[:]
        self.repeatability = gas_repeatability[:]
        self.units = gas_data.units
        self.averaging_kernel = averaging_kernel
        self.pressure = pressure[:]
        self.pressure_units = pressure.units
        self.network = network
        self.sitefile = sitefile
 

# Class to read in the netcdf site file written by matt listing the mobile GAUGE sites (ferry and aircraft)  

 # sitefile: full name and file path of the file you want to read in
 # species: the gas species of interest.
 # dir: file path to file of interest
 # month: the number month file you want to read in e.g. for Jan set = 1
 # year: the year you want to read in 
class read_mobile_sitefile_nc(object):
    def __init__(self, sitefile = 0, species = 'CH4', dir = '/shared_data/snowy/shared/GAUGE/', month = 1, year = 2003):
        
        if sitefile is None:
            if species == 'CH4':
                sitefile = dir + species.upper() + '/global_obs_mobile_' +species.upper()+'/global_obs_mobile_' +species.upper()+'_'+str(year)+ str(month).zfill(2)+'.nc'
        
            else:
                sitefile = dir + species.upper() + '/global_obs_mobile/global_obs_mobile_'+str(year)+ str(month).zfill(2)+'.nc'

        # Check if the site file exists
        exists = os.path.isfile(sitefile)
                
        if exists :
            
            print('Site file being read:')
            print(sitefile)
            
            data=netCDF4.Dataset(sitefile, 'r')
            
            # Extract the data    
            time = data.variables['time'][:] # "seconds since 2004-01-01 00:00:00" ;
            site = data.variables['site'][:]
            network = data.variables['network'][:]
            scale = data.variables['scale'][:]
            lon = data.variables['longitude'][:]
            lat = data.variables['latitude'][:]
            alt = data.variables['altitude']
            gas_data = data.variables[species.lower()]
            gas_repeatability = data.variables[species.lower()+'_repeatability']
            pressure = data.variables['pressure']
            
            # Create the time variable
            dateunits = data.variables['time'].getncattr('units')
            sincedate = dateunits[dateunits.find('seconds since ') +14:-1] # seconds since 2014-01-01 00:00:00
                    
            time_dt = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in time]
            #time_dt = [dt.datetime(2009,1,1,0,0,0) + dt.timedelta(seconds=(i).astype('int')) for i in time]
    
            self.time = time_dt
            self.time_secs = time
            self.lat = lat
            self.lon = lon
            self.alt = alt[:]
            
            self.alt_units = alt.units
            self.scale = scale
            
            self.gasname = species.lower()
            self.conc = gas_data[:]
            self.repeatability = gas_repeatability[:]
            self.units = gas_data.units
            self.pressure = pressure[:]
            self.pressure_units = pressure.units
            self.network = network
            self.site = site
            self.sitefile = sitefile
            self.fileexists = exists
    
        else:
            print('Sitefile ' + sitefile + ' does not exist')
            self.fileexists = exists




# ___________________________________________________________________________________________________________________
# CODE TO DO USEFUL STUFF
# ___________________________________________________________________________________________________________________
        
 # Class to estimate the pressure levels from a given altitude
 # This uses the scale height and a simple atmospheric model
 # P = P0 * e^(-Z/H)
 # Where P = Pressure
 # P0 = surface pressure in Pa
 # -Z = altitude (km)
 # H = scale height (km) this is hard coded to be 7.64km which is the global mean
 # This assumes that the altitude is in m unless other units are given
class calc_pressure(object):
    def __init__(self, altitude, P0, units='m'):

        from math import exp
        
        if units == 'm':
            altitude = altitude/1000.0
        elif units =='metres':
            altitude = altitude/1000.0
        elif units =='km':
            altitude = altitude
        elif units =='miles':
            altitude = altitude*1.609344
        elif (units in {'m','km','miles'}) == False:
            print('the units you have given are not a listed option')
            print('please give the altitude in m, km or miles')
        
        pressure = P0*exp((-1*altitude)/7.64) 
        
        self.pressure = pressure
 
 # Calculates altitude from pressures using the standard scale height 7.64 km.
 # Pressure in Pa.       
 # P0 = surface pressure in Pa
 # P =  pressure in Pa
def calc_altitude(P, P0, h0=7.64e3):
    alt = -h0*np.log(old_div(P,P0))
    return alt

 # Class to read in the site file txt version
class read_sitefile_txt(object):
    def __init__(self, sitefile):
        
        if type(sitefile) == tuple:
            sitedata=np.genfromtxt(sitefile[0], dtype=str, skip_header=1)
        elif type(sitefile) == str:
            sitedata=np.genfromtxt(sitefile, dtype=str, skip_header=1)
        
        sitenames = sitedata[:,0]
        lat = sitedata[:,1]
        lon = sitedata[:,2]
        alt = sitedata[:,3]
        
        self.sitenames = sitenames
        self.lat = lat.astype('float')
        self.lon = lon.astype('float')
        self.alt = alt.astype('float')
        self.filename = sitefile
        
 # Class to extract the lat lon for the correct site from the text site files  
class extract_site_info(object):
    def __init__(self, sitefile, sitename):
        
        if sum([sitefile[0].find('acf'), sitefile[0].find('ferry')])  < -1:
            sitedata=read_sitefile_txt(sitefile)
        else:
            sitedata=read_sitefile_GONZI_nc(sitefile)
            
        site_i = (np.where(sitedata.sitenames==sitename))[0]      
        
        self.sitename = sitedata.sitenames[site_i]        
        self.lat = sitedata.lat[site_i]
        self.lon = sitedata.lon[site_i]
        self.alt = sitedata.alt[site_i]

# Class to match a point to the closest lat/lon in an array of lat/lons using bisect

# lat: the latitude in degrees of your point of interest
# lon: the longitude in degrees of your point of interest
# lat_array: 2D array of latitudes in degress
# lon_array: 2D array of longitudes in degress

class match_latlon(object):
    def __init__(self, lat, lon, lat_array, lon_array):
        
        # NB: Assuming evenly spaced grid
        lat_spacing = lat_array[1] - lat_array[0]
        lon_spacing = lon_array[1] - lon_array[0]
        
        
        # If the lon array is from 0 to 360
        # then need to check if the lon point is < 0
        # if it's < 0 then convert it
        if min(lon_array) >= 0 and lon < 0 :
            lon = lon + 360
        
        # If the lon array is from -180 to 180
        # then need to check that the lon point is > 180
        # if it's > 180 then convert it
        if min(lon_array) >= 0 and lon < 0 :
            lon = 360 - lon
        
        
        lat_index = bisect.bisect(lat_array+(old_div(lat_spacing,2)), lat) # nb: the adjustment shifts the grid so that it returns the closest point
        lon_index = bisect.bisect(lon_array+(old_div(lon_spacing,2)), lon) # nb: the adjustment shifts the grid so that it returns the closest point


        # Check the edges of the lon grid
        if lon_index == len(lon_array):
            lon_index = 0
            
        
        self.inputlocation = np.array((lat,lon))
        self.lat_array = lat_array
        self.lon_array = lon_array
        self.closestpoint = np.array((lat_array[lat_index], lon_array[lon_index]))
        self.closestindex = np.array((lat_index, lon_index))
        








# ___________________________________________________________________________________________________________________
# CODE TO MATCH THE DIFFERENT DATA TYPES
# ___________________________________________________________________________________________________________________

        
# Class to filter the data for fixed locations
# e.g. towers NOT mobile locations
# This uses an individual MOZART history file
# and matt's netcdf site file which contains the lat, lon and alt for fixed sites

# mzfile: full name and path for the MOZART file of interest
# conc_tag: the suffix of the variable of interest that you want to read in.
# e.g for the variable CO2_VMR_avrg the suffix is '_VMR_avrg' 
# sitefile: file listing the fixed sites
# Ave: set if you want to take the average of the bottom 7 levels rather than try and match the height to the pressure levels

# NB: returns a 3D array (3x3x3) where the central point is the closest to the given fixed location
class data_filter_fixed(object):
    def __init__(self, mzfile, conc_tag = '_VMR_avrg', sitefile=None, Ave=0):
        
        # Read MOZART file name
        data = read(mzfile, conc_tag=conc_tag)
        
        # Read site info file
        # siteinfo = read_sitefile_txt(sitefile)
        species = data.species
        siteinfo = read_fixed_sitefile_nc(species=species, sitefile=sitefile)    
         
        # create parameters to store output
        # initialise to nans
        pressures = np.empty((len(siteinfo.site), len(data.time), 3, 3, 3))*np.nan  

        # need to determine how many tracers there are in the file
        conc_no  = len(data.concnames)    
        
        concs = np.empty((conc_no, len(siteinfo.site), len(data.time), 3, 3, 3))*np.nan 
        concs_sd = np.empty((conc_no, len(siteinfo.site), len(data.time), 3, 3, 3))*np.nan 
        
        levs = np.empty((len(siteinfo.site),len(data.time),3))*np.nan 
        
        emissions = np.empty((conc_no, len(siteinfo.site), len(data.time), 3, 3))*np.nan 
        
        matched_lats = np.empty((len(siteinfo.site), 3))*np.nan 
        matched_lons = np.empty((len(siteinfo.site), 3))*np.nan 
        matched_levs = np.empty((len(siteinfo.site), len(data.time), 3))*np.nan 
        
        site_pressure = np.empty(len(siteinfo.site))*np.nan         
        
        #Convert to an array for ease of access
        allconcs = np.array(data.conc)
        allemis = np.array(data.emis)

        
        # loop through each lat/lon in the siteinfo
        for j in np.arange(len(siteinfo.lat)):
            
            
            # use the match_latlot code which is based on bisect rather than calculating the exact distance
            latlon_index = match_latlon(siteinfo.lat[j],siteinfo.lon[j],data.lat, data.lon)      
            
            # As it's tall tower then we'll want the data for all time stamps
            # Extract column pressure at the correct lat/lon for all timestamps
            # This should be a time by lev array
            # column_P = np.squeeze(data.pressure[:,[np.arange(len(data.hyai)-1)],haversine.mindist_index[0], haversine.mindist_index[1]])        

            # Changed 16/1/2015 to extract
            # the closest match and then a cube surrounding that point, 
            # - north, south, east, west, above and below

            # find the lat and lon range
            print('site: ' + siteinfo.site[j])
            print('site postion: ' + str(siteinfo.lat[j]) + ', ' + str(siteinfo.lon[j]))
              
            
            # Adjustments for hitting the edge of the grid
            # lat index = 0 i.e. south pole
            if latlon_index.closestpoint[0] == 0:
                lat_range = np.squeeze([latlon_index.closestindex[0], latlon_index.closestindex[0]+1])
                matched_lats[j,0:2] = data.lat[lat_range]
                
                
            # lat index  = 95 i.e. north pole
            elif latlon_index.closestpoint[0] == 95:
                lat_range = np.squeeze([latlon_index.closestindex[0]-1, latlon_index.closestindex[0]])
                matched_lats[j,0:2] = data.lat[lat_range]
                
            else:            
                lat_range = np.squeeze([latlon_index.closestindex[0]-1, latlon_index.closestindex[0], latlon_index.closestindex[0]+1])
                matched_lats[j,:] = data.lat[lat_range]
                

            
            # Adjustments for hitting the edge of the grid
            # lon index = 0 i.e. western edge
            if latlon_index.closestindex[1] == 0:
                lon_range = [143,0,1]
            
            # lon index  = 143 i.e. eastern edge
            elif latlon_index.closestindex[1] == 143:
                lon_range = [142,143,0]
                
            else:            
                lon_range = np.squeeze([latlon_index.closestindex[1]-1, latlon_index.closestindex[1], latlon_index.closestindex[1]+1])
            
            matched_lons[j,:] = data.lon[lon_range]
            
            
            print('model lats: ' + str(matched_lats[j,:]))
            print('model lons: ' + str(matched_lons[j,:]))

            

            
            # Extract the column pressure at each time point for the matching (central) point of the cube
            # Pressure is time x lev x lat x lon
            column_P = np.squeeze(data.pressure[:,:,latlon_index.closestindex[0], latlon_index.closestindex[1]])        
            
            
            if Ave != 0:
                # Just take the average of the bottom 7 levels that's all the data roughly < 1 km
    
                # Put data for each lat/lon (i.e. j value) into output arrays 
                # I want the lowest 7 levels which are actually the LAST 7 not the first
                index = np.empty(7)
                index[:] = len(data.hyai)-1
                index = index - np.arange(7) -1
                pressures[j,:] = np.mean(np.squeeze(column_P[:,[index]]), axis=1)
                
                # Extract the corresponding concentrations and emissions
                conc_j = allconcs[:,:, latlon_index.closestindex[0], latlon_index.closestindex[1]]
                concs[j,:] = np.mean(conc_j[:,:,[index]], axis=2)
                concs_sd[j,:] = np.std(conc_j[:,:,[index]], axis=2)
                
    
            else:
                
                
                
                # Convert the altitude to a pressure using P0 from the model
                site_pressure[j] = (calc_pressure(siteinfo.alt[j], data.P0, units=siteinfo.alt_units)).pressure             
                print('site pressure: ' + str(site_pressure[j]))
                
                # Loop through each time step and match site pressure to column level
                # Extract the cube of data
                # Store the positions
                for i in np.arange(len(data.time)):
                    # Find the index of the closest level based on pressure
                    # column_P is time x lev
                    lev_index = np.where(abs(column_P[i,:] - site_pressure[j]) == min(abs(column_P[i,:] - site_pressure[j])))[0]
                    
                    # As I'm using "fancy' indexing rather than slicing I need to do each dimension separately 
                    # Extract data for time = i
                    pressures_i = np.squeeze(data.pressure[i,:,:,:])
                    concs_i = allconcs[:,i,:,:,:]
                    emissions_i = allemis[:,i,:,:]
                    
                    # Extract data for lat range
                    pressures_lat = pressures_i[:,lat_range,:]
                    concs_lat = concs_i[:,:,lat_range,:]
                    emissions_lat = emissions_i[:,lat_range,:]
                    
                    # Extract data for lon range  
                    pressures_lon = pressures_lat[:,:,lon_range]
                    concs_lon = concs_lat[:,:,:,lon_range]
                    emissions_lon = emissions_lat[:,:,lon_range]
                    
                    #pdb.set_trace()
                    
                    # Define the range of the height of the cube
                    # NB: the levels are 1 based while the levels are 1 based
                    # if using the bottom level
                    if lev_index == 55:
                        lev_i = np.squeeze([54,55])
                                                
                        # store the level numbers used                    
                        levs[j,i,0:2] =  [55, 56]                  
                        
                        #print('lev_i: ' + str(lev_i)                        
                        
                        # extract and store the pressure levels used and corresponding concs
                        if len(lat_range) == 2:
                            pressures[j,i,1:3,0:2,:] = pressures_lon[lev_i,:,:]
                            concs[:,j,i,1:3,0:2,:] = concs_lon[:,lev_i,:,:]
                        else:
                            pressures[j,i,1:3,:,:] = pressures_lon[lev_i,:,:]
                            concs[:,j,i,1:3,:,:] = concs_lon[:,lev_i,:,:]
                    
                        
                    else:
                        lev_i = np.squeeze([lev_index-1, lev_index, lev_index+1])
                    
                        
                        # store the level numbers used  
                        # NB: levels are 1 based while the index is 0 based
                        levs[j,i,:] =  [lev_index, lev_index+1, lev_index+2]                    
                        
                        #print('lev_i: ' + str(lev_i)
                        
                        # extract and store the pressure levels used and corresponding concs
                        if len(lat_range) == 2:
                            pressures[j,i,:,0:2,:] = np.squeeze(pressures_lon[lev_i,:,:])
                            concs[:j,i,:,0:2,:]  = np.squeeze(concs_lon[:,lev_i,:,:])
                        else:
                            pressures[j,i,:,:,:] = np.squeeze(pressures_lon[lev_i,:,:])
                            concs[:,j,i,:,:,:]  = np.squeeze(concs_lon[:,lev_i,:,:])
                
                    if len(lat_range) == 2 :
                        emissions[:,j,i,0:2,:] = emissions_lon
                    else:
                        emissions[:,j,i,:,:] = emissions_lon
                       
               
                    
        self.site = siteinfo.site
        self.sitetype = 'TT'
        self.sitenames = siteinfo.site
        self.site_lat = siteinfo.lat
        self.site_lon = siteinfo.lon
        self.site_alt = siteinfo.alt
        self.site_pressure = site_pressure
        self.time = data.time
        
        self.model_pressure = np.squeeze(pressures)
        self.model_lat = matched_lats
        self.model_lon = matched_lons
        self.model_levs = matched_levs
        self.conc = np.squeeze(concs)
        self.conc_sd = np.squeeze(concs_sd)
        self.emis = np.squeeze(emissions)
        self.concnames = data.concnames
        self.emisnames = data.emisnames
        
        self.case = data.case.strip()
        self.species = data.species.strip()
        self.mzfile = data.filename.strip()
        self.sitefile = sitefile        
        self.concunits = data.concunits
        self.emissunits = data.emissunits
        self.pressureunits = data.pressureunits         
        



# Class to filter the data
# This uses an individual MOZART history file
# and Matt's netcdf site file which contains the lat, lon and alt for column sites

# mzfile: full name and path for the MOZART file of interest
# conc_tag: the suffix of the variable of interest that you want to read in.
# e.g for the variable CO2_VMR_avrg the suffix is '_VMR_avrg' 
# sitefile: file listing the fixed sites
# singlesite: set to the three letter acronym of a single site if you just want a single site

class data_filter_column(object):
    def __init__(self, mzfile, sitefile, conc_tag = '_VMR_avrg', singlesite = None):
        
        # Read MOZART file name
        data = read(mzfile, conc_tag = conc_tag) 
        
        # Read site info file
        species = data.species
        columndata = read_fixed_sitefile_nc(species=species, sitefile=sitefile)
        
        # Determine how many sites we're extracting for
        if singlesite != None:
            sites = [singlesite]
        else:
            sites = columndata.site
        
        # create parameters to store output
        # initialise to nans
        # need to determine how many tracers there are in the file
        conc_no  = len(data.concnames)    

        model_pressures = np.empty((len(sites), len(data.time), len(data.lev),))*np.nan 
        model_concs = np.empty((conc_no, len(sites), len(data.time), len(data.lev)))*np.nan 
        
        # Lats and Lon are not going to change with time
        matched_lats = np.empty((len(sites)))*np.nan 
        matched_lons = np.empty((len(sites)))*np.nan 

        # Model times will be identical for all locations        
        model_times = data.time
        

        # loop through each site
        for j in np.arange(len(sites)):
            
            # Extract the index for that site in the column data file
            CD_j = np.where(columndata.site == sites[j])[0]

            # Use the match_latlon which is based on bisect
            # To identify the closest model point
            latlon_index = match_latlon(columndata.lat[CD_j],columndata.lon[CD_j],data.lat, data.lon)      

            print('Matching site ' + sites[j])
            print('Actual location: ' + str(columndata.lat[CD_j]) + ', ' + str(columndata.lon[CD_j]))
            print('Model matched location: ' + str(latlon_index.closestpoint[0]) + ', ' + str(latlon_index.closestpoint[1]))

            # Extract the matched location                
            matched_lats[j] = data.lat[latlon_index.closestindex[0]]
            matched_lons[j] = data.lon[latlon_index.closestindex[1]]
            
            # Extract the column pressure at the matching time point for the matching lat/lon
            # Pressure and conc are time x lev x lat x lon
            model_pressures[j,:] = np.squeeze(data.pressure[:,:, latlon_index.closestindex[0], latlon_index.closestindex[1]])     
            model_concs[:,j,:] = np.squeeze(data.conc[:,:,:, latlon_index.closestindex[0], latlon_index.closestindex[1]])
        
                    
        self.sitetype = 'Column'
        self.site_lat = columndata.lat
        self.site_lon = columndata.lon
        self.site = sites
        self.concnames = data.concnames
        
        self.model_time = np.array(model_times)
        self.model_pressure = model_pressures
        self.model_lat = matched_lats
        self.model_lon = matched_lons
        self.conc = model_concs
        
        self.case = data.case.strip()
        self.species = species
        self.mzfile = data.filename.strip()
        self.sitefile = sitefile        
        self.concunits = data.concunits
        self.pressureunits = data.pressureunits    



# Class to filter the data
# This uses an individual MOZART history file
# and a site file which contains the lat, lon, alt and time for moving sites

# mzfile: full name and path for the MOZART file of interest
# conc_tag: the suffix of the variable of interest that you want to read in.
# e.g for the variable CO2_VMR_avrg the suffix is '_VMR_avrg' 
# sitefile: file listing the fixed sites

class data_filter_mobile(object):
    def __init__(self, mzfile, conc_tag = '_VMR_avrg', sitefile = None):   
                
    
        # Read MOZART file name
        data = read(mzfile, conc_tag = conc_tag)
        
        species = data.species
        #print('reading site file : ' 
        print(sitefile)
        
        # Read site info file        
        siteinfo = read_mobile_sitefile_nc(sitefile = sitefile, species = species, month = data.time[0].month, year = data.time[0].year)
        
        # only proceed if the site file exists
        if siteinfo.fileexists :
            
            matched_data = data_match_mobile(species = species, \
                                            model_conc = data.conc, \
                                            model_lat = data.lat, \
                                            model_lon = data.lon, \
                                            model_time = data.time, \
                                            model_P0 = data.P0, \
                                            model_pressure = data.pressure, \
                                            model_emission = 0, \
                                            obs_conc = siteinfo.conc, \
                                            obs_lat = siteinfo.lat, \
                                            obs_lon = siteinfo.lon, \
                                            obs_time = siteinfo.time, \
                                            obs_pressure = siteinfo.pressure, \
                                            obs_alt = siteinfo.alt, \
                                            obs_alt_units = siteinfo.alt_units, \
                                            quiet = 1, \
                                            concnames = data.concnames)
         
                
            self.network = siteinfo.network
            self.site = siteinfo.site
            self.sitetype = 'mobile'
            self.case = data.case.strip()
            self.species = species
            self.mzfile = mzfile
            self.sitefile = sitefile
            self.concunits = data.concunits
            self.pressureunits = data.pressureunits
            
            self.site_lat = siteinfo.lat
            self.site_lon = siteinfo.lon
            self.site_alt = siteinfo.alt
            self.site_pressure = siteinfo.pressure
            self.site_conc = siteinfo.conc
            self.site_repeat = siteinfo.repeatability
            self.site_units = siteinfo.units
            self.site_time = siteinfo.time
            
            self.model_pressure = matched_data.matched_pressure
            self.model_lat = matched_data.matched_lat
            self.model_lon = matched_data.matched_lon
            self.model_time = matched_data.matched_time
            self.model_units = data.concunits
            
            self.conc = matched_data.matched_conc
            
            self.fileexists = True

            
        else:
            print('There is no matching mobile obs data for : ' + mzfile)
            self.fileexists = False
 

    
# Generalised code to match model 4D array (time/lat/lon/P) to given obs vector (dim = time) with associated lat, lons and P (alt) 
# Assumes that the model and obs times are given as datetimes
# Set quiet = 0 to stop matched info being printed
class data_match_mobile(object):
    def __init__(self, species = 0, \
                model_conc = 0, \
                model_lat = 0, \
                model_lon = 0, \
                model_time = 0, \
                model_P0 = 0, \
                model_pressure = 0, \
                model_emission = 0, \
                obs_conc = 0, \
                obs_lat = 0, \
                obs_lon = 0, \
                obs_time = 0, \
                obs_pressure = 0, \
                obs_alt = 0, \
                obs_alt_units = 0, \
                quiet = 1, \
                concnames = ''):   
                
            # check if the matching will be using alt or P
            if type(obs_pressure) == type(0):
                if type(obs_alt) == type(0):
                    print('Not obs pressure or altitude were given')
                    print('Assuming ground level')
 
 
            # Put in checks of the inputs
            if type(model_time) == type(0):
                print('You need to give model time')
            if type(model_conc) == type(0):
                print('You need to give model concentrations')
            if type(model_lat) == type(0):
                print('You need to give model lat')
            if type(model_lon) == type(0):
                print('You need to give model lon')
            if type(model_pressure) == type(0):
                print('You need to give model pressure')
            if type(model_P0) == type(0):
                print('You need to give model P0')
                
            if type(obs_time) == type(0):
                print('You need to give obs time')
            if type(obs_conc) == type(0):
                print('You need to give obs conc')
            if type(obs_lat) == type(0):
                print('You need to give obs lat')
            if type(obs_lon) == type(0):
                print('You need to give obs lon')
            

            
             
            # Convert the model times and the obs times to seconds
            # Assumes that these are given as datetimes
            
            model_secs = np.asarray([(i - dt.datetime(2009,1,1,0,0,0)).total_seconds() for i in model_time])
            
            obs_secs = np.asarray([(i - dt.datetime(2009,1,1,0,0,0)).total_seconds() for i in obs_time])

            # need to determine how many tracers there are in the file
            conc_no  = len(concnames)    

 
            # create parameters to store output
            matched_pressure = np.empty(len(obs_time))      
            matched_conc = np.empty(len(conc_no, obs_time))
            matched_time = []
            matched_lat = np.empty(len(obs_time))
            matched_lon = np.empty(len(obs_time))
            matched_emissions = np.empty(len(conc_no, obs_time))
            
            # loop through each lat/lon in the same time range as the model output
            for j in np.arange(len(obs_time)):
                
                # Use the haverseine code to determine the closest model grid point to the obs location
                latlon_index = (match_latlon(obs_lat[j],obs_lon[j],model_lat, model_lon)).closestindex      
                matched_lat[j] = model_lat[latlon_index[0]]                
                matched_lon[j] = model_lon[latlon_index[1]] 
                
                
                # Match obs timestamp to the closest model timestamp
                time_gap = model_secs[1] - model_secs[0]
                timeindex_j = bisect.bisect(model_secs + (old_div(time_gap,2)), obs_secs[j])
                
                
                #pdb.set_trace()                
                
                # if it's AFTER the last model point then bisect returns the number of elements in the data.time array
                if timeindex_j == len(model_time):
                    timeindex_j = len(model_time) - 1
                    print('Switched to last element of time array')
                
                matched_time.append(model_time[timeindex_j])
                
                
                # Determine the closest level
                # if there's no alt or pressure given assuming it's the surface (which for mozart is the last one)
                #pdb.set_trace()  

                # Extract column pressure at the correct lat/lon for the  matching timestamp
                column_P = np.squeeze(model_pressure[timeindex_j,:,latlon_index[0], latlon_index[1]])                
                
                if type(obs_pressure) == type(0) and type(obs_alt) == type(0):
                    
                    lev_i = -1
                
                else:
                    # if obs pressure isn't given use alt
                    if type(obs_pressure) == type(0) or obs_pressure[j] == -1:

                        obs_pressure_j = calc_pressure(obs_alt[j], model_P0, units=obs_alt_units).pressure                    
                        # Match site pressure to column level
                        # as the pressure levels aren't evenly matched i'd need to find the gap and then compare to 
                        # the pressures  on either side which is unlikely to be much faster than this anyway
                        lev_i = np.where(abs(column_P - obs_pressure_j) == min(abs(column_P - obs_pressure_j)))[0]
                        
                    else:
                        # ferry P = -1
                        if obs_pressure[j] == -1:
                            # use surface
                            lev_i = -1
                            
                        else:
                            
                            obs_pressure_j = obs_pressure[j]
                    
                            # Match site pressure to column level
                            # as the pressure levels aren't evenly matched i'd need to find the gap and then compare to 
                            # the pressures  on either side which is unlikely to be much faster than this anyway
                            lev_i = np.where(abs(column_P - obs_pressure_j) == min(abs(column_P - obs_pressure_j)))[0]
             
                matched_pressure[j] = np.squeeze(column_P[lev_i])
                     
                # Extract the corresponding concentrations and emission
                # Put data for each lat/lon (i.e. j value) into output arrays            
                
                matched_conc[:,j] = np.squeeze(model_conc[:,timeindex_j,lev_i, latlon_index[0],latlon_index[1]])
                
                if type(model_emission) != type(1):
                    matched_emissions[:,j] = np.squeeze(model_emission[:,timeindex_j,lev_i, latlon_index[0],latlon_index[1]])
    
    
                if quiet != 0 :
                    np.shape(obs_lat)
                    type(obs_lat)
                    print('Obs lat: ' + str(obs_lat[j]))
                    print('Model lat: ' + str(matched_lat[j]))
                    print('Obs lon: ' + str(obs_lon[j]))
                    print('Model lon: ' + str(matched_lon[j]))
                       
                    print('Obs time: ' + str(obs_time[j]))
                    print('Model time: ' + str(matched_time[j]))
                    
                    if lev_i != -1 :
                        print('Obs pressure: ' + str(obs_pressure_j))
                    print('Model pressure: ' + str(matched_pressure[j]))
                    
            self.obs_time = obs_time    
            self.obs_lat = obs_lat
            self.obs_lon = obs_lon
            self.obs_alt = obs_alt
            self.obs_pressure = obs_pressure
            self.obs_conc = obs_conc
            self.concnames = concnames

            self.model_time = model_time
            self.model_lat = model_lat
            self.model_lon = model_lon
            self.model_pressure = model_pressure
            self.model_conc = model_conc
            
            self.matched_time = matched_time
            self.matched_lat = matched_lat
            self.matched_lon = matched_lon
            self.matched_pressure = matched_pressure
            self.matched_conc = matched_conc
            self.matched_emissions = matched_emissions
            
            self.species = species
          
 
 
 
 
# ___________________________________________________________________________________________________________________
# CODE TO WRITE THE DIFFERENT DATA TYPES
# ___________________________________________________________________________________________________________________
            
            
# Class to write out the data from a moving platform

# filtereddata: the output of data_match_mobile
# outdir: the directory you wish to write the file to. Defaults to the directory containing the original MOZART file.
# filename: name for output file defaults to "species"_"casename".mzt.h0."Timestamp"_"sitetype".nc

class write_ncdf_mobile(object):
    def __init__(self, filtereddata, outdir = 0, filename=0):
        
        import os
        
        mzfile = filtereddata.mzfile
        
        if type(outdir) == int:
            outdir = os.path.dirname(mzfile)
    
        
        if type(filename) == int:
            if type(mzfile) == tuple:  
                filetimestamp = (filtereddata.mzfile[0])[(filtereddata.mzfile[0]).find('h0')+ 2: (filtereddata.mzfile[0]).find('.nc')]
            if type(mzfile) == str:
                filetimestamp = filtereddata.mzfile[filtereddata.mzfile.find('h0')+ 2: filtereddata.mzfile.find('.nc')]
            filename = filtereddata.species + '_' + filtereddata.case + '.mzt.h0'+  filetimestamp + '_' + filtereddata.sitetype+'.nc'
        
        print('writing file: ' + outdir + '/'+ filename)
        
        
        #Write NetCDF file
        ncF = netCDF4.Dataset(outdir + '/'+ filename, 'w')
        
        # Create the dimensions
        ncF.createDimension('time', len(filtereddata.site_time))
        
        # Make some global attributes
        ncF.mzfile = filtereddata.mzfile
        ncF.sitefile = filtereddata.sitefile
        ncF.case = filtereddata.case
        ncF.species = filtereddata.species
        ncF.sitetype = filtereddata.sitetype
        
        # Create the variables
        ncsitenames = ncF.createVariable('sitename',type(filtereddata.site[0]), ('time',))        
        
        ncobs_time = ncF.createVariable('obs_time', 'i', ('time',))
        ncobs_lon = ncF.createVariable('obs_lon', 'f', ('time',))
        ncobs_lat = ncF.createVariable('obs_lat', 'f', ('time',))
        ncobs_alt = ncF.createVariable('obs_alt', 'f', ('time',))
        ncobs_press = ncF.createVariable('obs_pressure', 'f', ('time',))
        ncobs_conc = ncF.createVariable('obs_conc', 'f', ('time',))
        ncobs_repeat = ncF.createVariable('obs_repeatability', 'f', ('time',))
        
        ncmodel_time = ncF.createVariable('model_time', 'i', ('time',))
        ncmodel_lon = ncF.createVariable('model_lon', 'f', ('time',))
        ncmodel_lat = ncF.createVariable('model_lat', 'f', ('time',))
        ncmodel_press = ncF.createVariable('model_pressure', 'f', ('time',))


        for i in np.arange(len(filterdata.concnames)):
            ncmodel_conc = ncF.createVariable(filtereddata.concnames[i], 'f', ('time'))
            ncmodel_conc[:] = filtereddata.conc[i,:]
            ncmodel_conc.units = filtereddata.model_units[i]
        
        # Fill the variables
        ncsitenames[:] = filtereddata.site        
                
        # times as seconds since 1/1/2009
        ncobs_time[:] = [(t - dt.datetime(2009,1,1,0,0,0)).total_seconds() for t in filtereddata.site_time]     
    
        ncobs_lon[:] = filtereddata.site_lon
        ncobs_lat[:] = filtereddata.site_lat
        ncobs_alt[:] = filtereddata.site_alt
        ncobs_press[:] = filtereddata.site_pressure
        ncobs_conc[:] = filtereddata.site_conc
        ncobs_repeat[:] = filtereddata.site_repeat
        
        # times as seconds since 1/1/2009
        ncmodel_time[:] = [(t - dt.datetime(2009,1,1,0,0,0)).total_seconds() for t in filtereddata.model_time]     
    
        ncmodel_lon[:] = filtereddata.model_lon
        ncmodel_lat[:] = filtereddata.model_lat
        ncmodel_press[:] = filtereddata.model_pressure

        
        
        
        # Give the variables some attributes        
        ncmodel_lon.units = 'Degrees east'
        ncmodel_lat.units = 'Degrees north'
        ncmodel_conc.units = filtereddata.concunits
        ncobs_conc.units = filtereddata.site_units
        ncmodel_press.units = filtereddata.pressureunits
        ncmodel_time.units = 'seconds since 2009-01-01 00:00:00'
        
        ncF.close()
        print("Written " + outdir + '/'+ filename)



# Class to write out the data from a stationary platform

# filtereddata: the output of data_match_fixed
# outdir: the directory you wish to write the file to. Defaults to the directory containing the original MOZART file.
# filename: name for output file defaults to "species"_"casename".mzt.h0."Timestamp"_"sitetype".nc

class write_ncdf_fixed(object):
    def __init__(self, filtereddata, outdir = 0, filename=0):
        
        import os
        
        mzfile = filtereddata.mzfile
        
        if type(outdir) == int:
            outdir = os.path.dirname(mzfile)
    
        if type(filename) == int:
            if type(mzfile) == tuple:  
                filetimestamp = mzfile[0][mzfile[0].find('h0')+ 2: mzfile[0].find('.nc')]
            if type(mzfile) == str:
                filetimestamp = mzfile[mzfile.find('h0')+ 2: mzfile.find('.nc')]
            filename = filtereddata.species + '_' + filtereddata.case + '.mzt.h0'+  filetimestamp + '_' + filtereddata.sitetype+'.nc'
        
        print('writing file: ' + outdir + '/'+ filename)
        
        #Write NetCDF file
        ncF = netCDF4.Dataset(outdir + '/'+ filename, 'w')
        
        # Create the dimensions
        ncF.createDimension('time', len(filtereddata.time))
        ncF.createDimension('sitenames', len(filtereddata.site))
        ncF.createDimension('boxwidth', 3)
        
        # Make some global attributes
        ncF.mzfile = filtereddata.mzfile
        ncF.sitefile = filtereddata.sitefile
        ncF.case = filtereddata.case
        ncF.species = filtereddata.species
        ncF.sitetype = filtereddata.sitetype
        
        # Create the variables
        #ncsitenames = ncF.createVariable('sitename','s', ('sitenames',))
        ncsitenames = ncF.createVariable('sitename',type(filtereddata.sitenames[0]), ('sitenames',))        
        
        nctime = ncF.createVariable('time', 'i', ('time',))

        nclon = ncF.createVariable('lon', 'f', ('sitenames','boxwidth'))
        nclat = ncF.createVariable('lat', 'f', ('sitenames','boxwidth'))
        ncpress = ncF.createVariable('pressure', 'f', ('sitenames','time','boxwidth','boxwidth','boxwidth',))
        
        # Fill the variables
        ncsitenames[:] = filtereddata.sitenames        
                
        # times as seconds since 1/1/2009
        nctime[:] = [(t - dt.datetime(2009,1,1,0,0,0)).total_seconds() for t in filtereddata.time]     
    
   
        nclon[:] = filtereddata.model_lon
        nclat[:] = filtereddata.model_lat
        ncpress[:] = filtereddata.model_pressure
        
        for i in np.arange(len(filtereddata.concnames)):
            ncconc = ncF.createVariable(filtereddata.concnames[i], 'f', ('sitenames','time','boxwidth','boxwidth','boxwidth',))        
            ncconc[:] = filtereddata.conc[i,:,:,:,:,:]
            ncconc.units = filtereddata.concunits[i]
        
        
            ncemiss = ncF.createVariable(filtereddata.emisnames[i], 'f', ('sitenames','time','boxwidth','boxwidth'))        
            ncemiss[:] = filtereddata.emis[i,:]
            ncemiss.units = filtereddata.emissunits[i]

        # Give the variables some attributes        
        nclon.units = 'Degrees east'
        nclat.units = 'Degrees north'
        ncpress.units = filtereddata.pressureunits
        nctime.units = 'seconds since 2009-01-01 00:00:00'
        
        ncF.close()
        print("Written " + outdir + '/'+ filename)


# Class to write out the data from a stationary platform

# filtereddata: the output of data_match_column
# outdir: the directory you wish to write the file to. Defaults to the directory containing the original MOZART file.
# filename: name for output file defaults to "species"_"casename".mzt.h0."Timestamp"_"sitetype".nc

class write_ncdf_column(object):
    def __init__(self, filtereddata, outdir = 0, filename=0):
        
        import os
        
        
        
        if type(outdir) == int:
            outdir = os.path.dirname(filtereddata.mzfile)
    
        if type(filename) == int:
            if type(filtereddata.mzfile) == tuple:            
                filetimestamp = filtereddata.mzfile[0][filtereddata.mzfile[0].find('h0')+ 2: filtereddata.mzfile[0].find('.nc')]
            if type(filtereddata.mzfile) == str:
                filetimestamp = filtereddata.mzfile[filtereddata.mzfile.find('h0')+ 2: filtereddata.mzfile.find('.nc')]
            filename = filtereddata.species + '_' + filtereddata.case + '.mzt.h0'+  filetimestamp + '_' + filtereddata.sitetype+'.nc'

        print('writing file: ' + outdir + '/'+ filename)
        
        #Write NetCDF file
        ncF = netCDF4.Dataset(outdir + '/'+ filename, 'w')
        
        # Create the dimensions
        ncF.createDimension('time', len(filtereddata.model_time))
        ncF.createDimension('lev', np.shape(filtereddata.model_pressure)[2])
        ncF.createDimension('site', len(filtereddata.site))
        
        
        # Make some global attributes
        ncF.mzfile = filtereddata.mzfile
        ncF.sitefile = filtereddata.sitefile
        ncF.case = filtereddata.case
        ncF.species = filtereddata.species
        ncF.sitetype = filtereddata.sitetype
        
        # Create the variables 
        # time variable the same as the number of time points
        nctime = ncF.createVariable('time', 'i', ('time',))   
        
        # Lats and lons - one per site
        nclon = ncF.createVariable('lon', 'f', ('site',))
        nclat = ncF.createVariable('lat', 'f', ('site',))
        
        # Pressure and concs
        # Sites by time by lev
        ncpress = ncF.createVariable('pressure', 'f', ('site','time', 'lev',))
        
        for i in np.arange(len(filtereddata.concnames)):
            ncconc = ncF.createVariable(filtereddata.concnames[i], 'f', ('site','time', 'lev',))
            ncconc[:] = filtereddata.conc[i,:]    
            ncconc.units = filtereddata.concunits[i]
        
        # Fill the variables               
        # times as seconds since 1/1/2009
        nctime[:] = [(t - dt.datetime(2009,1,1,0,0,0)).total_seconds() for t in filtereddata.model_time]     
   
        nclon[:] = filtereddata.model_lon
        nclat[:] = filtereddata.model_lat
        ncpress[:,:] = filtereddata.model_pressure
        
        
        # Give the variables some attributes        
        nclon.units = 'Degrees east'
        nclat.units = 'Degrees north'
        nctime.units = 'seconds since 2009-01-01 00:00:00'
        ncpress.units = filtereddata.pressureunits

        
        ncF.close()
        print("Written " + outdir + '/'+ filename)


            
# ___________________________________________________________________________________________________________________
# CODE TO READ THE DIFFERENT DATA TYPES
# ___________________________________________________________________________________________________________________
# Class to read in the filtered output

# filename: files you'd like to read in. This overides setting the filepattern variable.
# filepattern: suffix on end of files that you'd like to read in
# species: speies of interest (set this if using filepattern)
class read_ncdf_fixed(object):
    def __init__(self, filenames = None, filepattern = '*_TT.nc',  species='CH4', directory = None):
        
        if filenames is None:
            import fnmatch
            import os
            
            if directory is None :
                directory = '/data/as13988/MOZART/'+species.upper()+'/output/FWDModelComparison_NewEDGAR/'
            
            filepattern = '*'+species.upper()+filepattern
            
            matches = []
            for root, dirnames, filenames in os.walk(directory):
                for filename in fnmatch.filter(filenames, filepattern):
                    matches.append(os.path.join(root, filename))   
                    
        filenames = matches
        # need to sort the files
        filenames.sort()
        
        if len(filenames) == 0 :
            print('There are no files matching the file pattern in the given directory')

        else:
            
            for j in np.arange(len(filenames)):
                
                print('Reading file : ' + str(filenames[j]))
                
                data=netCDF4.Dataset(filenames[j])
                
                lon = data.variables['lon'][:]
                lat = data.variables['lat'][:]
                
                #sitenames = data.variables['sitename'][:] 
                sitenames = data.variables['sitename'][:] 
                
                time_j = np.transpose(data.variables['time'][:])
                pressure_j = np.transpose(data.variables['pressure'][:])
                
                # Create the time variable
                dateunits = data.variables['time'].getncattr('units')
                sincedate = dateunits[dateunits.find('seconds since ') +14:-1] # seconds since 2014-01-01 00:00:00
                    
                dt_date_j = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in time_j]

                if 'h0' in filenames[j]:
                    conc_tag = '_VMR_avrg'
                
                if 'h1' in filenames[j]:        
                    conc_varname = '_13:30_LT'
                
                if 'h2' in filenames[j]:        
                    conc_varname = '_VMR_avrg'
        
                # Might be multiple tracers
                conc_varname = [i for i in list(data.variables.keys()) if conc_tag in i]      
                conc_j = []
                if j == 0: conc_units = []
                
                for i in conc_varname:        
                    conc_j.append(data.variables[i][:]) 
                    if j == 0: conc_units = data.variables[i].units
                    
                if 'h0' in filename:
                    # Might be multiple tracers
                    emis_varname = [i for i in list(data.variables.keys()) if '_SRF_EMIS_avrg' in i]      
                    
                    emis_j = []
                    if j==0 : emis_units = []
                    
                    
                    for i in emis_varname:        
                        emis_j.append(data.variables[i][:]) 
                        if j==0: emis_units = data.variables[i].units
                
                if j == 0:
                
                    conc = conc_j              
                    emis = emis_j
                    pressure =  pressure_j
                    dt_date = dt_date_j              
                    case = str(data.__getattribute__('case')).strip()
                    sitetype = str(data.__getattribute__('sitetype')).strip()
                    sitefile = str(data.__getattribute__('sitefile')).strip()
                    pressureunits = data.variables['pressure'].getncattr('units')
                else:
                    
                    conc = np.concatenate((conc, conc_j), axis=2)
                    emis = np.concatenate((emis, emis_j), axis=2)
                    pressure = np.concatenate((pressure, pressure_j), axis=3)                
                    dt_date = np.concatenate((dt_date, dt_date_j))
                
                data.close()
            
            
            self.time = dt_date
            self.emis = emis
            self.conc = conc
            self.pressure = pressure
            self.lon = lon
            self.lat = lat
            self.sitenames = sitenames
            self.filenames = filenames         
            self.species = species
            self.case = case
            self.sitetype = sitetype
            self.sitefile = sitefile
            
            self.concnames =conc_varname
            self.units = conc_units
            self.pressureunits = pressureunits
 

# Class to read in the filtered output for mobile platforms

# filename: files you'd like to read in this overides setting the filepattern variable
# filepattern: suffix on end of files that you'd like to read in
# species: speies of interest (set this if using filepattern)
class read_ncdf_mobile(object):
    def __init__(self,  filenames = None, species = 'CH4', filepattern = '*_mobile.nc',\
        directory = None):
        
        if filename is None:
            import fnmatch
            import os
            
            if directory is None:
                directory = '/data/as13988/MOZART/'+species+'/output/FWDModelComparison_NewEDGAR/'
            
            filepattern = '*'+species+filepattern
             
            
            matches = []
            for root, dirnames, filenames in os.walk(directory):
                for filename in fnmatch.filter(filenames, filepattern):
                    matches.append(os.path.join(root, filename))   
                    
            filenames = matches
            
        # need to sort the files
        filenames.sort()
        
        if len(filenames) == 0:        
            print("There are no files in the given directory matching the file pattern")
        
        else: 
            for j in np.arange(len(filenames)):
                
                print('Reading file : ' + str(filenames[j]))
                
                data=netCDF4.Dataset(filenames[j])
                            
                model_lon_j = data.variables['model_lon'][:]
                model_lat_j = data.variables['model_lat'][:]
                obs_lon_j = data.variables['obs_lon'][:]
                obs_lat_j = data.variables['obs_lat'][:]
               
                #sitenames = data.variables['sitename'][:] 
                sitenames_j = data.variables['sitename'][:] 
                
                model_time_j = np.transpose(data.variables['model_time'][:])
                obs_time_j = np.transpose(data.variables['obs_time'][:])

                model_conc_j = np.transpose(data.variables['model_conc'][:])
                obs_conc_j = np.transpose(data.variables['obs_conc'][:])

                model_pressure_j = np.transpose(data.variables['model_pressure'][:])
                obs_pressure_j = np.transpose(data.variables['obs_pressure'][:])
                
                # Create the time variable
                dateunits = data.variables['model_time'].getncattr('units')
                sincedate = dateunits[dateunits.find('seconds since ') +14:-1] # seconds since 2014-01-01 00:00:00
                    
                model_dt_date_j = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in model_time_j]
                obs_dt_date_j = [ dt.datetime.strptime(sincedate, "%Y-%m-%d %H:%M:%S") + dt.timedelta(seconds=(i).astype('int')) for i in obs_time_j]
               
                
                if j == 0:
    
                    sitenames = sitenames_j            
                
                    model_conc = model_conc_j      
                    obs_conc = obs_conc_j                    

                    model_pressure =  model_pressure_j
                    obs_pressure =  obs_pressure_j
                    
                    model_dt_date = model_dt_date_j         
                    obs_dt_date = obs_dt_date_j         
                    
                    model_lat = model_lat_j
                    model_lon = model_lon_j
                    obs_lat = obs_lat_j
                    obs_lon = obs_lon_j
                    
    
                else:
                    
                    sitenames = np.concatenate((sitenames, sitenames_j))               
                    
                    model_conc = np.concatenate((model_conc, model_conc_j))
                    obs_conc = np.concatenate((obs_conc, obs_conc_j))

                    model_pressure = np.concatenate((model_pressure, model_pressure_j))    
                    obs_pressure = np.concatenate((obs_pressure, obs_pressure_j)) 
                    
                    model_dt_date = np.concatenate((model_dt_date, model_dt_date_j))
                    obs_dt_date = np.concatenate((obs_dt_date, obs_dt_date_j))
                    
                    model_lat = np.concatenate((model_lat, model_lat_j))
                    model_lon = np.concatenate((model_lon, model_lon_j))
                    obs_lat = np.concatenate((obs_lat, obs_lat_j))
                    obs_lon = np.concatenate((obs_lon, obs_lon_j))
    
                    
                    
            self.model_time = model_dt_date
            self.obs_time = obs_dt_date
            self.model_conc = model_conc
            self.obs_conc = obs_conc
            self.model_pressure = model_pressure
            self.obs_pressure = obs_pressure
            self.model_lon = model_lon
            self.model_lat = model_lat
            self.obs_lon = obs_lon
            self.obs_lat = obs_lat
            self.sitenames = sitenames
            self.filenames = filenames         
            self.species = str(data.__getattribute__('species')).strip()
            self.case = str(data.__getattribute__('case')).strip()
            self.sitetype = str(data.__getattribute__('sitetype')).strip()
            self.sitefile = str(data.__getattribute__('sitefile')).strip()
            
            self.concunits = data.variables['model_conc'].getncattr('units')
            self.pressureunits = data.variables['model_pressure'].getncattr('units')
       
# ___________________________________________________________________________________________________________________
# CODE TO PLOT THE DIFFERENT DATA TYPES
# ___________________________________________________________________________________________________________________

# Class to plot the filtered output
# Plots the output of read_ncdf_fixed against the obs at the given site

# data: output of read_necdf_fixed
# sitename: 3 letter acronym of the site of interest
# scaling: a scaling factoras the MOZART output is in mol/mol not ppm or ppb
# x_range: set a fixed range for the x axis 
# save_plot: set if you'd like to save the plot. Saves the pot to a new subdirectory 'plots' in the same location as the data file
# network: set the network of the obs you wish to compare to
# height: set the height of the intake you wish to plot
# speciesname: set if you wish to plot of a single species only. Otherwise default to plotting all species given in the file.
# diff: set to plot the difference between the MOZART output and the observations

class plot_ncdf_fixed(object):
    def __init__(self, data, sitename = 'mhd', scaling = 1e06, x_range = None, save_plot = 0, network = None, height = None, speciesname = None, diff=None):
        
        import matplotlib.ticker as ticker
        import matplotlib.pyplot as plt
        import acrg_plottools as plottools
        
        # Extract the model data for the given site
        sites = data.sitenames
        matched = np.where(sites == sitename)[0]
          
        print(matched)
          
        if len(matched) > 1:
            # This means that the site was listed twice in the site file as two measurement networks share it.
            # As we're pulling out model data at the same location it doesn't matter which version we use
            # Default to using the first one
            matched = [matched[0]]
            
        
        if len(matched) == 0:
            print('There is no sitename matching : ' + sitename)
            print('Check the sitename or try using lowercase')
        else: 
            time = data.time
            # conc is lon x lat x lev x time x site
            #conc = np.squeeze(data.conc[:,:,:,:,matched])
            pressure = np.squeeze(data.pressure[:,:,:,:,matched])
            
            # Plot for the given species only at multiple gridboxes
            if speciesname != None:
                species_no = (np.where(speciesname in data.concnames))[0]
                # conc is species x site x time x lev x lon x lat
                conc = np.squeeze(data.conc[species_no,matched,:,:,:])
                reshapedconc = np.reshape(conc,(np.shape(conc)[0],27))
                reshapedpressure = np.reshape(pressure, (27,np.shape(pressure)[-1]))
                
                n_colours = 27
                
            # PLot all the species/tracers at the central point only
            else:
                # conc is species x site x time x lev x lon x lat
                conc = np.squeeze(data.conc[:,matched,:,1,1,1])
                reshapedconc = np.transpose(conc)
                reshapedpressure = np.squeeze(pressure[1,1,1,:])

                n_colours = len(data.concnames)
            
            
             
            # Indicies for lats, lons and levs
            lat_i = [1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3]
            lon_i = [1,1,1,2,2,2,3,3,3,1,1,1,2,2,2,3,3,3,1,1,1,2,2,2,3,3,3]
            lev_i = [1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3]  
            
                    
            
            colours = plottools.generatecolours(n_colours).RGB
            
            # Plot model ooutput for fixed site data
            fig = plt.figure()
            fig.subplots_adjust(right = 0.8)
            
            legend_spacing = np.arange(n_colours)   
            
                        
            
            for i in np.arange(n_colours):      
                
                conc_i = reshapedconc[:,i]        
                yaxislabel = data.species + '(' + data.units + '*' + str(scaling) + ')'
               
                if diff is not None:
                    conc_i = conc_i - reshapedconc[:,diff]
                    yaxislabel = data.species + '- '+data.concnames[diff] + ' (' + data.units + '*' + str(scaling) + ')'
                    
                # Plot the data
                plt1 = plt.subplot()
                
                plt1.plot(time, conc_i*scaling, "-", color = colours[i], markersize = 3)
                    
                y_formatter = ticker.ScalarFormatter(useOffset=False)
                plt1.yaxis.set_major_formatter(y_formatter)
                
                x_tickno_formatter = ticker.MaxNLocator(5)
                plt1.xaxis.set_major_locator(x_tickno_formatter)
                
                plt1.set_title('Model output at '+ sitename)
                plt1.set_ylabel(yaxislabel)
                plt1.set_xlabel('Time')
    
                if speciesname != None: legend_i = str(data.lat[matched, lat_i[i]-1][0]) + ', ' +str(data.lon[matched,lon_i[i]-1][0]) + ', ' + str(lev_i[i]-1)
                if speciesname is None: legend_i = data.concnames[i]
                    
                plt.figtext(0.82, 0.85-(0.03*legend_spacing[i]), legend_i, verticalalignment='bottom', \
                horizontalalignment='left', color=colours[i], fontsize=8)
                    
    
            if speciesname != None: 
                plt1.plot(time, reshapedconc[:,13]*scaling, "--", color = 'black', markersize = 3)
                plt.figtext(0.82, 0.88, 'Lat, Lon, Lev', verticalalignment='bottom', horizontalalignment='left', color='black', fontsize=8)
                plt.figtext(0.6, 0.2, 'Central point ---', verticalalignment='bottom', horizontalalignment='left', color='black', fontsize=8)
              
            
            
            if x_range != None:
                plt1.set_xlim(x_range)            
            
            if save_plot != 0:
                outdir = os.path.dirname(os.path.dirname(data.filenames[0]))
                fig.savefig(outdir + '/plots/' + data.species+ '_'+ sitename+ '_Model.png', dpi=100)
                print('Figure saved as : ' + outdir + '/plots/' + data.species+ '_'+ sitename+ '_Model.png')
            
            
            plt.show()
        
            plt.close()
            
            if speciesname != None:
                 # Plot model output and obs    
                # Read in the obs
                import acrg_agage
                import json
                
                print('Plotting site ' + sitename)
                print('Plotting data from /dagage2/agage/metoffice/processed_obs/')
                
                # check if there is UKMO data for that site
                acrg_path=os.path.split(os.path.realpath(__file__))
    
                with open(acrg_path[0] + "/acrg_site_info.json") as f:
                    site_info=json.load(f)
                
                site = acrg_agage.synonyms(sitename, site_info)
                
                if site is None:
                    print("Site " + sitename + ' is not listed')
                
                else:
                    
                    obs = acrg_agage.get(sitename, data.species, network = network, height = height)         
                    
                                   
                    
                    # Only plot model output for the same time range as the obs
                    #start = bisect.bisect_left(time, min(obs_time)) -1
                    #finish = bisect.bisect_right(time, max(obs_time))
                    
                    model_time = time
                    model_conc = reshapedconc[:,13]
                    
                    fig = plt.figure()
                     
                    # Plot the data
                    plt1 = plt.subplot()
                    
                    plt1.plot(obs.index, obs['mf'], "r-", markersize = 3, markeredgecolor = 'red')
                    plt1.plot(model_time, model_conc*scaling, "b-", markersize = 3, markeredgecolor = 'blue')
                     
                    y_formatter = ticker.ScalarFormatter(useOffset=False)
                    plt1.yaxis.set_major_formatter(y_formatter)
                    
                    x_tickno_formatter = ticker.MaxNLocator(5)
                    plt1.xaxis.set_major_locator(x_tickno_formatter)
                    
                    plt1.set_title('Model output and observations at '+ sitename )
                    plt1.set_ylabel(data.species + '(' + data.units + '*' + str(scaling) + ')')
                    plt1.set_xlabel('Time')
        
                    if x_range != None:
                        plt1.set_xlim(x_range)
                        
                    if save_plot != 0:
                        outdir = os.path.dirname(os.path.dirname(data.filenames[0]))
                        fig.savefig(outdir + '/plots/' + data.species+ '_UKMO_'+ sitename+ '.png', dpi=100)
                        print('Figure saved as : ' + outdir + '/plots/' + data.species+ '_UKMO_'+ sitename+ '.png')
                    
                    
                    plt.show()
                    
                
                    plt.close()
                 
                                         
        
        
        
# Class to plot the filtered output
# Plots the output of read_ncdf_mobile
# defaults to not plotting the obs concentrations as we only have these for CH4 at the moment

# data: output of read_necdf_fixed
# sitename: 3 letter acronym of the site of interest
# scaling: a scaling factoras the MOZART output is in mol/mol not ppm or ppb
# save_plot: set if you'd like to save the plot. Saves the pot to a new subdirectory 'plots' in the same location as the data file
# no_obs: set if you don't want to plot the observations

class plot_ncdf_mobile(object):
    def __init__(self, data, sitename = 'ferry', save_plot = 0, scaling = 1e06, no_obs=1):
        
        import matplotlib.ticker as ticker
        import matplotlib.pyplot as plt
        
        # Extract the data for the given site
        sites = data.sitenames
        matched = np.where(sites == sitename)[0]
        
        if len(matched) == 0 :        
            print('There are no sitenames matching ' + str(sitename))
            
        else:
            # conc is of dimension time 
            # sitenames are also of dimension time        
        
            time = np.squeeze(data.obs_time[matched])
            
            model_conc = np.squeeze(data.model_conc[matched])
            obs_conc = np.squeeze(data.obs_conc[matched])
                
            
            model_pressure = np.squeeze(data.model_pressure[matched])
            obs_pressure = np.squeeze(data.obs_pressure[matched])
            
            model_lat = np.squeeze(data.model_lat[matched])
            obs_lat = np.squeeze(data.obs_lat[matched])
            
            model_lon = np.squeeze(data.model_lon[matched])
            obs_lon = np.squeeze(data.obs_lon[matched])
            
            model_GT180 = np.where(model_lon > 180)[0]
            obs_GT180 = np.where(obs_lon > 180)[0]
            
                   
            
            if len(model_GT180) != 0:
                model_lon[model_GT180] = model_lon[model_GT180] - 360
            
            if len(obs_GT180) != 0:
                obs_lon[obs_GT180] = obs_lon[obs_GT180] - 360


            # Plot of 
            fig = plt.figure()
            
            # Plot the data
            plt1 = plt.subplot(6,1,1)
                        
            plt1.plot(time, model_conc*scaling, "bo-",  markersize = 3)
            
            if no_obs !=0:
                plt1.plot(time, obs_conc, "ro-",  markersize = 3)
                
            # plot the model and the obs time/space matched output
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt1.yaxis.set_major_formatter(y_formatter)
             
            plt1.set_title(data.species + 'model output (blue) and obs (red) for '+ sitename)
            plt1.set_ylabel(data.species + '(' + data.concunits + '*' + str(scaling) + ')')

            
            # plot the difference between the model and the obs
            plt5 = plt.subplot(6,1,2)
                        
            plt5.plot(time, model_conc*scaling - obs_conc, "go-", markersize = 3)
            
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt5.yaxis.set_major_formatter(y_formatter)
             
            plt5.set_ylabel('Conc diff')
            
            
            # plot the model and obs pressures
            plt2 = plt.subplot(6,1,3)
                        
            plt2.plot(time, model_pressure, "bo-", markersize = 3)
            plt2.plot(time, obs_pressure, "ro-", markersize = 3)
                
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt2.yaxis.set_major_formatter(y_formatter)
             
            plt2.set_ylabel('Pressure (Pa)')


            # plot the model and obs pressure difference
            plt6 = plt.subplot(6,1,4)
                        
            plt6.plot(time, model_pressure- obs_pressure, "go-", markersize = 3)
                
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt6.yaxis.set_major_formatter(y_formatter)
             
            plt6.set_ylabel('Pressure diff (Pa)')
            
            
            # plot the model and obs lats
            plt3 = plt.subplot(6,1,5)
                        
            plt3.plot(time, model_lat, "bo-", markersize = 3)
            plt3.plot(time, obs_lat, "ro-", markersize = 3)
                
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt3.yaxis.set_major_formatter(y_formatter)
             
            plt3.set_ylabel('lat')


            # plot the model and obs lons
            plt4 = plt.subplot(6,1,6)
                        
            plt4.plot(time, model_lon, "bo-", markersize = 3)
            plt4.plot(time, obs_lon, "ro-", markersize = 3)
                
            y_formatter = ticker.ScalarFormatter(useOffset=False)
            plt4.yaxis.set_major_formatter(y_formatter)
             
            plt4.set_ylabel('lon')

            fig.set_size_inches(6,8)

            if save_plot != 0:
                outdir = os.path.dirname(os.path.dirname(data.filenames[0]))
                fig.savefig(outdir + '/plots/' + data.species+ '_'+ sitename+ '.png', dpi=100)
                print('Figure saved as : ' + outdir + '/plots/' + data.species+ '_'+ sitename+ '.png')
            
            
            plt.show()      



# Code to set up input for contour plotting
class plot_map_setup(object):
    def __init__(self, data, lat, lon, 
                 lon_range = None, lat_range = None):

        if lon_range is None:
            lon_range = (min(lon), max(lon))
        if lat_range is None:
            lat_range = (min(lat), max(lat))
        
        m = Basemap(projection='gall',
            llcrnrlat=lat_range[0], urcrnrlat=lat_range[1],
            llcrnrlon=lon_range[0], urcrnrlon=lon_range[1],
            resolution='l')

        lons, lats = np.meshgrid(lon, lat)
        x, y = m(lons, lats)
        
        self.x = x
        self.y = y
        self.m = m

# data: output of read
# lat: 1D array of latitudes (optinal)
# lon: 1D array of longitudes (optinal)
# time: 1D array of time values (optinal)
# timestep: which timestep you want to plot e.g. set to 3 to plot the third timestep either a pandas time variable or a string '%d/%m/%y
# out_filename: name of output file defaults to 'MZT_' + species + '_L'+str(level)+ '_'+time.strftime('%y%m%d_%H%M')+'.png' (optinal)
# range_all: base the range of the contour colours on all the data rather than just the data for that timestep (optinal)
# lon_range : set lon range (optinal)
# lat_range: set lat_range (optinal)
# species: set to species or defaults to data.species (optinal)
# scale: set optional scaling factor (optinal)
# rangescale: scaling factor for range (optinal)
# colourbar_label: label for colourbar  defaults to  species + ' [' + units + ']' (optinal)
# savefig: set if you want to save the figure(optinal)
# map_data: precalculated output of acrg_plottools.plot_map_setup instead of calculating it each time(optinal)
# nlevels: set to the number of levels you want to use in the contours defaults to 10 (optinal)
# levels: imput specific contour levels to use (optinal)
# minconc: minimum concentration used to calculate the levels (optinal)
# maxconc: maximim concentration used to calculate the levels (optinal)
# title: plot title
# outdir: where the plots are saved    
# Plot a filled contour map of a given MZT output
# Defaults to plotting the first timestep at ground level
def plotlevel_MZT(data, lat = None, lon = None, time = None, level = -1, timestep = 0, out_filename=None, range_all = None,
         lon_range=None, lat_range=None, species = None, species_choice = 0, scale = None, rangescale = 100, colourbar_label = None, savefig =None,
         map_data = None, nlevels = 10, levels = None, minconc = None, maxconc = None, title = None, outdir = '/home/as16992/MOZART/plots/'):

    if map_data is None:

        if lat == None:
            lat = data.lat
        
        if lon == None:
            lon = data.lon

        map_data = plot_map_setup(data, lat, lon, 
                                  lon_range = lon_range,
                                  lat_range = lat_range)
    
    fig = plt.figure(figsize=(8,8))
    fig.add_axes([0.1,0.1,0.8,0.8])

    map_data.m.drawcoastlines()
#    map_data.m.drawstates()
#    map_data.m.drawcountries()
#    map_data.m.shadedrelief()
    
    if species == None:           
        species = data.species
    
    species_options = np.array(['CO2', 'CH4', 'N2O', 'C2H6','Error', 'Flux']) 
    scale_options = [1e6, 1e9, 1e9, 1e9, 1, 1]
    unit_options = ['ppm', 'ppb', 'ppb', 'ppb', '%', '']    
    
    index = np.where(np.array(species_options) == species)[0][0]
    if scale == None:
        scale = scale_options[index]
    units = unit_options[index]    
    
    if level < 0 :
        level = np.arange(56)[level]
    
    # make range for conc contours
    # Rounds to the nearest 100
    if isinstance(data, np.ndarray):
        conc = data[timestep, :,:]
    else:
        conc = data.conc[species_choice]
        conc = conc[timestep,level,:,:]
        
    conc = np.squeeze(conc)*scale
    
    if np.shape(conc) != np.shape(map_data.x):
        conc = np.transpose(conc)
    
    
    #pdb.set_trace()
    
    if minconc == None:
        if range_all == None:
            minconc = np.floor(old_div(np.nanmin(conc),rangescale))*rangescale
        else:
            minconc = np.floor(old_div(np.nanmin(data),rangescale))*rangescale
            
    if maxconc == None:
        if range_all == None:
            maxconc = np.ceil(old_div(np.nanmax(conc),rangescale))*rangescale
        else:
            maxconc = np.ceil(old_div(np.nanmax(data),rangescale))*rangescale
    
    
    step = old_div((maxconc - minconc),nlevels)
    
    if levels == None:
        levels = np.arange(minconc, maxconc+step, step)
   

    #Plot map
    #cs = map_data.m.contourf(map_data.x, map_data.y, conc, levels, cmap = plt.cm.Spectral_r    
    cs = map_data.m.contourf(map_data.x, map_data.y, conc, levels, cmap = plt.cm.RdYlBu)

    """     
    # Alter this at some point to plot the tall tower sites ?
                       
    #Plot release location
    if "release_lat" in dir(fp_data):
        rplons, rplats = np.meshgrid(fp_data.release_lon[time_index],
                                     fp_data.release_lat[time_index])
        rpx, rpy = map_data.m(rplons, rplats)
        rp = map_data.m.scatter(rpx, rpy, 100, color = 'black')
        
    """
    if time == None:    
        time = data.time
        
    time = time[timestep]
    
    if isinstance(time, pd.tslib.Timestamp):
       time = (time).strftime('%d/%m/%y')
       
    # Determine the average pressure at that level in kPa
    if isinstance(data, np.ndarray):
        P = 'Ground'
    else:        
        P = np.round(np.mean(np.squeeze(data.pressure[timestep, level, :,:]))/1000.0)
    
    if title == None:
        title = 'MOZART output P = ' + str(P) + 'kPa at ' + str(time)
    
    
    plt.title(title, fontsize=16)

    cb = map_data.m.colorbar(cs, location='bottom', pad="5%")
    
    tick_locator = ticker.MaxNLocator(nbins=7)
    cb.locator = tick_locator
    cb.update_ticks()
 
    if colourbar_label == None:
        colourbar_label = species + ' [' + units + ']' 
 
    cb.set_label(colourbar_label, 
                 fontsize=12)
    cb.ax.tick_params(labelsize=13) 
    
    if out_filename == None:
        out_filename = 'MZT_' + species + '_L'+str(level)+ '_'+time.strftime('%y%m%d_%H%M')+'.png'
        
    if savefig is not None:
        plt.savefig(outdir + out_filename)
        plt.show()
        plt.close()
    else:        
        plt.show()
        
    return map_data, conc, levels
    
# Plot multiple profile plots for a given MZT output file at a given lon against lat and then at a given lat against lon
# Defaults to plotting the first timestep at lat = 0.94 and lon = 0

# data: output of read
# timestep: the number of the timestep you want to plot
# latindex: the index of the latitude you want to plot. Defaults to 48 = 0.947 degrees North
# lonindex: the index of the longitude you want to plot. Defaults to 0 = 0 degrees
# out_filename: outfile name
# outdir: where to save output file
def plotprofiles_MZT(data, timestep = 0, latindex = 48, lonindex = 0, out_filename=None, outdir='/home/as13988/Plots/'):

    species = data.species
    
    species_options = ['CO2', 'CH4', 'N2O']    
    scale_options = [1e6, 1e9, 1e9]
    unit_options = ['ppm', 'ppb', 'ppb']    
    
    index = np.where(np.array(species_options) == species)[0]
    scale = scale_options[index]
    units = unit_options[index]    


    # extract the conc at the given timestep for all levels and lons
    # extract the corresponding pressures
    conc_lons = np.squeeze(data.conc[timestep, :, latindex,:])*scale
    conc_lats = np.squeeze(data.conc[timestep, :, :,lonindex])*scale
    p_lons = old_div(np.squeeze(data.pressure[timestep, :, latindex,:]),1000)
    p_lats = old_div(np.squeeze(data.pressure[timestep, :, :,lonindex]),1000)
    lon_lons, b = np.meshgrid(data.lon, np.arange(56))
    lat_lats, b = np.meshgrid(data.lat, np.arange(56))
    
    
    fig = plt.figure(figsize=(8,8))
    ax = fig.gca(projection='3d')
    
    
    for i in np.arange(old_div(len(data.lon),3))*3:
        y = conc_lons[:,i]
        z = p_lons[:,i]
        x = lon_lons[:,i]
        
        ax.plot(x, y, z)
   
    ax.invert_zaxis()
    ax.azim = -20
    ax.elev = 10
    #ax.set_ylim3d(1800,2100)
    ax.set_xlabel('lon')
    ax.set_ylabel(species + ' [' + units + ']')   
    ax.set_zlabel('Pressure (kPa)')
    ax.set_title('MOZART output Lat = ' + str(np.round(data.lat[latindex])) + ' at ' + str(data.time[timestep]), fontsize=16)

    plt.show()
    
    if out_filename is not None:
        out_filename = 'MZT_' + species + '_Lat'+str(np.round(data.lat[latindex]))+ '_'+data.time[timestep].strftime('%y%m%d_%H%M')+'.png'
        fig.savefig(outdir + out_filename)
    
    plt.close()


    fig = plt.figure(figsize=(8,8))
    ax = fig.gca(projection='3d')
    
    for i in np.arange(len(data.lat)):
        y = conc_lats[:,i]
        z = p_lats[:,i]
        x = lat_lats[:,i]
        
        ax.plot(x, y, z)
   
    ax.invert_zaxis()
    ax.azim = -20
    ax.elev = 10
    ax.set_xlabel('lat')
    ax.set_ylabel(species + ' [' + units + ']')   
    ax.set_zlabel('Pressure (kPa)')
    ax.set_title('MOZART output Lon = ' + str(np.round(data.lon[lonindex])) + ' at ' + str(data.time[timestep]), fontsize=16)
    
    #ax.set_ylim3d(1800,2100)
    
    plt.show()
    
    if out_filename is not None:
        out_filename = 'MZT_' + species + '_Lon'+ str(np.round(data.lon[lonindex]))+ '_'+data.time[timestep].strftime('%y%m%d_%H%M')+'.png'
        fig.savefig(outdir + out_filename)
    
    plt.close()