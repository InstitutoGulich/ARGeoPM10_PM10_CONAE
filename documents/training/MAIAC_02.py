# %%
import os
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping
import geopandas as gpd
from scipy.interpolate import griddata
from tqdm import tqdm

# Constants
TILE = 'h13v12'
ROOT_FOLDER = f'/media/data/msgro/empatia/data/model/MAIAC'
TILE_FOLDER = f'{ROOT_FOLDER}/{TILE}/'
WORKING_PROJECTION = 'EPSG:4326'  # WGS84
MERRA_DOMAIN = box(-63.4, -39.3, -57.7, -34)  # Bounding box for cropping

def proccess_tif_file(filepath, output_dir):
    # Open the raster file
    with rasterio.open(filepath) as src:
        # Crop the raster to the MERRA domain
        domain_geom = [mapping(MERRA_DOMAIN)]
        out_image, out_transform = mask(src, domain_geom, crop=True)
        out_meta = src.meta.copy()

        # Update metadata for the cropped raster
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": WORKING_PROJECTION,
            "dtype": 'float64'
        })

        # Mask the raster to the MERRA domain
        mask_array = geometry_mask(domain_geom, transform=out_transform, invert=True, out_shape=out_image.shape[1:])
        cropped_raster = np.where(mask_array, out_image[0], out_meta['nodata'])

    # Create a grid for interpolation
    x = np.linspace(out_transform[2], out_transform[2] + out_transform[0] * cropped_raster.shape[1], cropped_raster.shape[1])
    y = np.linspace(out_transform[5], out_transform[5] + out_transform[4] * cropped_raster.shape[0], cropped_raster.shape[0])
    xv, yv = np.meshgrid(x, y)

    # Extract valid points for interpolation
    valid_mask = ~np.isnan(cropped_raster)
    if np.sum(valid_mask) > 1764:  # Interpolate only if at least 10% of data is valid
        points = np.column_stack((xv[valid_mask], yv[valid_mask]))
        values = cropped_raster[valid_mask]

        # Interpolate using Inverse Distance Weighting (IDW)
        grid_z = griddata(points, values, (xv, yv), method='linear')

        # Save the interpolated raster
        output_file = os.path.split(filepath)[-1]
        output_filepath = os.path.join(output_dir, output_file)
        with rasterio.open(output_filepath, "w", **out_meta) as dst:
            dst.write(grid_z, 1)
                
def process(input_dir, output_dir):

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # List all .tif files in the input directory
    files = [f for f in os.listdir(input_dir) if f.endswith('.tif')]

    # Process each file
    for filename in tqdm(files, desc="Processing TIF files"):
        filepath = os.path.join(input_dir, filename)
        proccess_tif_file(filepath, output_dir)

# %%
if __name__ == "__main__":
    init_year = 2010
    end_year = 2020
    for year in range(init_year, end_year):
        input_dir = os.path.join(TILE_FOLDER, str(year), 'tif')
        output_dir = os.path.join(TILE_FOLDER, str(year), 'recorte_interpolado')
        process(input_dir, output_dir)
        print(f"Processed files for year {year}.")