from typing import List, Any
import os

from empatia.settings import MERRA_DATASET_PATH
from empatia.settings.log import logger

from empatia.etl.downloader import get_data_earthdata

from datetime import datetime

def get_merra_files(
    date: str,
    base_url: str,
    product: str,
    shortname: str,
    region: List[float],
    start_hour: str,
    end_hour: str,
    version: str,
    variables: List[str] = [],
    file_format: str = "nc",
) -> List[Any]:
    """
    Download MERRA products
    """

    try:
        dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{date}/"
        os.makedirs(dst_path, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating directory {dst_path}: {e}")
        return

    logger.info(f"Downloading MERRA2 product: {product}")

    start_date = datetime.strptime(date, "%Y-%m-%d") 
    start_hour = datetime.strptime(start_hour, "%H:%M:%S")
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.strptime(date, "%Y-%m-%d")
    end_hour = datetime.strptime(end_hour, "%H:%M:%S")
    end_date = end_date.replace(hour=23, minute=59, second=59)

    fnames = get_data_earthdata(shortname, region, start_date, end_date, dst_path, variables=variables)
    return fnames if fnames else []
