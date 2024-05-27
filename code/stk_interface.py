import datetime
import re
import string

from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import AgESTKObjectType, AgEVePropagatorType


class STKInterface:
    stk_date_format = "%d %b %Y %H:%M:%S.%f"
    stk_date_regex = re.compile(r"^(\d{1,2}\s[A-Z][a-z]{2}\s\d{4} \d{2}:\d{2}:)(\d{2}\.\d{1,})$")

    def __init__(self, cleanup=True):
        # STK management
        self.stk = STKDesktop.AttachToApplication()
        self.root = self.stk.Root
        self.scenario = self.root.CurrentScenario

        if not self.scenario:
            print("Either the scenario is not opened in STK or STK has a hiccup and needs to be restarted.")
            self.cleanup = False  # so no error occurs
            exit(1)

        # Assumes that the names of the objects contain the word attacker/victim
        self.attacker_object = None
        self.victim_object = None
        self.find_attacker_and_victim()

        # Defender dynamically changes during experiment
        self.defender = None

        self.added_satellites = []

        # De-/Activate cleanup
        self.cleanup = cleanup

        # Add constellation map
        self.constellations = {}

    def __del__(self):
        if self.cleanup:
            self.cleanup_scenario()

    def find_attacker_and_victim(self):
        """
        Scans all objects in the scenario and finds victims and attackers
        :return: None
        """
        scenario_objects = self.scenario.Children

        for scenario_object in scenario_objects:
            object_name = scenario_object.InstanceName

            # Set attacker object
            if "attacker" in object_name.lower():
                self.attacker_object = scenario_object

            # Set victim object
            if "victim" in object_name.lower():
                self.victim_object = scenario_object

        if not (self.attacker_object):
            print("Attacker not found! Did you forget to add object with 'attacker' in name?")
            exit(1)

        if not (self.victim_object):
            print("Victim not found! Did you forget to add object with 'victim' in name?")
            exit(1)

    def cleanup_scenario(self):
        for satellite in self.added_satellites:
            self.remove_satellite(satellite)

    def convert_name(self, satellite_name):
        satellite_name = satellite_name.replace(" ", "_")
        allowed_chars = string.ascii_letters + string.digits + "_"

        satellite_name = "".join(filter(lambda c: c in allowed_chars, list(satellite_name)))
        return satellite_name

    def through_away_milliseconds(self, time):
        time_datetime = self.stk_date_to_datetime(time)
        time_datetime = time_datetime.replace(microsecond=0)
        return self.datetime_to_stk_date(time_datetime)

    def get_aer_report_data(self, object1, object2, step_size=10) -> dict[str, str]:
        """

        :param object1: Can be the path of the object or the object itself
        :param object2: Can be the path of the object or the object itself
        :param step_size:
        :return: mapping from time to range in km
        """

        # If object is provided instead of path, convert to path
        if type(object1) is not str:
            object1 = object1.Path

        if type(object2) is not str:
            object2 = object2.Path

        # Create access
        access_report = self.scenario.GetAccessBetweenObjectsByPath(object1, object2)

        # Create AER report
        aer_report = access_report.DataProviders.Item('AER Data')  # Don't ask

        # Take the default one (Options: Default, VVLH CBI, VVLH CBF, BodyFixed, NorthEastDown)
        default_aer_report = aer_report.Group.GetItemByName("Default")

        # Trigger actual simulation calculations of report
        executed_aer = default_aer_report.Exec(self.scenario.StartTime, self.scenario.StopTime, step_size)
        number_of_intervals = executed_aer.Intervals.Count

        times = []
        ranges = []

        # Iterate over all Access time slot
        for i in range(number_of_intervals):
            # Take values from report
            executed_aer_dataset = executed_aer.Intervals.Item(i).DataSets

            if "Time" in executed_aer_dataset.ElementNames:
                times += executed_aer_dataset.GetDataSetByName('Time').GetValues()
            else:
                # Out of range
                return {}

            if "Range" in executed_aer_dataset.ElementNames:
                ranges += executed_aer_dataset.GetDataSetByName('Range').GetValues()
            else:
                # Out of range
                return {}

        # Filter out milliseconds, because stk not always does clean jumps in access reports
        times = [self.through_away_milliseconds(t) for t in times]

        return dict(zip(times, ranges))

    def add_constellation(self, constellation_name, sat_name_ssc_map: dict[str, str]) -> dict[
        str, AgESTKObjectType.eSatellite]:
        satellites_in_constellation = {}

        for satellite_name, ssc_number in sat_name_ssc_map.items():
            stk_satellite_name = self.convert_name(satellite_name)
            satellite = self.add_satellite(stk_satellite_name, ssc_number)
            satellites_in_constellation[satellite_name] = satellite

        self.constellations[constellation_name] = satellites_in_constellation

        return satellites_in_constellation

    def add_satellite(self, satellite_name: str, ssc_number: str) -> AgESTKObjectType.eSatellite:
        # Remove satellite with same name if exists
        self.remove_duplicates(satellite_name)

        # Create satellite
        satellite = self.scenario.Children.New(AgESTKObjectType.eSatellite, satellite_name)

        # Get propagator
        satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorSGP4)
        propagator = satellite.Propagator
        propagator.Step = 60.0

        # Set SCC number
        propagator.CommonTasks.AddSegsFromOnlineSource(ssc_number)
        propagator.Propagate()

        # Add to newly added satellite list
        self.added_satellites.append(satellite)

        return satellite

    def remove_duplicates(self, satellite_name):
        scenario_objects = self.scenario.Children

        for scenario_object in scenario_objects:
            object_name = scenario_object.InstanceName
            if object_name == satellite_name:
                self.remove_satellite(scenario_object)

    def remove_satellite(self, satellite: AgESTKObjectType.eSatellite) -> None:
        if satellite in self.added_satellites:
            self.added_satellites.remove(satellite)
        satellite.Unload()

    def stk_date_to_datetime(self, s: str) -> datetime.datetime:
        truncate_to_microseconds = lambda match: f"{match.group(1)}{round(float(match.group(2)), 6)}"
        return datetime.datetime.strptime(re.sub(self.stk_date_regex, truncate_to_microseconds, s),
                                          self.stk_date_format)

    def datetime_to_stk_date(self, d: datetime.datetime) -> str:
        return d.strftime(self.stk_date_format)


def main():
    stk_interface = STKInterface()
    attacker_object = stk_interface.attacker_object
    victim_object = stk_interface.victim_object

    accesses = stk_interface.get_aer_report_data(attacker_object, victim_object)

    for time, range in accesses.items():
        print(time, range)


if __name__ == "__main__":
    main()
