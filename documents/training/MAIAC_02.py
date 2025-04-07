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
crs_project = "EPSG:4326"  # WGS84
#merra_domain = box(-59.2, -35, -57.7, -34)  # Bounding box for cropping
merra_domain = box(-63.4, -39.3, -57.7, -34)  # Bounding box for cropping #Bahia Blanca
tile = 'h13v12'

for year in range(2016, 2020):

    root_folder = f'/home/msgro/work/empatia/data/model/MAIAC/{tile}/{year}/'
    dirin = f'{root_folder}/tif'  # Input directory
    dirout = f'{root_folder}/recorte_interpolado'  # Output directory
    os.makedirs(dirout, exist_ok=True)

    # List all .tif files in the input directory
    files = [f for f in os.listdir(dirin) if f.endswith('.tif')]

    # Process each file
    for filename in tqdm(files, desc=f"Processing files for {year}"):
        # Construct the full file path
        filepath = os.path.join(dirin, filename)

        # Open the raster file
        with rasterio.open(filepath) as src:
            # Crop the raster to the MERRA domain
            domain_geom = [mapping(merra_domain)]
            out_image, out_transform = mask(src, domain_geom, crop=True)
            out_meta = src.meta.copy()

            # Update metadata for the cropped raster
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "crs": crs_project,
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
            output_filepath = os.path.join(dirout, f"{os.path.splitext(filename)[0]}_rec_interpol.tif")
            with rasterio.open(output_filepath, "w", **out_meta) as dst:
                dst.write(grid_z, 1)
                
# %%
