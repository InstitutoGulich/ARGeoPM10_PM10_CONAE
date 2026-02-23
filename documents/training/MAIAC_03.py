# %%
import os
import pandas as pd
import rasterio
from datetime import datetime, timedelta
from tqdm import tqdm
import numpy as np

# Constants
TILE = 'h13v12'
ROOT_FOLDER = '/media/data/msgro/empatia/data/model/MAIAC'
TILE_FOLDER = f'{ROOT_FOLDER}/{TILE}/'
WORKING_PROJECTION = 'EPSG:4326'  # WGS84
NODATA_VALUE = -9999
PM_DATA_PATH = "/home/msgro/work/empatia/documents/training/estaciones_ceilap.csv"
OUTPUT_FILE = 'MAIAC_pixel_data_CEILAP_2010-2019_INTERPOLADO.csv'

def process(input_dir, results):

    # List all .tif files in the input directory
    files = [f for f in os.listdir(input_dir) if f.endswith('.tif')]

    # Process each file
    for filename in tqdm(files, desc=f"Processing files for {year}"):
        # Extract date-time information from the filename
        year = int(filename[21:25])
        julian_day = int(filename[25:28])
        hour = int(filename[29:31])
        minute = int(filename[31:33])
        date = datetime(year, 1, 1) + timedelta(days=julian_day - 1)
        fecha = f"{date.strftime('%Y-%m-%d')} {hour:02}:{minute:02}:00"

        # Extract wavelength and satellite information
        taod = int(filename[17:20])
        sat = filename[15]

        # Open the raster file
        raster_path = os.path.join(input_dir, filename)
        with rasterio.open(raster_path) as src:
            # Process each PM station
            for _, station in pm_data.iterrows():
                # Get station coordinates
                coordinates = [(station['LONGITUDE'], station['LATITUDE'])]
                
                # Extract AOD value for the station
                for val in rasterio.sample.sample_gen(src, coordinates):
                    valor = int(val[0]) if val[0] is not None else np.nan
                    valor = valor*0.001 if valor > 0 else np.nan
                # Append the result
                results.append([fecha, sat, taod, valor, station['SHORTNAME']])

if __name__ == "__main__":
    # Load PM station data
    pm_data = pd.read_csv(PM_DATA_PATH, header=0)

    # Define output file path
    output_file = os.path.join(ROOT_FOLDER, OUTPUT_FILE)

    # Initialize an empty list to store results
    results = []
    for year in range(2010, 2020):
        input_dir = os.path.join(TILE_FOLDER, str(year), 'recorte_interpolado')
        process(input_dir, results)

    # Convert results to a DataFrame
    columns = [
        'Fecha_Hora (yyyy-mm-dd hh:mm:ss)',
        'Satelite',
        'AODnm',
        'valor_AOD',
        'estacion_pm'
    ]
    results_df = pd.DataFrame(results, columns=columns)
    results_df['Fecha_Hora (yyyy-mm-dd hh:mm:ss)'] = pd.to_datetime(results_df['Fecha_Hora (yyyy-mm-dd hh:mm:ss)'])
    results_df.dropna(inplace=True)
    results_df.set_index('Fecha_Hora (yyyy-mm-dd hh:mm:ss)', inplace=True)
    results_df.sort_index(inplace=True)

    # Save the results to a CSV file
    results_df.to_csv(output_file, index=True, float_format='%.3f')
# %%
