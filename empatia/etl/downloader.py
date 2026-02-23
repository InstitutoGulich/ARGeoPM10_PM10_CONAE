from typing import Dict, List, Any

import requests
from requests.exceptions import HTTPError

from harmony import Client, Collection, Request, BBox
import earthaccess
import os

from empatia.etl.file_writer import FileWriter
from empatia.settings.log import logger
from empatia.utils.exceptions import FileExists

auth = earthaccess.login(strategy="environment",persist=False)
harmony_client = Client(token=os.environ["EARTHDATA_TOKEN"])

def get_data(
    url: str, dst: str, file_format: str, params: Dict = {}, headers: Dict = {}
) -> None:
    """
    Download files
    Args:
        url: source url
        dst: location of the downloaded file
        file_format: file extension
        params: download parameters
        header: download header
    """
    try:
        writer = FileWriter(path=dst, file_format=file_format, force=True)
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        writer(response.content)
        logger.info(f"Contents of {response.url} written to {writer.destination}")
    except FileExists:
        logger.info("Dataset already exists")
    except HTTPError as e:
        logger.error("Data was not downloaded", exc_info=e)
        raise HTTPError

def get_data_earthdata(
        short_name: str, bbox: tuple, start_date: str, end_date: str, dst_path: str, variables=['all']
) -> List[Any]:

    bbox = BBox(*bbox)

    temporal = {
        "start": start_date,
        "stop": end_date
    }

    concept_id = earthaccess.search_datasets(short_name=short_name)[0].concept_id()

    request = Request(
        collection=Collection(concept_id),
        spatial=bbox,
        temporal=temporal,
        variables=variables
    )

    try:
        if not request.is_valid():
            logger.error("Local validation error", exc_info=request.parameter_validations)
        else:
            job_id = harmony_client.submit(request)
            harmony_client.wait_for_processing(job_id, show_progress=False)

    except Exception as e:
        logger.error("Harmony request failed:", exc_info=e)

    os.makedirs(dst_path, exist_ok=True)

    futures = harmony_client.download_all(job_id, directory=dst_path, overwrite=False)

    filelist = [f.result() for f in futures]
    return filelist if filelist else []