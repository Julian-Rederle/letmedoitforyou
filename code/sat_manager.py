import os.path
import json


# Get database from https://www.celestrak.org/NORAD/elements/ -> JSON -> "Active Satellites"
def get_celestrak_data(celestrak_file):
    scc_number_mapping = {}

    if not os.path.isfile(celestrak_file):
        print(f"File not found: {celestrak_file}")
        exit(1)

    with open(celestrak_file, "r") as f:
        content = f.read()

    celestrak_data = json.loads(content)

    return celestrak_data

def get_ssc_mapping_from_file(database_file):
    scc_number_mapping = {}
    satellite_data = get_celestrak_data(database_file)
    for satellite_values in satellite_data:
        # Change format to be valid for STK
        ssc_number = str(satellite_values["NORAD_CAT_ID"])
        scc_number_padded = "0"*(5-len(ssc_number)) + ssc_number
        scc_number_mapping[satellite_values["OBJECT_NAME"]] = scc_number_padded

    return scc_number_mapping