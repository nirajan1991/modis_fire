# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 17:21:25 2021
This script used MRT tool kit to preprocess MODIS fire product data
It uses MRT toolkit as I was used to it compared to pymodis 
@author: Nirajan
"""
import os
import glob
import subprocess
from tqdm import tqdm
import time
#%%
datadir = 'G:\MODIS_fire_product\Downloads'
mosaic_path = 'G:\MODIS_fire_product\Mosaicked'
resample_path = 'G:\MODIS_fire_product\Mosaicked\Resampled'
data_vars = ['MOD', 'MYD']
yaers = list(range(2017,2021))
dyas = list(range(1,146,8)) #use 146 instead of 145
#%%
#first mosaic the data
for dt in data_vars:

    for yr in yaers:
        for d in tqdm(dyas):
            dy = str(yr)+ '{num:03d}'.format(num=d)

            search_criteria = dt+'*'+dy+'*.hdf'
            search_path = os.path.join(datadir,search_criteria)
            filelist = glob.glob(search_path)

            a = open("MOSAICINPUT.TXT", "w")
            for file in filelist:
                a.write('%s\n'%file)
            a.close()
            a = None
            
            print(os.path.join(mosaic_path,dt+'14A1_'+dy+'_Mosaic.hdf'))
            command = 'C:/MRT/bin/mrtmosaic.exe -i MOSAICINPUT.TXT -s "1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 " -o ' + os.path.join(mosaic_path,dt+'14A1_'+dy+'_Mosaic.hdf')
            subprocess.run(command)
            time.sleep(5)
            
        
    
os.remove("MOSAICINPUT.TXT")

#%%

#Then resample the data
search_criteria = '*Mosaic*.hdf'
search_path = os.path.join(mosaic_path,search_criteria)
infilelist = glob.glob(search_path)
filelist = map(os.path.basename,infilelist)
filelist = list(filelist)
prm_file = os.path.join(mosaic_path, '0modis_resample.prm')
#%%
for i,infile in tqdm(enumerate(infilelist)):
    outfile = os.path.join(resample_path, filelist[i]+'.tif')
    command = 'C:/MRT/bin/resample.exe -p '+prm_file+' -i '+infile+'  -o '+ outfile
    subprocess.run(command)
    time.sleep(10)

#resampling creates log file so remove that too
os.remove('resample.log')
#%%
