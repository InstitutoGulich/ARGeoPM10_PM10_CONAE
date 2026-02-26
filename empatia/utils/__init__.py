import os
import glob
import numpy as np
import datetime as dt
import shutil
import json
from pathlib import Path
from typing import Dict, List, Union
from empatia.settings.constants import DEFAULT_DATE_FORMAT
from empatia.settings.log import logger


def date_range(start: dt.date, end: dt.date) -> List[str]:
    delta = end - start
    date_list = []
    for i in range(delta.days + 1):
        day = start + dt.timedelta(days=i)
        date_list.append(day.strftime(DEFAULT_DATE_FORMAT))

    return date_list


def get_dates_to_download_for_a_range(start_date: str, end_date: str = None) -> List[str]:
    if not end_date:
        return [start_date]
    date_format = "%Y-%m-%d"
    start_date_dt = dt.datetime.strptime(start_date, date_format)
    end_date_dt = dt.datetime.strptime(end_date, date_format)
    return [
        (start_date_dt + dt.timedelta(days=days)).strftime(date_format)
        for days in range((end_date_dt - start_date_dt).days + 1)
    ]


def get_dates_to_download(log_file: str, today: dt.datetime) -> List[str]:
    min_exec_date = dt.datetime.strftime(
        today - dt.timedelta(days=90), DEFAULT_DATE_FORMAT
    )
    logger.info("Running ETL ...")
    if os.path.exists(log_file):
        with open(log_file) as json_file:
            log_data = json.load(json_file)
            uncompleted_dates = log_data["uncompleted_dates"]
            date_start = dt.datetime.strptime(
                log_data["last_execution_date"], DEFAULT_DATE_FORMAT
            )
    else:
        uncompleted_dates = []
        date_start = today
    dates_to_download = list(set(uncompleted_dates + date_range(date_start, today)))
    dates_to_download = sorted(filter(lambda x: x >= min_exec_date, dates_to_download))
    return dates_to_download


def get_total_cells(result: Dict) -> int:
    cells_data = [k for k in result if k.startswith("cells")][0]
    total_cells = int(cells_data.replace(" ", "")[6:])
    logger.debug(f"Total cells in Argentina: {total_cells}")
    return total_cells


def get_qa_class(x: float) -> int:
    _class = -9999
    if np.isnan(x):
        _class = -9999
    elif (x > 0.1) and (x <= 54):
        _class = 1
    elif (x > 54) and (x <= 154):
        _class = 2
    elif (x > 154) and (x <= 254):
        _class = 3
    elif (x > 254) and (x <= 354):
        _class = 4
    elif (x > 354) and (x <= 424):
        _class = 5
    elif x > 424:
        _class = 6

    return _class


def create_xml(xml_template: Union[str, Path], metadata: Dict, outfile: str) -> None:

    with open(xml_template, "r") as xml_file:
        xml = "".join(xml_file.readlines())

    for key, value in metadata.items():
        xml = xml.replace(key, value)

    with open(f"{outfile}.xml", "w") as xml_file:
        xml_file.writelines(xml)


def zip_directory(input_dir: str, output_dir: str) -> None:
    shutil.make_archive(output_dir, "zip", input_dir)


def remove_folder(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        print(f"Folder not found: {path}")


def remove_folders_from_date(pattern: str, ds: dt.date) -> None:
    paths = sorted(glob.glob(pattern))
    for path in paths:
        path_ds = dt.datetime.strptime(path.split("/")[-1], DEFAULT_DATE_FORMAT)
        if path_ds < ds:
            remove_folder(path)


def remove_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted file: {path}")
    else:
        print(f"No {path} file to delete")

def update_log_data(dates_to_download: List[str], log_file: str, uncompleted_dates: List[str]) -> None:
    """
    Update log data with the last execution date and the uncompleted dates for the next execution
    
    Args:
        dates_to_download (List[str]): List of dates that were attempted to be downloaded and processed in the current execution
        log_file (str): Path to the log file where data is stored
        new_uncompleted_dates (List[str]): List of dates that were not completed in the current execution
    """
    last_execution_date = dates_to_download[-1]
    log_data = {
        "last_execution_date": last_execution_date,
        "uncompleted_dates": sorted(set(uncompleted_dates)),
    }
    with open(log_file, "w") as outfile:
        json.dump(log_data, outfile)
