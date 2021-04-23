# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 17:44:06 2021
This script reads modis fire products tiffiles and
calculates the actual date from filename, then
quality filter according to quality filter file
save them as binary fire/no fire tifffile
peform zonal statistics to get values for each district
save results as csv file for each year
@author: Nirajan
"""
#%%
#import necesary libraries
from osgeo import gdal #do not import gdal and rasterio in the same programme
#import rasterio
#from netCDF4 import Dataset
import datetime
from tqdm import tqdm
import numpy as np
#import re
import os
#import glob
#from matplotlib import pyplot as plt
import time
from rasterstats import zonal_stats
import geopandas as gpd
import pandas as pd
#%%
#Make a vectorized function for converting decimel to binary
de2bi = np.vectorize(np.binary_repr)
#Then create function to slice an array of strings
def slicer_vectorized(a,start,end):
    b = a.view((str,1)).reshape(len(a),-1)[:,start:end]
    return np.frombuffer(b.tobytes(),dtype=(str,end-start))

'''
#define a function to read the data directly
def readrasterdata(file):
    ds = rasterio.open(file)
    data = ds.read(1)
    ds.close()
    return data

def readrasterattributes(file):
    ds = rasterio.open(file)
    transform = ds.transform #rasterio used affine
    crs = ds.crs #rasterio used pyproj style
    ds.close()

    return transform, crs
'''
#define a function to read the data directly
def readrasterdata(file):
    ds = gdal.Open(file)
    data = ds.ReadAsArray()
    ds = None
    return data

def readrasterattributes(file):
    ds = gdal.Open(file)
    transform = ds.GetGeoTransform()
    proj = ds.GetProjection() #rasterio used pyproj style
    ds = None

    return transform, proj

#%%
#Define the variables for looping with them later
modis_sat = ['MOD', 'MYD']
modis_vars = ['FireMask', 'QA']
days_numbers = list(range(1,9))
day_of_year = list(range(1,146,8))
yaers = list(range(2017,2021))
pathdir = r'G:\MODIS_fire_product\Resampled'
outdir = r'G:\MODIS_fire_product\zonal_stat_output'
#pathdir = '/media/gdrive/MODIS_fire_product/Resampled'
#outdir = '/media/gdrive/MODIS_fire_product/zonal_stat_output'

#shapefile = 'G:\G-Drive\Shapefiles\New_Darchula\District\Darchulanewmerged_sinosoidal.shp'
shapefile = r'G:\MODIS_fire_product\nepal_new_sinusoidal.shp'
#shapefile = '/media/gdrive/G-Drive/Shapefiles/npl_admbnda_nd_20190430_shp/npl_admbnda_districts_nd_20190430.shp'
#read shapefil to red districts name
shape_gpd = gpd.read_file(shapefile)
districts = shape_gpd['DIST_EN'].values
#Insert title to the date
#%%
fire_threshold = 7 #firemask vlaues 7,8,9 refer to fire, 7 means low confidence

qc_bits = np.arange(0,7)
qc_big_endian = de2bi(qc_bits,3)
mask = slicer_vectorized(qc_big_endian, 1, 3)
day_night = slicer_vectorized(qc_big_endian, 0, 1)
land_qc = qc_bits[mask == '10']
#%%
sample_file = os.path.join(pathdir, 'MOD14A1_2017009_Mosaic.hdf.FireMask.Number_of_Days_01.tif')
#transform, crs = readrasterattributes(sample_file)
ds = gdal.Open(sample_file)
transform = ds.GetGeoTransform()
proj = ds.GetProjection() #rasterio used pyproj style
ds = None
#transform, proj = readrasterattributes(sample_file)

#%%


'''
for yr in [2020]:
    stat_collection = districts.copy()
    stat_collection = np.insert(stat_collection, 0, 'Date').reshape(1,-1)
    date_base = datetime.date(yr,1,1)

    for doy in tqdm([73]):
        for dn in [3]:
'''
for yr in yaers:
    stat_collection = districts.copy()
    stat_collection = np.insert(stat_collection, 0, 'Date').reshape(1,-1)
    date_base = datetime.date(yr,1,1)

    for doy in tqdm(day_of_year):
        for dn in days_numbers:

            mod_fire_file = os.path.join(pathdir, 'MOD14A1_'+str(yr)+'{:03d}'.format(doy)+'_Mosaic.hdf.'+modis_vars[0]+'.Number_of_Days_'+'{:02}'.format(dn)+'.tif').replace('\\','/')
            mod_qa_file = os.path.join(pathdir, 'MOD14A1_'+str(yr)+'{:03d}'.format(doy)+'_Mosaic.hdf.'+modis_vars[1]+'.Number_of_Days_'+'{:02}'.format(dn)+'.tif').replace('\\','/')
            myd_fire_file = os.path.join(pathdir, 'MYD14A1_'+str(yr)+'{:03d}'.format(doy)+'_Mosaic.hdf.'+modis_vars[0]+'.Number_of_Days_'+'{:02}'.format(dn)+'.tif').replace('\\','/')
            myd_qa_file = os.path.join(pathdir, 'MYD14A1_'+str(yr)+'{:03d}'.format(doy)+'_Mosaic.hdf.'+modis_vars[1]+'.Number_of_Days_'+'{:02}'.format(dn)+'.tif').replace('\\','/')

            # mod_fire_search_criteria = modis_sat[0] +'*'+str(yr)+'*'+ modis_vars[0] +'*.tif'
            if os.path.exists(mod_fire_file):
                data_fire_mod = readrasterdata(mod_fire_file)
                data_qa_mod = readrasterdata(mod_qa_file)
                #create mask for fire detected pixel based on the confident fire detected pixels
                land_mask_mod = np.isin(data_qa_mod, land_qc)
                fire_mask_mod = data_fire_mod >= fire_threshold
                #This gave zero area in all years and days so i will exclude the land mask
                mod_data_fire_land = np.logical_and(land_mask_mod,fire_mask_mod).astype(np.uint8)
                #mod_data_fire_land = fire_mask_mod

            if os.path.exists(myd_fire_file):
                data_fire_myd = readrasterdata(myd_fire_file)
                data_qa_myd = readrasterdata(myd_qa_file)
                #create mask for fire detected pixel based on the confident fire detected pixels
                land_mask_myd = np.isin(data_qa_myd, land_qc)
                fire_mask_myd = data_fire_myd >= fire_threshold
                myd_data_fire_land = np.logical_and(land_mask_myd,fire_mask_myd).astype(np.uint8)
                #myd_data_fire_land = fire_mask_myd

            #get the data if fire is detected in any one product
            if os.path.exists(mod_fire_file) and os.path.exists(myd_fire_file):
                data_fire_mask = np.logical_or(mod_data_fire_land, myd_data_fire_land)
            elif os.path.exists(mod_fire_file) == True and os.path.exists(myd_fire_file) == False:
                data_fire_mask = mod_data_fire_land
            elif os.path.exists(myd_fire_file) == True and os.path.exists(mod_fire_file) == False:
                data_fire_mask = myd_data_fire_land
            else:
                break #break that loop and skip everything after that

            data_fire_mask = data_fire_mask.astype(np.float32)
            #%%
            '''
            filename = os.path.basename(mod_fire_file)
            #define the time values of each day from the filename
            n_pos = re.findall('\d+',filename)
            #gives list of 4 items first modis product 14, second product type 1, and doy and day
            file_date = n_pos[2]
            nth_day = n_pos[3]
            data_doy = str(int(file_date) + int(nth_day) - 1)
            data_date = datetime.datetime.strptime(data_doy,'%Y%j').date()
            date_str = data_date.strftime('%Y-%m-%d')
            #Use of strptime is understood from this link and %Y means 4digit, %y means 2digit year value
            #https://stackoverflow.com/questions/37743940/how-to-convert-julian-date-to-standard-date
            #date_since_1970 = data_date - datetime.date(1970, 1, 1)
            '''
            file_date = datetime.timedelta(days = doy+dn-1)
            date_date = date_base + file_date
            date_str = date_date.strftime('%Y-%m-%d')
            #%%
            #write the masked data to a temporaty file
            outfile = os.path.join(outdir,'temporary_file.tif')
            '''
            with rasterio.open(
                outfile,
                'w',
                driver='GTiff',
                height=data_fire_mask.shape[0],
                width=data_fire_mask.shape[1],
                count=1,
                dtype=data_fire_mask.dtype,
                crs = crs,
                transform=transform,
            ) as dst:
                dst.write(data_fire_mask, 1)
            '''
            driver = gdal.GetDriverByName('GTiff')
            outds = driver.Create(outfile, data_fire_mask.shape[1],\
                                  data_fire_mask.shape[0], 1, gdal.GDT_Float32)
            outds.SetProjection(proj)
            outds.SetGeoTransform(transform)

            outband = outds.GetRasterBand(1)
            outband.SetNoDataValue(0)

            outband.WriteArray(data_fire_mask)
            data_fire_written = outds.ReadAsArray()
            outband.FlushCache()
            outds.FlushCache()
            outband = None
            outds = None

            del outds, outband

            outdsfile = gdal.Open(outfile)
            out_written_data = outdsfile.ReadAsArray()
            outdsfile = None

            #%%
            #stat = zonal_stats(shapefile,outfile,stats=['count'], nodata = 0)
            stat = zonal_stats(shapefile,outfile,stats=['count'])
            count_vals = [i.get('count')  for i in stat]
            stat_array = np.array(count_vals).astype(np.float32)
            #district_area = stat_array  * transform[0] * transform[0] #for rasterio size is at 0
            district_area = stat_array  * transform[1] * transform[1] #for gdal size is at 1
            district_stat = district_area.astype(object)
            district_stat = np.insert(district_stat, 0, date_str).reshape(1,-1)

            stat_collection = np.append(stat_collection, district_stat, axis =0)

        time.sleep(10)

    stat_pd = pd.DataFrame(stat_collection)

    csv_out_fn = 'MODMYD_fire_area_'+str(fire_threshold)+'_districtwise_'+str(yr)+'.csv'
    csv_out_file = os.path.join(outdir, csv_out_fn)

    stat_pd.to_csv(csv_out_file, header = None, index = None)

    time.sleep(60)
#%%
'''
#os.remove(outfile)
from matplotlib import pyplot
pyplot.figure()
pyplot.imshow(data_fire_mask)
'''
