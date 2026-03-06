from typing import List, Any
from pathlib import Path

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
    file_format: str = "nc4",
) -> List[Any]:
    """
    Download MERRA products
    """

    dst_path = Path(MERRA_DATASET_PATH) / shortname / date
    dst_path.mkdir(parents=True, exist_ok=True)
    
    existing_files = list(dst_path.glob(f"*{file_format}"))
    if existing_files:
        logger.info(f"Files already exist in {dst_path}. Skipping download.")
        return dst_path / existing_files[0].name
    
    logger.info(f"Downloading MERRA2 product: {product}")

    start_date = datetime.strptime(date, "%Y-%m-%d") 
    #start_hour = datetime.strptime(start_hour, "%H:%M:%S")
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.strptime(date, "%Y-%m-%d")
    #end_hour = datetime.strptime(end_hour, "%H:%M:%S")
    end_date = end_date.replace(hour=23, minute=59, second=59)

    fnames = get_data_earthdata(shortname, region, start_date, end_date, dst_path, variables=variables)
    return fnames[0] if fnames else []
