from typing import List
import os

import json
import urllib3
import certifi
from time import sleep

from empatia.settings import MERRA_DATASET_PATH
from empatia.settings.constants import MERRA_VERSION
from empatia.settings.credentials import NASA_TOKEN
from empatia.settings.log import logger


import requests
from requests.adapters import HTTPAdapter, Retry

from tqdm import tqdm

def download(file_url, filename, file_path, headers=None):
    
    if os.path.exists(file_path):
        logger.info(f"{file_path} already exists.. skipping")
        return

    s = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        logger.info(f"Downloading {filename}.. try {attempts+1}/{max_attempts}")
        logger.info(f"Requesting {file_url}")

        file_response = s.get(file_url, headers=headers, stream=True)
        if file_response.status_code != 200:
            logger.error(f"Failed to get response from {file_url}. Status code: {file_response.status_code}")
            attempts += 1
            sleep(2)
            break

        file_size = int(file_response.headers.get('Content-Length', 0))
        progress = tqdm(file_response.iter_content(1024), f'Downloading {filename}', total=file_size, unit='B', unit_scale=True, unit_divisor=1024)
        with open(file_path, 'wb') as f:
            for data in progress.iterable:
                f.write(data)
                progress.update(len(data))
        progress.close()
            
        if file_response.status_code == 200:
            break

    return file_response.status_code

def get_http_data(request):
    
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
    url = 'https://disc.gsfc.nasa.gov/service/subset/jsonwsp'

    headers = {'Content-Type': 'application/json',
               'Accept'      : 'application/json'}

    try:
        data = json.dumps(request)
        r = http.request('POST', url, body=data, headers=headers)
        response = json.loads(r.data)
    except urllib3.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        raise

    if response['type'] == 'jsonwsp/fault' :
        print(f'API Error: faulty {response["methodname"]} request')

    return response

def get_merra_product_url(request):
    """
    Get MERRA product URL from the NASA API.
    """
    response = get_http_data(request)
    myJobId = response['result']['jobId']
    
    if response['type'] == 'jsonwsp/fault':
        logger.error(f"API Error: {response['fault']['message']}")
        raise

    # Construct JSON WSP request for API method: GetStatus
    status_request = {
        'methodname': 'GetStatus',
        'version': '1.0',
        'type': 'jsonwsp/request',
        'args': {'jobId': myJobId}
    }

    while response['result']['Status'] in ['Accepted', 'Running']:
        sleep(5)
        response = get_http_data(status_request)

    if response['result']['Status'] == 'Succeeded' :
        logger.info(f"Job {myJobId} completed successfully. {response['result']['message']}")
    else : 
        logger.error(f"Job {myJobId} failed with status: {response['result']['Status']}")
        raise

    result = requests.get(f'https://disc.gsfc.nasa.gov/api/jobs/results/{myJobId}')
    try:
        result.raise_for_status()
        urls = result.text.split('\n')
        urls = [url for url in urls if not url.strip().endswith('.pdf')]
    except:
        logger.error(f'Request returned error code {result.status_code}')
        raise

    if not urls:
        logger.error(f"No valid URLs found for job {myJobId}")
        raise ValueError(f"No valid URLs found for job {myJobId}")

    return urls[0]


def get_merra_files(
    date_stamp: str,
    base_url: str,
    product: str,
    shortname: str,
    region: List[float],
    start_hour: str,
    end_hour: str,
    version: str,
    variables: List[str] = [],
    file_format: str = "nc",
) -> None:
    """
    Download MERRA products
    """

    try:
        dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{date_stamp}/"
        os.makedirs(dst_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {dst_path}: {e}")
        return

    logger.info(f"Requesting subset for {shortname} on {date_stamp} from {base_url}")

    data = []
    for var in variables:
        data.append({'datasetId': f"{shortname}_{MERRA_VERSION}", 'variable': var})

    subset_request = {
        'methodname': 'subset',
        'type': 'jsonwsp/request',
        'version': '1.0',
        'args': {
            'role'  : 'subset',
            'start' : date_stamp + 'T' + start_hour,
            'end'   : date_stamp + 'T' + end_hour,
            'box'   : region,
            'crop'  : True, 
            'data': data
        }
    }

    try:
        url = get_merra_product_url(subset_request)
    except Exception as e:
        logger.error(f"Failed to get MERRA product URL: {e}")
        return

    logger.info(f"Downloading MERRA2 product: {product}")
    headers = {"Authorization": f"Bearer {NASA_TOKEN}"}
    download(url, product, f"{dst_path}{product}.nc", headers=headers)
    logger.info(f"Files downloaded to {dst_path}")
    return f"{product}.nc"