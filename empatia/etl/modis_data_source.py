import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple
import os
from bs4 import BeautifulSoup
from datetime import datetime
from empatia.etl.downloader import get_data, get_data_earthdata
from empatia.settings import MODIS_DATASET_PATH
from empatia.settings.constants import MODIS_BASE_URL
from empatia.settings.credentials import NASA_TOKEN
from empatia.settings.log import logger


def get_modis_urls(
    product: str,
    collection: int,
    north: float,
    south: float,
    east: float,
    west: float,
    start_date: str,
    end_date: str = None,
) -> Tuple[List, List]:
    """
    Get uls of Modis products
    """

    urls: List[str] = []
    fnames: List[Dict] = []

    if not end_date:
        end_date = start_date

    try:
        """
        # check product
        prods = mclient.listProducts()
        if not (product in prods.keys()):
            raise ValueError("Invalid product")

        # check collection
        colls = mclient.getCollections(product)
        if not str(collection) in colls.keys():
            raise ValueError(f"Invalid collection param for {product}")

        files = mclient.searchForFiles(
            product,
            start_date,
            end_date,
            north,
            south,
            east,
            west,
            collection=collection,
        )

        if len(files) == 1:
            raise ValueError(f"Data not found for range: {start_date}-{end_date}")

        for fn in files:
            metadata = mclient.getFileProperties(fn)
            fnames.extend([meta["fileName"] for meta in metadata])
            urls.extend(mclient.getFileUrls(fn))
        """

        url = (
            f"{MODIS_BASE_URL}/?products={product}"
            + f"&temporalRanges={start_date}..{end_date}"
            + f"&regions=[BBOX]N{north}%20S{south}%20E{east}%20W{west}"
        )

        with urllib.request.urlopen(url) as response:
            html = response.read()

        soup = BeautifulSoup(html, "html.parser")
        tags = soup("a")
        for tag in tags:
            u = tag.get("href", None)
            if u.endswith(".hdf") or u.endswith(".h5"):
                # if (product == "VNP46A1") and (".002." in u):
                #    continue
                fnames.append(u.split("/")[-1])
                urls.append(u)

    except ValueError as e:
        logger.error(f"Invalid request to get files for {product}")

    return fnames, urls


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
    logger.info(f"Get MODIS urls to download files for: {product}")
    if not end_date:
        end_date = start_date
        
    start_date = datetime.strptime(start_date, "%Y-%m-%d") 
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    fnames = get_data_earthdata(product, (west, south, east, north), start_date, end_date, dst_path)
    return fnames
