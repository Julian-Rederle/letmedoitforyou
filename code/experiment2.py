import json
import os.path
from datetime import datetime, timedelta

from decision_window_calc import decisionDelay
from sat_manager import get_ssc_mapping_from_file
from stk_interface import STKInterface

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# See: https://planet4589.org/space/con/largecon.html
# CONSTELLATIONS = ["globalstar", "iridium", "jilin", "beidou", "orbcomm", "kepler"]
CONSTELLATIONS = ["starlink"]

def set_animation_time(stk_interface, start_time, target_time):
    start_time_datetime = stk_interface.stk_date_to_datetime(start_time)
    target_time_datetime = stk_interface.stk_date_to_datetime(target_time)

    offset_in_seconds = target_time_datetime - start_time_datetime
    stk_interface.root.CurrentTime = offset_in_seconds.total_seconds()

def many_to_one_experiment():
    # Time run
    experiment_start = datetime.now()

    # Setup STK
    stk_interface = STKInterface()

    # Set experiment time window
    time_window_start = "1 Jan 2024 00:00:00.000000000"
    time_window_end = "2 Jan 2024 00:00:00.000000000"
    stk_interface.scenario.SetTimePeriod(time_window_start, time_window_end)

    # Set experiment step size of time
    time_step_size = 60 # 10  # sec

    # Set experiment bit_rate and related parameters
    """bit_rate = 9600  # in bits per second
    tail_size = 6 * 8
    tail_time = 1 / bit_rate * tail_size"""
    tail_time = 8 / 1000


    # Get all active satellites and their SSC number
    celestrak_file = "celestrak.json"
    satellite_ssc_number_mapping = get_ssc_mapping_from_file(celestrak_file)

    # Get attacker and victim form stk scenario
    attacker = stk_interface.attacker_object
    victim = stk_interface.victim_object

    # Start experiment
    print("Starting experiment...")

    # Get slots of victim in range of attacker during experiment time window
    AtoV_time_range_map = stk_interface.get_aer_report_data(attacker, victim, step_size=time_step_size)

    if not AtoV_time_range_map:
        print("Attacker is never in range of victim in this scenario!")
        exit(1)

    constellation_time_defender_mapping = {}

    constellation_loop_round = 0
    for constellation_name in CONSTELLATIONS:
        constellation_loop_round += 1
        print(f"Start testing constellation {constellation_name}")

        # Collect all satellite scc numbers of that constellation
        satellite_name_filter = lambda sat: constellation_name.lower() in sat.lower()
        satellite_names = list(filter(satellite_name_filter, list(satellite_ssc_number_mapping.keys())))

        sat_name_ssc_map = {}
        for satellite_name in satellite_names:
            sat_name_ssc_map[satellite_name] = satellite_ssc_number_mapping[satellite_name]

        time_defender_mapping = {}
        # Fill time_defender_mapping with time slot where we need to defend
        for target_time in AtoV_time_range_map.keys():
            time_defender_mapping[target_time] = {}

        # For each satellite in constellation check time at which they can protect
        time_for_one_check = timedelta(minutes=3)
        satellite_loop_round = 0
        for satellite_name, satellite_ssc_number in sat_name_ssc_map.items():
            satellite_loop_round += 1

            # For runtime estimations
            one_check_start = datetime.now()

            # Skip if we already defend all time slots
            if all(time_defender_mapping.values()):
                print(f"Skipping checks for {constellation_name}. All time slots already defended!")
                break

            # Add satellite to simulation
            stk_satellite_name = stk_interface.convert_name(satellite_name)
            satellite_object = stk_interface.add_satellite(stk_satellite_name, satellite_ssc_number)

            # Check for each timeslot in which we need protection
            time_loop_round = 0
            for target_time, AtoV in AtoV_time_range_map.items():
                # Give feedback during run
                time_loop_round += 1

                # Skip if we already have a defender for that time slot
                if time_defender_mapping[target_time]:
                    print(f"Skipping {target_time}. Defender already found!")
                    continue

                time_progress = round((time_loop_round / len(AtoV_time_range_map.keys())) * 100, 3)
                satellite_progress = round((satellite_loop_round / len(sat_name_ssc_map.keys())) * 100, 3)
                constellation_progress = round((constellation_loop_round / len(CONSTELLATIONS)) * 100, 3)
                print(f"Checking time {target_time} | Time {time_progress}% | Satellite {satellite_progress}% | Constellation {constellation_progress}%")
                current_runtime = datetime.now() - experiment_start
                satellites_checks_left = len(sat_name_ssc_map.keys()) - satellite_loop_round
                estimated_runtime = current_runtime + time_for_one_check * satellites_checks_left
                print(f"Runtime: {current_runtime} | Estimated runtime until next constellation check {estimated_runtime}")

                # Set animation time to target time to have visual feedback
                set_animation_time(stk_interface, time_window_start, target_time)

                # Calculate distances
                AtoD = None
                AtoD_aer = stk_interface.get_aer_report_data(attacker, satellite_object)
                if AtoD_aer:
                    if target_time in AtoD_aer.keys():
                        AtoD = AtoD_aer[target_time] * 1000  # we want it in m
                if not AtoD:
                    # Defender not in range of attacker
                    continue

                DtoV = None
                DtoV_aer = stk_interface.get_aer_report_data(satellite_object, victim)
                if DtoV_aer:
                    if target_time in DtoV_aer.keys():
                        DtoV = DtoV_aer[target_time] * 1000  # we want it in m
                if not DtoV:
                    # Victim not in range of defender
                    continue

                # Calculate decision delay in seconds
                AtoV_meters = AtoV * 1000
                decision_delay = decisionDelay(AtoD, DtoV, AtoV_meters, tail_time)

                # Check if satellite could react
                if decision_delay > 0:
                    time_defender_mapping[target_time][satellite_name] = {
                        "AtoV": AtoV,
                        "AtoD": AtoV_meters,
                        "DtoV": DtoV,
                        "decision_delay": decision_delay
                    }

            # Remove satellite from simulation
            stk_interface.remove_satellite(satellite_object)

            # For runtime estimations
            one_check_end = datetime.now()
            time_for_one_check = one_check_end - one_check_start

        # Check if all time points have at least one possible defenders
        number_of_defended_times = 0
        total_number_of_target_times = len(time_defender_mapping.keys())
        for defenders in time_defender_mapping.values():
            if defenders:
                number_of_defended_times += 1

        constellation_time_defender_mapping[constellation_name] = {
            "defended times": number_of_defended_times,
            "not defended times": total_number_of_target_times - number_of_defended_times,
            "defend percentage": (number_of_defended_times/total_number_of_target_times)*100,
            "defenders": time_defender_mapping
        }

    # Time run
    experiment_end = datetime.now()
    print(f"Start: {experiment_start}")
    print(f"End: {experiment_end}")
    print(f"Runtime: {experiment_end - experiment_start}")

    output = {
        "setup": {
            "Attacker": stk_interface.attacker_object.InstanceName,
            "Victim": stk_interface.victim_object.InstanceName,
            "Start time": time_window_start,
            "End time": time_window_end,
            # "Bit rate": bit_rate,
            # "Tail size": tail_size,
            "Tail time": tail_time,
            "Time step size": time_step_size,
            "Number of observations": len(AtoV_time_range_map.keys())
        },
        "runtime": {
            "start": str(experiment_start),
            "end": str(experiment_end),
            "runtime": str(experiment_end - experiment_start)
        },
        "report": constellation_time_defender_mapping
    }

    # Store report
    results_dir = os.path.join(BASE_DIR, "results")
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)

    report_file = os.path.join(results_dir, "report_Exp2.json")
    with open(report_file, "w") as outfile:
        json.dump(output, outfile, indent=1)

    # Cleanup
    stk_interface.cleanup_scenario()


if __name__ == "__main__":
    many_to_one_experiment()
