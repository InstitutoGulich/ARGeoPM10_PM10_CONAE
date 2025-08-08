from datetime import datetime as dt
from itertools import product
from typing import Dict, List
from unittest import result
from urllib import response
import urllib.request
import os

import sys
import json
import urllib3
import certifi
from time import sleep
from http.cookiejar import CookieJar
from urllib.parse import urlencode
import getpass

from empatia.etl.downloader import get_data
from empatia.settings import MERRA_DATASET_PATH
from empatia.settings.constants import MERRA_BASE_URL, MERRA_VERSION
from empatia.settings.credentials import NASA_USER, NASA_PASS
from empatia.settings.log import logger

from bs4 import BeautifulSoup

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

from tqdm import tqdm

def download(url, filename, file_path, headers=None):
    file_url = url + filename
    print(f"Downloading {filename} from {url} to {file_path}")

    if os.path.exists(file_path):
        print(f"{file_path} already exists.. skipping")
        return 

    s = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        print(f"Downloading {filename}.. try {attempts+1}/{max_attempts}")

        file_response = s.get(file_url, headers=headers, stream=True)
        if file_response.status_code != 200:
            print(f"Failed to get response from {file_url}. Status code: {file_response.status_code}")
            attempts += 1
            time.sleep(2)
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

#def get_merra_files(
#    date_stamp: str,   
#    base_url: str,
#    product: str,
#    shortname: str,
#    region: List[str],
#    start_hour: str,
#    end_hour: str,
#    version: str,
#    variables: List[str] = [],
#    file_format: str = "nc",
#) -> None:
#    """
#    Download MERRA products
#    """
#    ds: dt = dt.strptime(date_stamp, "%Y-%m-%d")
#
#    url = (
#            f"{base_url}/data/MERRA2/{shortname}.{version}/"
#            + f"{ds.year}/{ds.month:02d}/"        
#        )
#
#    with urllib.request.urlopen(url) as response:
#        html = response.read()
#
#    soup = BeautifulSoup(html, "html.parser")
#    tags = soup("a")
#    urls: List[str] = []
#    fnames: List[Dict] = []
#    for tag in tags:
#        u = tag.get("href", None)
#        if u.endswith(".nc4") and ds.strftime("%Y%m%d") in u:
#            if not u in urls:
#                print(f"Found file: {u}")
#                urls.append(u)
#
#    dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{ds.strftime('%Y-%m-%d')}/"
#    if not os.path.exists(dst_path):
#        os.makedirs(dst_path)
#
#    headers = {"Authorization": f"Bearer {NASA_TOKEN}"}
#    for u in urls:
#        logger.info(f"Downloading MERRA2 product: {u}")
#        output_filename = dst_path  + u.replace(f".{ds.strftime('%Y%m%d')}","")
#        download(url, u , output_filename, headers=headers)
#
#    return u.replace(f".{ds.strftime('%Y%m%d')}","")
#
#
#def get_merra_files(
#    date_stamp: str,
#    base_url: str,
#    product: str,
#    shortname: str,
#    region: List[str],
#    start_hour: str,
#    end_hour: str,
#    version: str,
#    variables: List[str] = [],
#    file_format: str = "nc",
#) -> None:
#    """
#    Download MERRA products
#    """
#    ds: dt = dt.strptime(date_stamp, "%Y-%m-%d")
#
#    dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{ds.strftime('%Y-%m-%d')}/"
#    filename = (
#        f"/data/MERRA2/{shortname}.{version}"
#        f"/{ds.year}/{ds.month:02d}/{product}.{ds.strftime('%Y%m%d')}.nc4"
#    )
#    time = (
#        f'{ds.strftime("%Y-%m-%d")}T{start_hour}/{ds.strftime("%Y-%m-%d")}T{end_hour}'
#    )
#    label = f'{product}.{ds.strftime("%Y%m%d")}.SUB.nc'
#
#    params = {
#        "FILENAME": filename,
#        "FORMAT": "bmM0Lw",
#        "BBOX": ",".join(region),
#        "TIME": time,
#        "LABEL": label,
#        "SHORTNAME": shortname,
#        "SERVICE": "L34RS_MERRA2",
#        "VERSION": "1.02",
#        "DATASET_VERSION": version,
#        "VARIABLES": ",".join(variables),
#    }
#
#    logger.info(f"Downloading MERRA2 product: {product}")
#    get_data(base_url, f"{dst_path}{product}", file_format, params=params)
#


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
    
    logger.info(f"Requesting subset for {shortname} on {date_stamp} from {base_url}")
    
    try:
        dst_path = f"{MERRA_DATASET_PATH}/{shortname}/{date_stamp}/"
        os.makedirs(dst_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {dst_path}: {e}")
        return

    response = get_http_data(subset_request)
    myJobId = response['result']['jobId']
    assert response['result']['Status'] == 'Accepted'

    # Construct JSON WSP request for API method: GetStatus
    status_request = {
        'methodname': 'GetStatus',
        'version': '1.0',
        'type': 'jsonwsp/request',
        'args': {'jobId': myJobId}
    }

    logger.info(f'{shortname} - Job ID: {myJobId}')
    while response['result']['Status'] in ['Accepted', 'Running']:
        sleep(5)
        response = get_http_data(status_request)
        status  = response['result']['Status']
        percent = response['result']['PercentCompleted']
        print ('Job status: %s (%d%c complete)' % (status,percent,'%'))

    if response['result']['Status'] == 'Succeeded' :
        print ('Job Finished:  %s' % response['result']['message'])
    else : 
        print('Job Failed: %s' % response['fault']['code'])

    result = requests.get('https://disc.gsfc.nasa.gov/api/jobs/results/'+myJobId)
    try:
        result.raise_for_status()
        urls = result.text.split('\n')
        urls = [url for url in urls if not url.strip().endswith('.pdf')]
    except:
        print('Request returned error code %d' % result.status_code)

    password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, "https://urs.earthdata.nasa.gov", NASA_USER, NASA_PASS)

    # Create a cookie jar for storing cookies. This is used to store and return the session cookie #given to use by the data server
    cookie_jar = CookieJar()

    # Install all the handlers.
    opener = urllib.request.build_opener (urllib.request.HTTPBasicAuthHandler (password_manager),urllib.request.HTTPCookieProcessor (cookie_jar))
    urllib.request.install_opener(opener)

    for URL in urls:
        if URL.endswith('.pdf') or URL.strip() == '':
            continue

        logger.info(f"Downloading MERRA2 product: {product}")

        DataRequest = urllib.request.Request(URL)
        DataResponse = urllib.request.urlopen(DataRequest)

        # Print out the result
        DataBody = DataResponse.read()

        # Save file to working directory
        try:
            file_ = open(f"{dst_path}{product}.nc", 'wb')
            file_.write(DataBody)
            file_.close()
        except requests.exceptions.HTTPError as e:
            print(e)

    logger.info(f"Files downloaded to {dst_path}")
    return f"{product}.nc"