import json
import os.path
import string
from datetime import datetime

from decision_window_calc import decisionDelay
from sat_manager import get_ssc_mapping_from_file
from stk_interface import STKInterface

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def convert_name(satellite_name):
    satellite_name = satellite_name.replace(" ", "_")
    allowed_chars = string.ascii_letters + string.digits + "_"

    satellite_name = "".join(filter(lambda c: c in allowed_chars, list(satellite_name)))
    return satellite_name


def show_results_in_stk():
    # Load report
    results_dir = os.path.join(BASE_DIR, "results")
    report_file = os.path.join(results_dir, "report.json")
    with open(report_file, "r") as outfile:
        results = json.load(outfile)

    # Setup STK
    stk_interface = STKInterface(cleanup=False) # False, so satellites stay in scenario

    # Get ssc number mapping
    celestrak_file = "celestrak.json"
    satellite_ssc_number_mapping = get_ssc_mapping_from_file(celestrak_file)

    # Get satellites capable of defending
    report = results["report"]
    print(f"Found {len(report.keys())} potential defender satellites")

    for satellite_name in report.keys():
        # Get ssc number
        ssc_number = satellite_ssc_number_mapping[satellite_name]

        # Add current defender satellite to stk scenario
        stk_satellite_name = "Defender_" + convert_name(satellite_name)
        stk_interface.add_satellite(stk_satellite_name, ssc_number)


def one_to_one_experiment():
    # Time run
    experiment_start = datetime.now()

    # Setup STK
    stk_interface = STKInterface()

    # Set experiment time
    target_time = "1 Jan 2024 03:00:45.000000000"

    # Set experiment bit_rate and related parameters
    bit_rate = 9600  # in bits per second
    tail_size = 6 * 8
    tail_time = 1 / bit_rate * tail_size

    # Get all active satellites and their SSC number
    celestrak_file = "celestrak.json"
    satellite_ssc_number_mapping = get_ssc_mapping_from_file(celestrak_file)

    # Get attacker and victim form stk scenario
    attacker = stk_interface.attacker_object
    victim = stk_interface.victim_object

    # Calculate static values for experiment
    AtoV = None
    AtoV_aer = stk_interface.get_aer_report_data(attacker, victim)
    if AtoV_aer:
        if target_time in AtoV_aer.keys():
            AtoV = AtoV_aer[target_time] * 1000  # we want it in m
    if not AtoV:
        # Not in range during the time window of the simulation
        print(f"Attacker and Victim are not in range of each other!")
        exit(1)

    # Start experiment
    print("Starting experiment...")
    report = {}
    loop_round = 0
    for satellite_name, ssc_number in satellite_ssc_number_mapping.items():
        # Give user feedback
        loop_round += 1
        progress = (loop_round / len(satellite_ssc_number_mapping)) * 100
        print(f"Run {loop_round} of {len(satellite_ssc_number_mapping)} | {progress}% done")

        # Artificial limit
        """if round >= 150:
            break"""

        # Add current defender satellite to stk scenario
        stk_satellite_name = "Defender_" + convert_name(satellite_name)
        defender = stk_interface.add_satellite(stk_satellite_name, ssc_number)

        # Calculate distances
        AtoD = None
        AtoD_aer = stk_interface.get_aer_report_data(attacker, defender)
        if AtoD_aer:
            if target_time in AtoD_aer.keys():
                AtoD = AtoD_aer[target_time] * 1000  # we want it in m
        if not AtoD:
            # Not in range during the time window of the simulation
            stk_interface.remove_satellite(defender)
            continue

        DtoV = None
        DtoV_aer = stk_interface.get_aer_report_data(defender, victim)
        if DtoV_aer:
            if target_time in DtoV_aer.keys():
                DtoV = DtoV_aer[target_time] * 1000  # we want it in m
        if not DtoV:
            # Not in range during the time window of the simulation
            stk_interface.remove_satellite(defender)
            continue

        # Calculate decision delay in seconds
        decision_delay = decisionDelay(AtoD, DtoV, AtoV, tail_time)

        # Check if we could react
        if decision_delay > 0:
            report[satellite_name] = {
                "AtoV": AtoV,
                "AtoD": AtoD,
                "DtoV": DtoV,
                "decision_delay": decision_delay
            }

        # Cleanup for next iteration
        stk_interface.remove_satellite(defender)

    # Time run
    experiment_end = datetime.now()
    print(f"Start: {experiment_start}")
    print(f"End: {experiment_end}")
    print(f"Runtime: {experiment_end - experiment_start}")

    output = {
        "setup": {
            "Attacker": stk_interface.attacker_object.InstanceName,
            "Victim": stk_interface.victim_object.InstanceName,
            "Target Time": target_time,
            "Bit rate": bit_rate
        },
        "runtime": {
            "start": str(experiment_start),
            "end": str(experiment_end),
            "runtime": str(experiment_end - experiment_start)
        },
        "report": report
    }

    # Store report
    results_dir = os.path.join(BASE_DIR, "results")
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)

    report_file = os.path.join(results_dir, "report_Exp1.json")
    with open(report_file, "w") as outfile:
        json.dump(output, outfile, indent=1)


if __name__ == "__main__":
    one_to_one_experiment()
    # show_results_in_stk()
