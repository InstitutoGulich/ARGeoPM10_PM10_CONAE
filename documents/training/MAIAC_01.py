#%%
import os
import numpy as np
from osgeo import gdal
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import Affine
from rasterio.crs import CRS
from tqdm import tqdm

# Constants
TILE = 'h13v12'
ROOT_FOLDER = f'/media/data/msgro/empatia/data/model/MAIAC'
TILE_FOLDER = f'{ROOT_FOLDER}/{TILE}/'
VALID_QA = [1, 2, 9, 10, 17, 18, 25, 26, 97, 105, 113, 121, 98, 106, 114, 122]
WORKING_PROJECTION = 'EPSG:4326'  # WGS84
NODATA_VALUE = -9999

# %%

# Helper function to reproject raster
def reproject_raster(src, dst_crs, qa):
    
    # Get GeoTransform
    src_transform = src.GetGeoTransform()
    src_crs = src.GetProjection()
    
    src_array = src.ReadAsArray()

    invalid_mask = ~np.isin(qa, VALID_QA)
    src_array[invalid_mask] = NODATA_VALUE
    
    dst_array = np.empty(src_array.shape, dtype = src_array.dtype)
    src_transform = Affine.from_gdal(*src_transform)  # Convert source transform

    dst_array, dst_transform = reproject(
        source=src_array,
        destination=dst_array,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_crs=dst_crs,
        resampling=Resampling.nearest
    )

    return dst_array, dst_transform

def write_tif(array, transform, fileout):
    options = {
        'driver': 'GTiff',
        'height': array.shape[0],
        'width': array.shape[1],
        'count': 1,
        'dtype': array.dtype,
        'crs': WORKING_PROJECTION,
        'transform': transform,
        'nodata': NODATA_VALUE
    }
    with rasterio.open(fileout, 'w', **options) as dst:
        dst.write(array, 1)

# %%
def QA2Char(num):
    if not np.isnan(num):  # Check if the number is not NaN
        # Convert decimal to binary and pad to 32 bits
        binary_str = format(int(num), '032b')
        
        # Extract the last 16 bits
        char = binary_str[-16:]
        
        # QA array
        qa_arr = [
            char[0],          # 15 Reserved
            char[1:3],        # 13-14 Aerosol Model
            char[3],          # 12 Glint Mask
            char[4:8],        # 8-11 QA AOD
            char[8:11],       # 5-7 Adjacency Mask
            char[11:13],      # 3-4 Land Water Snow/Ice Mask
            char[13:16]       # 0-2 Cloud Mask
        ]
    else:
        qa_arr = [None] * 7  # Return an array of None if the input is NaN

    return qa_arr

# %%
def proccess_hdf_file(filepath, output_dir):

    # Open HDF file and extract subdatasets using gdal
    hdf_dataset = gdal.Open(filepath)
    subdatasets = hdf_dataset.GetSubDatasets()

    # Extract orbit metadata
    metadata = hdf_dataset.GetMetadata()
    orbits = metadata.get('Orbit_time_stamp', '').split()

    # QA
    qa_idx = next(i for i, s in enumerate(subdatasets) if "AOD_QA" in s[0])
    qa_ds = gdal.Open(subdatasets[qa_idx][0])
    qa = qa_ds.ReadAsArray()

    for band in ["Optical_Depth_047", "Optical_Depth_055"]:
        band_idx = next(i for i, s in enumerate(subdatasets) if band in s[0])
        band_ds = gdal.Open(subdatasets[band_idx][0])

        band_wavelength = band.split('_')[-1]  # Extract wavelength from band name

        # Reproject to WGS84
        band_reproj, band_transform = reproject_raster(band_ds, WORKING_PROJECTION, qa)

        # Save each orbit as .tif
        for i, orbit in enumerate(orbits):
            year = orbit[:4]
            jd = orbit[4:7]
            hour = orbit[7:9] + orbit[9:11]
            sat = orbit[11]

            # AOD 470 nm
            matrix = band_reproj[i]
            if not (matrix < 0).all():
                fileout = os.path.join(output_dir, f'MCD19A2.{TILE}.{sat}.{band_wavelength}.{year}{jd}.{hour}.tif')
                write_tif(matrix, band_transform, fileout)
            else:
                print(f"Skipping {band_wavelength} {year}{jd}.{hour}")

    return True

def proccess(input_dir, output_dir):

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # List all .hdf files in the input directory
    files = [f for f in os.listdir(input_dir) if f.endswith('.hdf')]

    # Process each file
    for filename in tqdm(files, desc="Processing HDF files"):
        filepath = os.path.join(input_dir, filename)
        proccess_hdf_file(filepath, output_dir)

# %%

if __name__ == "__main__":
    init_year = 2010
    end_year = 2020
    for year in range(init_year, end_year):
        input_dir = os.path.join(TILE_FOLDER, str(year), 'hdf')
        output_dir = os.path.join(TILE_FOLDER, str(year), 'tif')
        proccess(input_dir, output_dir)
        print(f"Processed files for year {year}.")
# %%