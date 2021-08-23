'''
Author: Eni Awowale
Date created: February 8, 2021
Last updated: March 9, 2021
Purpose: Calculating zonal statistics with the rasterstats module.
Explaination:
Given a vector layer in a gdb with it's layer number
and a raster layer with it's band num calculate_zone_stats() calculates the zone stats of the given parameters and outputs
as a geoJSON. This script has functions for reading and writing the vector layers so they can be read by rasterstats
Has a reproject function so the vector layers are in the same CRS as their respective rasters
Functions for automating all summary statistics so they are exported as table pdf file of each zones statistics
Function that outputs a bar graph of the zonal stats into a pdf

'''

#Libraries
import os
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
import rasterio as ras
import matplotlib.pyplot as plt
import matplotlib.style
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
import gdal
import fiona

#changing style sheet
matplotlib.style.use('seaborn')

#changing wd
#os.chdir('C:/Users/oawowale/OneDrive - USDA/Geospatial Ecology Team/Test_data/data_python')
os.chdir('E:/eni_folder/Water_Yields_Proj/')

#List of layers in the gdb
eni_geo_db = fiona.listlayers('EniProjData.gdb')

'''Fucntions'''

def field_to_index(dataframe, index_num):
    input_int = int(index_num)
    zone_header = dataframe.iloc[:, input_int]
    change_index = dataframe.set_index(zone_header)
    return change_index

#Read vector and raster functions
def read_vector(vector, layer_num):
    vector_read = gpd.read_file(vector, layer=layer_num)
    return vector_read

def read_raster(raster, band_num):
    raster_read = ras.open(raster, band=band_num)
    return raster_read

#Reprojection fucntion
def reproject(vector_file, raster_file):
    crs_source_raster = raster_file.crs
    #saves the raster crs
    repro = vector_file.to_crs(crs_source_raster)
    return repro

#Function to clean data for writing to table and graphs
#Enter the index of the column with the zones
def clean_data(geodataframe, index_num):
    series = geodataframe.iloc[:, index_num]
    series_df = pd.DataFrame(series)
    geo_stats = geodataframe[['min', 'mean', 'max', 'median', 'sum', 'std', 'range', 'count']]
    geodataframe_join = series_df.join(geo_stats)
    geodataframe_clean = field_to_index(geodataframe_join, 0)
    return geodataframe_clean




'''Functions for creating tables and graphical data'''

def df_to_csv(dataframe, desired_filename):
    str_filename = str(desired_filename) + '.csv'
    dataframe.to_csv(str_filename, index=False)


#this create table function creates a table and exports it as a pdf
def create_table(dataframe):
    name_fig = input('Type the name you want to save the file as with the file extension at the end:')
    string_name_fig = str(name_fig)
    with PdfPages(string_name_fig) as pdf:
        gdf = dataframe
        fig, ax = plt.subplots()
        #hide axes
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        zone_data_val = gdf.values
        rounded_values_list = []
        #rounding values
        for values in zone_data_val:
            val_list = values.tolist()
            for num_val in val_list:
                if type(num_val) == float:
                    rounded_values_list.append(round(num_val, 2))
                elif type(num_val) == str:
                    rounded_values_list.append(num_val.title())
                else:
                    rounded_values_list.append(num_val)
        nested_rounded_lists = [rounded_values_list[x:x + 9] for x in range(0, len(rounded_values_list), 9)]
        array_rounded_values = np.array(nested_rounded_lists)
        column_labels = []
        for labels in gdf.columns:
            column_labels.append(labels.title())
        #column_labels[0] = '' #change to reformat the first columns label name
        table = ax.table(cellText=array_rounded_values, colLabels=column_labels, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(4)
        table.auto_set_column_width(column_labels)
        fig.tight_layout()
        #plt.rcParams["font.weight"] = "semibold"
        plt.show()
        pdf.savefig()
        plt.close()

#Create bar graph function
#function switches the axes of the data
def bar_graph(dataframe):
    dataframe_transposed = dataframe.T
    metrics_df = dataframe_transposed.loc[['min', 'max', 'mean', 'median', 'std']]
    #selecting only the zone stats we want
    metrics_df2 = metrics_df.reset_index()
    #reset index so the index names are now colums
    metrics_df2['index'] = ['Minimum', 'Maximum', 'Mean', 'Median', 'Standard Deviation']
    #changed the names of the columns for display on the map
    name_fig = input('Type the name you want to save the file as with the file extension at the end:')
    string_name_fig = str(name_fig)
    with PdfPages(string_name_fig) as pdf:
        metrics_df2.plot.bar(x='index', colormap='tab20')
        plt.legend(fontsize=6, bbox_to_anchor=(0.9, 0.8), bbox_transform=plt.gcf().transFigure)
        plt.xticks(fontsize=6, rotation=0)
        title_name = input('Type what you would like to name the title')
        str_title_name = str(title_name)
        plt.title(str_title_name)
        plt.xlabel('Summary Statistics')
        plt.ylabel('Basal Area (sq. ft / ac.)')
        plt.show()
        pdf.savefig()
        plt.close()


'''Zone Stats function'''
'''Output is now geojson or a geodataframe when geojson is not true it's a nested dictionary in a list'''
def calculate_zone_stats(vector, layer_num, raster, band_num): #enter vector and raster as their exact names in directory
    vector_file = read_vector(vector, layer_num)
    raster_file = read_raster(raster, band_num)

    if vector_file.crs != raster_file.crs:
        reproject(vector_file, raster_file)
        zone_statistics = zonal_stats(vector_file, raster,
                                      stats=['min', 'mean', 'max', 'median', 'sum', 'std', 'range', 'count'], geojson_out=True)
        #zone_statistics is a geojson (format for stroing geo features) basically just a dictionary
        #geostats is a geojson stored in a geopandas data frame
        geostats = gpd.GeoDataFrame.from_features(zone_statistics)

    else:
        zone_statistics = zonal_stats(vector_file, raster,
                                      stats=['min', 'mean', 'max', 'median', 'sum', 'std', 'range', 'count'], geojson_out=True)
        geostats = gpd.GeoDataFrame.from_features(zone_statistics)
    raster_file.close()
    return geostats



'''Test statements for running code'''
#nat_com_all = calculate_zone_stats("EniProjData/EniProjData.gdb", 0, 'EniProjData/ALL_BAA.tif', 1)
#nat_com_clv3 = calculate_zone_stats("EniProjData/EniProjData.gdb", 0, 'EniProjData/CLC_v3.tif', 1)
#clean_huc_clcv3 = clean_data(nat_com_clv3, 3)
#priority_huc_zonestat = calculate_zone_stats("EniProjData/EniProjData.gdb", 2, 'EniProjData/Pine_BAA.tif', 1)
#priority_huc_zonestat_clean = clean_data(priority_huc_zonestat, 3)


