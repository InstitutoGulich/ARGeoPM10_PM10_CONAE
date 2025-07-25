from datetime import datetime as dt
from typing import Dict, List
import urllib.request

from empatia.etl.downloader import get_data
from empatia.settings import MERRA_DATASET_PATH
from empatia.settings.constants import MERRA_BASE_URL
from empatia.settings.credentials import NASA_TOKEN
from empatia.settings.log import logger

from bs4 import BeautifulSoup

def get_merra_files(
    date_stamp: str,
    base_url: str,
    product: str,
    shortname: str,
    region: List[str],
    start_hour: str,
    end_hour: str,
    version: str,
    variables: List[str] = [],
    file_format: str = "nc",
) -> None:
    """
    Download MERRA products
    """
    ds: dt = dt.strptime(date_stamp, "%Y-%m-%d")

    url = (
            f"{MERRA_BASE_URL}/data/MERRA2/{shortname}.{version}/"
            + f"{ds.year}/{ds.month:02d}/"        
        )

    with urllib.request.urlopen(url) as response:
        html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    tags = soup("a")
    urls: List[str] = []
    fnames: List[Dict] = []
    for tag in tags:
        u = tag.get("href", None)
        if u.endswith(".nc4") and ds.strftime("%Y%m%d") in u:
            print(f"Found file: {u}")
            fnames.append(u.split("/")[-1])
            urls.append(url + u)

    #filename = (
    #    f"/data/MERRA2/{shortname}.{version}"
    #    f"/{ds.year}/{ds.month:02d}/{product}.{ds.strftime('%Y%m%d')}.nc4"
    #)
    #time = (
    #    f'{ds.strftime("%Y-%m-%d")}T{start_hour}/{ds.strftime("%Y-%m-%d")}T{end_hour}'
    #)
    #label = f'{product}.{ds.strftime("%Y%m%d")}.SUB.nc'

    #params = {
    #    "FILENAME": filename,
    #    "FORMAT": "bmM0Lw",
    #    "BBOX": ",".join(region),
    #    "TIME": time,
    #    "LABEL": label,
    #    "SHORTNAME": shortname,
    #    "SERVICE": "L34RS_MERRA2",
    #    "VERSION": "1.02",
    #    "DATASET_VERSION": version,
    #    "VARIABLES": ",".join(variables),
    #}

    dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{ds.strftime('%Y-%m-%d')}/"

    headers = {"Authorization": f"Bearer {NASA_TOKEN}"}
    for url, filename in zip(urls, fnames):
        logger.info(f"Downloading MERRA2 product: {filename}")
        get_data(url, f"{dst_path}{filename}", file_format, headers=headers)
