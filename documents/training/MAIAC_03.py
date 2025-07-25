# %%
import os
import pandas as pd
import rasterio
from datetime import datetime, timedelta
from tqdm import tqdm
import numpy as np

nodata_value = -9999

# Load PM station data
pm_data_path = "/home/msgro/work/empatia/documents/training/estaciones_ceilap.csv"
pm_data = pd.read_csv(pm_data_path, header=0)

# Input and output directories
tile = 'h13v12'
output_file = os.path.join('/home/msgro/work/empatia/data/model', 'MAIAC_pixel_data_CEILAP_2010-2019_INTERPOLADO.csv')

# Initialize an empty list to store results
results = []
for year in range(2010, 2020):
    root_folder = f'/home/msgro/work/empatia/data/model/MAIAC/{tile}/{year}/'
    dir_inicial = f'{root_folder}/recorte_interpolado'  # Output directory

    # List all .tif files in the input directory
    files = [f for f in os.listdir(dir_inicial) if f.endswith('.tif')]

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
        raster_path = os.path.join(dir_inicial, filename)
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
