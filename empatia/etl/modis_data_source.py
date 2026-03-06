import os
from pathlib import Path
from datetime import datetime
from empatia.etl.downloader import get_data_earthdata
from empatia.settings.log import logger

def get_modis_files(
    dst_path: str,
    product: str,
    collection: int,
    north: float,
    south: float,
    east: float,
    west: float,
    start_date: str,
    end_date: str = None,
) -> list:
    """
    Download Modis products
    Return: True - if there are files to be processed
            False - otherwise
    """

    dst_path = Path(dst_path)
    dst_path.mkdir(parents=True, exist_ok=True)
    
    existing_files = list(dst_path.glob(f"*.hdf"))
    if existing_files:
        logger.info(f"Files already exist in {dst_path}. Skipping download.")
        return existing_files

    logger.info(f"Get MODIS urls to download files for: {product}")
    if not end_date:
        end_date = start_date

    start_date = datetime.strptime(start_date, "%Y-%m-%d") 
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    fnames = get_data_earthdata(product, (west, south, east, north), start_date, end_date, dst_path)

    return fnames if fnames else []
