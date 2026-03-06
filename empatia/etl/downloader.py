from typing import List, Any
import os

from harmony import Client, Collection, Request, BBox
import earthaccess

from empatia.settings.log import logger

auth = earthaccess.login(strategy="environment",persist=False)
harmony_client = Client(auth=(os.environ["EARTHDATA_USERNAME"], os.environ["EARTHDATA_PASSWORD"]))

def get_data_earthdata(
    short_name: str, 
    bbox: tuple, 
    start_date: str, 
    end_date: str, 
    dst_path: str, 
    variables=['all']
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

    futures = harmony_client.download_all(job_id, directory=dst_path, overwrite=False)

    filelist = [f.result() for f in futures]
    return filelist if filelist else []