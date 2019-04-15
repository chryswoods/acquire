#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 14:59:47 2018

This module is for creating country mask xarray.Dataset objects and netCDF files for new domains 
(or re-creating previous domains).

This is based on the regionmask module. This uses the Natural Earth database with a scale of 1:50m.

Output file name is of the form: "country_DOMAIN.nc" e.g. country_SOUTHAMERICA.nc

The domain can be extracted from current footprint files or latitude and longitude arrays can be specified.
Any country mask files already present within the output directory WILL NOT be overwritten. Rename or move 
the previous file if you wish to create a new file using this method.

Function to use for creating the country file is:
 - create_country_mask(...)

@author: rt17603
"""
from __future__ import print_function

from builtins import zip
from builtins import range
import regionmask
import iso3166
import numpy as np
import xarray as xray
from collections import OrderedDict
import glob
import getpass
import os
import pdb

data_path = os.getenv("DATA_PATH")
fp_directory = os.path.join(data_path,'NAME/fp/')
country_directory = os.path.join(data_path,'NAME/countries/')

def domain_volume(domain,fp_directory=fp_directory):
    '''
    The domain_volume function extracts the volume (lat, lon, height) within a domain from a related footprint file.
    
    Args:
        domain (str) : 
            Domain of interest (e.g. one of 'AUSTRALIA', 'CARIBBEAN','EASTASIA','EUROPE','NAMERICA','PACIFIC',
            'SOUTHAFRICA','SOUTHASIA','WESTUSA')
        fp_directory (str, optional) : 
            fp_directory can be specified if files are not in the default directory. 
            Must point to a directory which contains subfolders organized by domain.
        
    Returns:
        xarray.DataArray (3): 
            Latitude, longitude, height
    '''
    directory = os.path.join(fp_directory,domain)
    listoffiles = glob.glob(os.path.join(directory,"*"))
    if listoffiles:
        filename = listoffiles[0]
        print('Using footprint file: {0} to extract domain'.format(filename))
        with xray.open_dataset(filename) as temp:
            fields_ds = temp.load()
        
        fp_lat = fields_ds["lat"].values
        fp_lon = fields_ds["lon"].values
        fp_height = fields_ds["height"].values
    
        return fp_lat,fp_lon,fp_height     
    else:
        raise Exception('Cannot extract volume for domain: {1}. No footprint file found within {0}'.format(directory,domain))
        #return None

def range_from_bounds(bounds,step,include_upper=False):
    '''
    Create an array covering a range from a set of bounds. Choose whether to include upper
    bound or not.
    
    Args:
        bounds (list) :
            Two item list containing the upper and lower bounds of the range
        step (int/float) :
            Step size for the range
        include_upper (bool, optional) :
            Whether to include the upper bound.
            Default = False
    Returns:
        np.array:
            Array created using np.arange of range between lower and upper bounds.
    '''
    if include_upper:
        return np.arange(bounds[0],bounds[1]+step,step)
    else:
        return np.arange(bounds[0],bounds[1],step)

def country_name(code,allow_non_standard=True,supress_print=False):
    '''
    Extract country name based on ISO3166 standard.
    Note: allows non-standard values based on Natural Earth and Marine Regions databases to be included if 
    allow_non_standard is set to True.
    
    Args:
        code (str) :
            Can accept alpha2, alpha3 or numeric code to extract the country name.
        allow_non_standard (bool, optional) :
            Allow additional search for non-standard country names based on extra values 
            specifically from the Natural Earth and Marine Regions databases.
            Default = True.
        supress_print (bool, optional) :
            Whether to supress printing of a warning message when unable to find a match.
            Default = False.
    Returns:
        str:
            Country name (based on ISO3166 standard)
    '''
    non_standards_ne = {"DRC":u"Democratic Republic of the Congo",
                     "Dem. Rep. Congo":u"Democratic Republic of the Congo",
                     "SW":u"Swaziland","eSwatini":u"Swaziland",
                     "FL":u"Liechtenstein","Liechtenstein":u"Liechtenstein",
                     "KO":u"Kosovo","Kosovo":u"Kosovo"}
    non_standards_mr = {"Ascension":u"Saint Helena, Ascension and Tristan da Cunha",
                        "ASC":u"Saint Helena, Ascension and Tristan da Cunha",
                        "Tristan da Cunha":u"Saint Helena, Ascension and Tristan da Cunha",
                        "TAA":u"Saint Helena, Ascension and Tristan da Cunha",
                        "Clipperton Island":u"France","CPT":u"France"}
    
    non_standards = non_standards_ne
    non_standards.update(non_standards_mr)
    
    try:
        return iso3166.countries.get(code).name
    except KeyError:
        try:
            if not supress_print:
                print("Unable to derive country name from input: {}".format(code))
                print("WARNING: Looking through non-standard list")        
            return non_standards[code]
        except KeyError:
            if not supress_print:
                print("Unable to derive country name from non-standard list".format(code))
            return None

def country_alpha2(code,allow_non_standard=True,supress_print=False):
    '''
    Extract country two-letter code based on ISO3166 standard.
    Note: allows non-standard values based on Natural Earth and Marine Regions databases
    to be included if allow_non_standard is set to True.
    
    Args:
        code (str) :
            Can accept alpha3, numeric code or country name.
        allow_non_standard (bool, optional) :
            Allow additional search for non-standard country names based on extra values 
            specifically from the Natural Earth and Marine Regions databases.
            Default = True.
        supress_print (bool, optional) :
            Whether to supress printing of a warning message when unable to find a match.
            Default = False.
    Returns:
        str:
            Two-letter country code (based on ISO3166 standard)
    '''
    non_standards_ne = {"DRC":u"CD","Dem. Rep. Congo":u"CD","SW":u"SZ","eSwatini":u"SZ",
                     "FL":u"LI","Liechtenstein":u"LI"}
    non_standards_mr = {"Ascension":u"SH","ASC":u"SH","Tristan da Cunha":u"SH","TAA":u"SH",
                        "Clipperton Island":u"FR","CPT":u"FR"}
   
    # ASC - Ascension Islands - SH designates Saint Helena, Ascension and Tristan da Cunha (British Overseas Territory)
    # TAA - Tristan de Cunha - SH designates Saint Helena, Ascension and Tristan da Cunha (British Overseas Territory)
    # CPT - Clipperton Island - Uninhabited island in Eastern Pacific, oversees minor territory of France, included within FR country code.
    
    non_standards = non_standards_ne
    non_standards.update(non_standards_mr)
    
    try:
        return iso3166.countries.get(code).alpha2
    except KeyError:
        if allow_non_standard:
            try:
                if not supress_print:
                    print("Unable to derive country alpha2 code from input: {}".format(code))
                    print("WARNING: Having to look through non-standards")
                return non_standards[code]
                
            except KeyError:
                if not supress_print:
                    print("Unable to derive country alpha2 code from non-standard list")
                return None
        else:
            if not supress_print:
                print("Unable to derive country alpha2 code from input: {}".format(code))
            return None

def accepted_extra_countries(code):
    '''
    Additional country names with no equivalent within the ISO3166 standard but included (at the moment)
    within the Natural Earth database.
    
    e.g. Vatican, N. Cyprus, Kosovo, Somaliland
    
    Args:
        code (str) :
            Country name to check against list of additional accepted country names.
    
    Returns:
        str/None:
            returns the country name if it matches the list, None otherwise.
    '''
    accepted = [u"Somaliland",u"Vatican",u"N. Cyprus",u"Kosovo"]
    
    if code in accepted:
        return code
    else:
        return None

def manage_country_descriptor(countries):
    '''
    Manages the country names containing a comma and assumes the string after the comma contains the
    descriptor of the country e.g. "Republic Of". In most cases it is assumed that this detail is not 
    needed in the final country name. Exceptions are detailed below.
    
    Rules for commas are as follows:
     - If the country requires the designation after a comma the name will be rearranged. At the moment,
     this includes "congo" and "korea".
     e.g. "Korea, Republic of" becomes "Republic of Korea"
     e.g. "Korea, Democratic People's Republic of" becomes "Democratic People's Republic of Korea"
     - Otherwise, any designation specified after a comma will be removed.
     e.g. "Venezuela, Bolivarian Republic of" becomes "Venezuela"
    
    WARNING: Changes countries list in place
    
    Args:
        countries (list) :
            List of country names to manage.
    
    Returns:
        list:
            Country names altered as described above where appropriate.
    '''
    descriptor_needed = ["congo","korea"]
    for i,name in enumerate(countries):
        if name.find(',') != -1:
            name_split = name.split(',')
            if len(name_split) == 2:
                country,descriptor = name_split
                if country.lower() in descriptor_needed:
                    countries[i] = descriptor.lstrip() + ' ' + country.rstrip()
                else:
                    countries[i] = country.rstrip()

    return countries
    

def region_mapping(upper=True):
    '''
    Extract mapping from the region number to the country name from the regionmask module.
    
    See manage_country_descriptor() function for how names containing commas are treated.
    
    Args:
        upper (bool, optional):
            Return country names all in upper case. Default = True.
    
    Returns:
        dict:
            Dictionary containing the mapping of the region number to the country name.
    '''
    all_regions = regionmask.defined_regions.natural_earth.countries_50.region_ids
    #codes = [key for key in all_regions.keys() if isinstance(key,unicode) and len(key) == 2]
    #names = [country_name(code,supress_print=True) for code in codes]
    
    #names = [name.split(',')[0] if name else name for name in names]
    
    names = regionmask.defined_regions.natural_earth.countries_50.names
    numbers = [all_regions[key] for key in names]

    # Check all numbers are covered
    max_num = np.max(numbers)
    for i in range(max_num+1):
        if i not in numbers:
            #for key,item in list(all_regions.items()):
            for key,item in all_regions.items():
                if item == i:
                    if isinstance(key,str) and len(key) > 1:
                        name = country_name(key,supress_print=True)
                        if name:
                            numbers.append(i)
                            names.append(name)
                            break
                        else:
                            if accepted_extra_countries(key):
                                numbers.append(i)
                                names.append(key)
                                break
    
    names = manage_country_descriptor(names)
    if upper:
        names = np.core.defchararray.upper(names)
    #region_dict = {num:name for num,name in list(zip(numbers,names))}
    region_dict = {num:name for num,name in zip(numbers,names)}

    return region_dict

def create_country_mask(domain,lat=None,lon=None,reset_index=True,ocean_label=True,write=True,
                        output_dir=country_directory):
    '''
    Creates a country mask for the latitude and longitude range. Derives country data from
    Natural Earth database (at 1:50m resolution).
    
    If write=True, writes out file of the form "country_DOMAIN.nc" e.g. country_SOUTHAMERICA.nc
    Note: Will not overwrite a pre-existing file.
    
    Args:
        domain (str) :
            Domain associated with lat and lon grid.
            If lat and lon arrays are not specified, domain will be used to extract latitude and
            longitude grids.
        lat (np.array, optional) :
            Latitude grid values.
            If not specified, will attempt to extract latitude values from domain footprint file.
        lon (np.array, optional) :
            Longitude grid values.
            If not specified, will attempt to extract longitdue values from domain footprint file.
        reset_index (bool, optional) :
            Reset index values within grid to 0 - num regions rather than retain their
            original values within the Natural Earth input (regionmask input).
            May be useful to not reset the index when needing to compare to other inputs.
            Should be set to True when writing to file to match with other ACRG code for looking at 
            country totals.
            Default = True.
        ocean_label (bool, optional) :
            Add additional explicit ocean label as well as countries within domain.
            Default = True.
        write (bool, optional) :
            Write produced dataset to file of the form "country_"DOMAIN".nc".
            Default = True.
        output_dir (str, optional) :
            Directory for writing output.
    
    Returns:
        xarray.Dataset:
            Dataset containing the country map
        
        If write:
            Writes the dataset to file.
    '''
    
    database = "Natural_Earth"
    scale = "1:50m"
    
    if lat is None and lon is None:
        lat,lon,height = domain_volume(domain)
    elif lat is None or lon is None:
        raise Exception("Latitude and Longitude arrays must both be specified. Otherwise domain can be used to find these values.")
    
    if database == "Natural_Earth" and scale == "1:50m":
        mask = regionmask.defined_regions.natural_earth.countries_50.mask(lon,lat,xarray=True)
    elif database == "Natural_Earth" and scale == "1:110m":
        mask = regionmask.defined_regions.natural_earth.countries_110.mask(lon,lat,xarray=True)
    
    ## Find region numbers and associate with countries    
    mask_flat = mask.values.flatten()
    regions = np.unique(mask_flat[~np.isnan(mask_flat)])
    region_dict = region_mapping()
    countries = [region_dict[region] for region in regions]

    ## Check for multiple region numbers with the same region name
    unique,inverse,counts = np.unique(countries,return_inverse=True,return_counts=True)
    if counts[counts>1].any():
        repeats = np.where(counts>1)[0]
        repeat_indices = [np.where(inverse == r)[0] for r in repeats]
        repeat_regions = [regions[ri] for ri in repeat_indices]
        
        for region_mult in repeat_regions:
            region_initial = region_mult[0]
            region_repeat = region_mult[1:]
            for region in region_repeat:
                mask.values[np.where(mask == region)] = region_initial
        
        index_remove = [ri for ri_mult in repeat_indices for ri in ri_mult[1:]]
        index_remove.reverse()
        for ri in index_remove:
            countries.pop(ri)
        regions = np.delete(regions,index_remove)

    ## Add ocean label if relevant and set appropriate ocean_ref
    if ocean_label:
        ocean_ref = -1
        countries.insert(0,"OCEAN")
        regions = np.insert(regions,0,[ocean_ref])
    else:
        ocean_ref = -(2)**31
    
    ## Set NaN values as ocean reference but make sure to keep any regions already labelled as 0.0 as 
    # nan_to_num function changes the nan values to 0.
    temp_num = 100000
    mask.values[np.where(mask == 0)] = temp_num
    mask.values = np.nan_to_num(mask)
    mask.values[np.where(mask == 0)] = ocean_ref
    mask.values[np.where(mask == temp_num)] = 0
    
    if reset_index:
        ## Normalise numbers in mask- have to add arbitrary number to avoid clashes when numbers are being reassigned
        add_num = 100000
        mask.values = mask.values+add_num
        for i,region_num in enumerate(regions):
            mask_num = region_num+add_num
            mask.values[np.where(mask == mask_num)] = i
   
    ## Turn mask output into a dataset and add additional parameters and attributes
    
    ds = mask.to_dataset(name="country")

    countries = np.array(countries).astype(str)
    if reset_index:
        ds["name"] = xray.DataArray(countries,dims="ncountries")
    else:
        ds["name"] = xray.DataArray(countries,coords={"ncountries":regions},dims={"ncountries":len(regions)})
    
    ds["country"].attrs = {"long_name":"Country indices"}
    ds["lat"].attrs = {"long_name":"latitude","units":"degrees_north"}
    ds["lon"].attrs = {"long_name":"longitude","units":"degrees_east"}
    ds["name"].attrs = {"long_name":"Country names"}
    
    attributes = OrderedDict([])
    attributes["title"] = "Grid of country extent across {} domain".format(domain)
    attributes["author"] = "File created by {}".format(getpass.getuser())
    attributes["database"] = "{} database with scale {} used to create this file. Python module regionmask (https://regionmask.readthedocs.io/en/stable/) used to extract data.".format(database,scale)
    attributes["extent"] = "Domain beween latitude {} - {}, longitude {} - {} with resolution {:.3f},{:.3f} degrees".format(np.min(lat),np.max(lat),np.min(lon),np.max(lon),lat[1]-lat[0],lon[1]-lon[0])

    ds.attrs = attributes
    
    if write:
        filename = "country_{}.nc".format(domain)
        filename = os.path.join(output_dir,filename)
        if not os.path.isfile(filename):    
            print('Writing output to {}'.format(filename))
            ds.to_netcdf(filename)
        else:
            print("ERROR: DID NOT WRITE TO FILE: {} already exists".format(filename))
    
    return ds

if __name__=="__main__":
    
    ## EXAMPLE OF HOW THIS MODULE CAN BE USED ##
    write = True
    domain = "NORTHAFRICA"
    # Lat/Lon can be specified explictly or a domain footprint file can be used to find these values.
    
    ds = create_country_mask(domain,write=write,reset_index=True,ocean_label=True)
    
