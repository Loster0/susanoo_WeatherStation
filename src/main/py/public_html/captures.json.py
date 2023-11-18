#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

from db_module import get_home
from urllib.parse import parse_qsl

HOME = get_home()
LOGFILE = HOME + "/susanoo-web.log"
logging.basicConfig(
    filename=LOGFILE,
    level=logging.DEBUG,
    format='%(asctime)s\t%(levelname)s\t%(name)s (%(process)d)\t%(message)s')
log = logging.getLogger("captures.json")

# Get the query string from the environment
query_string = os.environ.get("QUERY_STRING")

log.info(f"Start building json for capture '{query_string}'")


def write_content_type():
    print("Content-type: application/json; charset=utf-8\n")
    return


def write_json_content(data_to_print):
    # Serialize the JSON object to a string
    json_data = json.dumps(data_to_print, ensure_ascii=False)  # ensure_ascii=False to allow non-ASCII characters
    # json_data = json.dumps(folder_data, indent=4)

    # Output the JSON data
    print(json_data)


def get_oldest_created_folder(folder):
    # log.debug(f"get_oldest_created_folder({l_folder}) starting")
    oldest_folder = None
    oldest_timestamp = float('inf')  # Initialize with a large value

    for dir_name in os.listdir(folder):
        # log.debug(f"\tchecking subfolder '{dir_name}'")
        dir_path = os.path.join(folder, dir_name)
        if os.path.isdir(dir_path):
            # log.debug(f"\t\tis directory")
            try:
                timestamp = os.path.getctime(dir_path)  # Date of creation
                if timestamp < oldest_timestamp:
                    oldest_folder = os.path.basename(dir_path)  # Extract only the folder name
                    oldest_timestamp = timestamp
            except OSError:
                pass  # Ignore any errors, such as permission denied

    # log.debug(f"get_oldest_created_folder({l_folder}) returning -> '{oldest_folder}'")
    return oldest_folder


def get_newest_modified_folder(folder):
    # log.debug(f"get_newest_modified_folder({l_folder}) starting")
    newest_folder = None
    newest_timestamp = 0  # Initialize with zero

    for dir_name in os.listdir(folder):
        dir_path = os.path.join(folder, dir_name)
        if os.path.isdir(dir_path):
            try:
                timestamp = os.path.getmtime(dir_path)  # Date of modification
                if timestamp > newest_timestamp:
                    newest_folder = os.path.basename(dir_path)  # Extract only the folder name
                    newest_timestamp = timestamp
            except OSError:
                pass  # Ignore any errors, such as permission denied

    # log.debug(f"get_newest_modified_folder({l_folder}) returning -> '{newest_folder}'")
    return newest_folder


def get_first_folder(path, reverse_order=True):
    try:
        # Get a list of all directories in the specified path
        folders = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

        # Sort the list of folders alphabetically (or in reverse order if reverse_order is True)
        sorted_folders = sorted(folders, reverse=reverse_order)

        # Return the first folder in the sorted list
        if sorted_folders:
            return sorted_folders[0]
        else:
            log.warning(f"No folder found in '{path}'!")
            return None  # Return None if there are no folders in the specified path
    except OSError as e:
        log.critical(f"OSError occurred when getting folder from {path}: {e}")
        return None


def get_json_pictures_from_folder(pictures_folder):
    pictures_in_folder = {}

    # Get a list of filenames sorted alphabetically
    filenames = sorted(os.listdir(pictures_folder))

    for filename in filenames:
        if filename.endswith(".jpg"):
            # Extract the timestamp from the filename
            timestamp = filename.split("_")[1].split(".")[0]  # Assumes the format is "sensor_YYYY-MM-DDZhh-mm-ss.jpg"
            time_parts = timestamp[-8:].split("-")
            hour_minute = f"{time_parts[0]}h{time_parts[1]}"

            # Get file size
            file_path = os.path.join(pictures_folder, filename)
            fsize = os.path.getsize(file_path)

            # Add an entry to the pictures_in_folder dictionary
            pictures_in_folder[hour_minute] = {"fSize": fsize, "img": filename}

    return pictures_in_folder


def get_json_from_folder(l_sensor, l_year, l_month, l_day):
    # log.debug(os.getcwd())
    error_message = ""

    if l_sensor:
        if os.path.exists(f"captures/{l_sensor}"):
            sensor_folder = l_sensor
        else:
            sensor_folder = get_first_folder("captures", reverse_order=False)
            message = f"Sensor '{l_sensor}' was not valid, '{sensor_folder}' will be used instead."
            log.warning(message)
            error_message = message + "<br/>\n"
    else:
        sensor_folder = get_first_folder("captures", reverse_order=False)
    log.debug(f"sensor_folder = '{sensor_folder}'")

    if l_year:
        if os.path.exists(f"captures/{sensor_folder}/{l_year}"):
            year_folder = l_year
        else:
            year_folder = get_first_folder(f"captures/{sensor_folder}", reverse_order=True)
            message = f"Given year '{l_year}' was not valid, '{year_folder}' will be used instead."
            log.warning(message)
            error_message = error_message + message + "<br/>\n"
    else:
        year_folder = get_first_folder(f"captures/{sensor_folder}", reverse_order=True)
    log.debug(f"       + year = '{year_folder}'")

    if l_month and l_day:
        if os.path.exists(f"captures/{sensor_folder}/{year_folder}/{l_month}-{l_day}"):
            month_day_folder = f"{l_month}-{l_day}"
        else:
            month_day_folder = get_first_folder(f"captures/{sensor_folder}/{year_folder}", reverse_order=True)
            message = f"Given that month-day '{l_month}-{l_day}' was not a valid folder," \
                      f" '{month_day_folder}' will be used instead"
            log.warning(message)
            error_message = error_message + message + "<br/>\n"
    else:
        month_day_folder = get_first_folder(f"captures/{sensor_folder}/{year_folder}", reverse_order=True)
    log.debug(f"      + mm-dd = '{month_day_folder}'")

    log.info(f"Will get pictures from folder '{month_day_folder}'")

    pictures_json = get_json_pictures_from_folder(f"captures/{sensor_folder}/{year_folder}/{month_day_folder}")
    metadata_json = {"sensor": sensor_folder,
                     "year": year_folder,
                     "month_day": month_day_folder,
                     "error_message": error_message}
    data_json = {"pictures": pictures_json,
                 "metadata": metadata_json}
    return data_json


write_content_type()

# Parse the query string to extract parameters
query_params = parse_qsl(query_string)

# Create a dictionary to store the parameters
params = dict(query_params)

# Access the values by key
sensor = params.get("s")
year = params.get("y")
month = params.get("m")
day = params.get("d")

log.debug(f"sensor='{sensor}'\tyear='{year}'\tmonth-day='{month}-{day}'")

data = get_json_from_folder(sensor, year, month, day)
write_json_content(data)
log.info("Terminated building json for capture page")
