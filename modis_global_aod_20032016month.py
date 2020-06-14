import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import sys
from netCDF4 import Dataset
import netCDF4 as nc

#---------------------------------------------------------------
#combine MODIS Monthly mean Dust AOD over ocean (Dr. Yu) and over land (Paul)
#Over Ocean 2000-2017; Over land 2003-2016
#Global product 2013-2016
#---------------------------------------------------------------
def global_mn_aod(iy):
    #read MODIS ocean product from Dr.Yu  
    ocean_dir ='/home/cd11735/zzbatmos_common/Data/Global_dust_from_HongbinYu/Hongbin_Ocean_monthly/'
    ocean_fname = ocean_dir+ 'AquaMODISAODComponentsmonthly20002017.nc'
    ocean_dataset = Dataset(ocean_fname)
    ocean_year    = ocean_dataset.variables['year'][:]
    ocean_lat     = ocean_dataset.variables['lat'][:]
    ocean_lon     = ocean_dataset.variables['lon'][:]
    ocean_dod     = ocean_dataset.variables['daod'][:] #((18year, 12mon, 180lat, 360lon))
    ocean_taod    = ocean_dataset.variables['taod'][:] #((18year, 12mon, 180lat, 360lon))
    ocean_year_list = ocean_year.tolist()
    iy_ocean = ocean_year_list.index(year[iy])
    #read MODIS land product from Paul
    land_dir  ='/home/cd11735/zzbatmos_common/Data/Global_dust_from_HongbinYu/Paul_Land/aqua/'
    land_fname  = land_dir +'fod_sod_dod_av_mth_{:4d}_1x1_mth.nc'.format(year[iy])
    land_dataset = Dataset(land_fname)
    land_lat  = land_dataset.variables['lat'][:]
    land_lon  = land_dataset.variables['lon'][:]
    land_dod  = land_dataset.variables['dod_flag3_av_mth'][:]#(12time, 180lat, 360lon)
    land_fod  = land_dataset.variables['fod_flag3_av_mth'][:]#(12time, 180lat, 360lon)
    land_sod  = land_dataset.variables['sod_flag3_av_mth'][:]#(12time, 180lat, 360lon)
    #the following three variables are for total aod (taod) calculation (summation = taod)
    land_dod_for_taod = land_dataset.variables['dod_flag3_av_mth'][:]#(12time, 180lat, 360lon) 
    land_fod_for_taod = land_dataset.variables['fod_flag3_av_mth'][:]#(12time, 180lat, 360lon)
    land_sod_for_taod  = land_dataset.variables['sod_flag3_av_mth'][:]#(12time, 180lat, 360lon) 

    land_fill_value = land_dataset.variables['dod_flag3_av_mth']._FillValue
    ocean_fill_value = -9.9
    print(land_fill_value,ocean_fill_value)

    #replace filled_value with np.nan
    ocean_dod[ocean_dod<=ocean_fill_value]   = np.nan
    ocean_taod[ocean_taod<=ocean_fill_value] = np.nan
    land_dod[land_dod <= land_fill_value]    = np.nan
    land_dod_for_taod[land_dod_for_taod<=land_fill_value] = 0.0
    land_fod_for_taod[land_fod_for_taod<=land_fill_value] = 0.0
    land_sod_for_taod[land_sod_for_taod<=land_fill_value] = 0.0
   
    #This part combine MODIS ocean and land together 
    global_mon_dod = np.zeros((12,180,360)) #12month,180lat,360lon
    global_mon_taod = np.zeros((12,180,360))
    bm = Basemap()
    for im in np.arange(0,12):
        for ilat in range(180):
            for ilon in range(360):
                if not(bm.is_land(ocean_lon[ilon],ocean_lat[ilat])): # check whether the location is over ocean
                    global_mon_dod[im,ilat,ilon]=ocean_dod[iy_ocean,im,ilat,ilon]
                    global_mon_taod[im,ilat,ilon]=ocean_taod[iy_ocean,im,ilat,ilon] 
                else:
                    global_mon_dod[im,ilat,ilon]=land_dod[im,ilat,ilon]
                    global_mon_taod[im,ilat,ilon]=land_dod_for_taod[im,ilat,ilon]+land_fod_for_taod[im,ilat,ilon]+land_sod_for_taod[im,ilat,ilon]
    #convert to 5lonx2lat, in order to be consistent with CALIOP dust product
    global_mon_dod_5x2deg=np.zeros((12,90,72))#12month,90lat,72lon
    global_mon_taod_5x2deg=np.zeros((12,90,72))#12month,90lat,72lon
    lon_ct = np.arange(-179.5,180,1)
    lat_ct = np.arange(89.5,-90,-1)
    lon_ct_new=np.arange(177.5,-180,-5)
    lat_ct_new=np.arange(-89,90,2)
    for im in range(12):
        for ilat in range(90):
            for ilon in range(72):
                lon_mask=((lon_ct>=lon_ct_new[ilon]-2.5))&(lon_ct<(lon_ct_new[ilon]+2.5))
                lat_mask=((lat_ct>=lat_ct_new[ilat]-1))&(lat_ct<(lat_ct_new[ilat]+1))
                global_mon_dod_5x2deg[im,ilat,ilon]=np.nanmean(global_mon_dod[im,:,:][lat_mask,:][:,lon_mask])
                global_mon_taod_5x2deg[im,ilat,ilon]=np.nanmean(global_mon_taod[im,:,:][lat_mask,:][:,lon_mask])
    return(global_mon_dod_5x2deg,global_mon_taod_5x2deg)

if __name__ == '__main__':
    year  = np.array([2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016])
    ny    = len(year)
    nm    = 12
    nlat  = 90
    nlon  = 72
    global_mon_dod_20032016  = np.zeros((ny,nm,nlat,nlon))
    global_mon_taod_20032016 = np.zeros((ny,nm,nlat,nlon))
    for iy in range(ny):
        global_mon_dod_20032016[iy,:,:,:]  = global_mn_aod(iy)[0]
        global_mon_taod_20032016[iy,:,:,:] = global_mn_aod(iy)[1]
    #-----------------
    #write netCDF file
    #-----------------
    #write to netcdf file
    lonS  = np.arange(177.5,-180,-5)
    latS  = np.arange(-89,90,2)
    yearS = year
    monS  = range(12)
    nlon  = len(lonS)
    nlat  = len(latS)
    ny    = len(yearS)
    nm    = len(monS)
    
    da=nc.Dataset('ModisGlobalMonthlyGlobalAOD20032016.nc','w',format='NETCDF4')
    da.createDimension('lons',nlon) #create x coordinate
    da.createDimension('lats',nlat) #create y coordinate
    da.createDimension('year',ny)
    da.createDimension('month',nm)
    da.createVariable("lon",'f',("lons")) #'f' 数据类型，不可或缺
    da.createVariable("lat",'f',("lats"))
    da.createVariable("year",'f',("year"))
    da.createVariable("month",'f',("month"))
    da.createVariable('daod','f',('year','month','lats','lons'))
    da.createVariable('taod','f',('year','month','lats','lons'))
    da.variables['lat'][:]   = latS     #填充数据
    da.variables['lon'][:]   = lonS     #填充数据
    da.variables['year'][:]  = yearS
    da.variables['month'][:] = monS
    da.variables['daod'][:]  = global_mon_dod_20032016
    da.variables['taod'][:]  = global_mon_taod_20032016
    da.close()
