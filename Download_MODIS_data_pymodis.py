# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 17:21:25 2021
This scrpt is used to download the MODIS land surface product from NASA LP DAAC
#followed the example given at https://github.com/lucadelu/pyModis/blob/master/scripts/modis_download.py
@author: Nirajan
"""
#%%
import pymodis
import os
import glob
#%%
pathdir = ('G:\MODIS_fire_product').replace('\\','/')
yaers = list(range(2017, 2021))

username = 'your_username'
password = 'your_password'
tiles = ['h24v05', 'h24v06', 'h25v05', 'h25v06']
paths = ['MOLT','MOLA'] #separate folder for terra and aqua
products = ['MOD14A1.006', 'MYD14A1.006']
timeout = 60
url = 'https://e4ftl01.cr.usgs.gov'

for ii in range(len(products)):
    for yr in yaers:
        startdate = str(yr)+'-01-01'
        enddate = str(yr)+'-05-31'
        modis_request = pymodis.downmodis.downModis(pathdir, password = password, user = username,\
                                    url = url, path =paths[ii], product = products[ii], tiles = tiles,\
                                    today = startdate, enddate = enddate, jpg = False, delta = 10,\
                                    debug = False, checkgdal=False)
        modis_request.connect()
        if modis_request.nconnection <= 20:
            modis_request.downloadsAllDay(clean = False, allDays = False)
            print('Downloading: Check the folder' + pathdir)
        else:
            print('A problem with the connection occured')
#%%
#check download
search_criteria = '*.hdf'
search_path = os.path.join(pathdir, search_criteria).replace('\\', '/')
filelist = glob.glob(search_path)
no_of_files = len(filelist)
if no_of_files == 0:
    print('NO DATA DOWNLOADED')
#%%
#remove xml files
search_criteria = '*.xml'
search_path = os.path.join(pathdir, search_criteria).replace('\\', '/')
filelist = glob.glob(search_path)
for f in filelist:
    os.remove(f)
