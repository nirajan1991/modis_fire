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
import datetime
from tqdm import tqdm
import numpy as np
import os
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

#define a function to read the data directly
def readrasterdata(file):
    ds = gdal.Open(file)
    data = ds.ReadAsArray()
    ds = None
    return data

#%%
#Define the variables for looping with them later
modis_sat = ['MOD', 'MYD']
modis_vars = ['FireMask', 'QA']
days_numbers = list(range(1,9))
day_of_year = list(range(1,146,8))
yaers = list(range(2017,2021))
pathdir = r'G:\MODIS_fire_product\Resampled'
outdir = r'G:\MODIS_fire_product\zonal_stat_output'

shapefile = r'G:\MODIS_fire_product\nepal_new_sinusoidal.shp'
#read shapefil to get districts name
shape_gpd = gpd.read_file(shapefile)
districts = shape_gpd['DIST_EN'].values
#%%
fire_threshold = 7 #firemask vlaues 7,8,9 refer to fire with low confidence, moderate confidence, high confidence resp.

qc_bits = np.arange(0,7)
qc_big_endian = de2bi(qc_bits,3)
mask = slicer_vectorized(qc_big_endian, 1, 3)
day_night = slicer_vectorized(qc_big_endian, 0, 1)
land_qc = qc_bits[mask == '10']
#%%
sample_file = os.path.join(pathdir, 'MOD14A1_2017009_Mosaic.hdf.FireMask.Number_of_Days_01.tif')
ds = gdal.Open(sample_file)
transform = ds.GetGeoTransform()
proj = ds.GetProjection() 
ds = None

#%%
#loop through each day
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
                #get data only for land area
                land_mask_mod = np.isin(data_qa_mod, land_qc)
                #create mask for fire detected pixel based on the confident fire detected pixels
                fire_mask_mod = data_fire_mod >= fire_threshold
                #combine the masks
                mod_data_fire_land = np.logical_and(land_mask_mod,fire_mask_mod).astype(np.uint8)
                
            if os.path.exists(myd_fire_file):
                data_fire_myd = readrasterdata(myd_fire_file)
                data_qa_myd = readrasterdata(myd_qa_file)
                
                land_mask_myd = np.isin(data_qa_myd, land_qc)
                fire_mask_myd = data_fire_myd >= fire_threshold
                
                myd_data_fire_land = np.logical_and(land_mask_myd,fire_mask_myd).astype(np.uint8)
                
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
            #read the date from file name
            file_date = datetime.timedelta(days = doy+dn-1)
            date_date = date_base + file_date
            date_str = date_date.strftime('%Y-%m-%d')
            #%%
            #write the masked data to a temporary file
            outfile = os.path.join(outdir,'temporary_file.tif')
            
            driver = gdal.GetDriverByName('GTiff')
            outds = driver.Create(outfile, data_fire_mask.shape[1],\
                                  data_fire_mask.shape[0], 1, gdal.GDT_Float32) #gdal saved only zeros when Interger was used so used float
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
            stat = zonal_stats(shapefile,outfile,stats=['count'])
            count_vals = [i.get('count')  for i in stat]
            stat_array = np.array(count_vals).astype(np.float32)
            district_area = stat_array  * transform[1] * transform[1] #for gdal size is at 1
            district_stat = district_area.astype(object)
            district_stat = np.insert(district_stat, 0, date_str).reshape(1,-1)

            stat_collection = np.append(stat_collection, district_stat, axis =0)

        time.sleep(10)

    stat_pd = pd.DataFrame(stat_collection)

    csv_out_fn = 'MODMYD_fire_area_'+str(fire_threshold)+'_districtwise_'+str(yr)+'.csv'
    csv_out_file = os.path.join(outdir, csv_out_fn)

    stat_pd.to_csv(csv_out_file, header = None, index = None)

    time.sleep(60) #prevent overheating of processor
#%%
'''
#remove the temporary file
os.remove(outfile)
#check the fire mask if found some anamoly
from matplotlib import pyplot
pyplot.figure()
pyplot.imshow(data_fire_mask)
'''
