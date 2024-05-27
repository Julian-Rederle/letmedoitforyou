## Experiment 1: One-on-one protection

### Settings

You can play with the following settings:

- `target_time`: a string representation of the point in time when the attacker starts sending the tail in a valid STK
  format. We recommend looking at the example in the example experiment we provide.
- `bit_rate`: In bits per second, see the paper for further details
- `celestrak_file`: This is the database of satellites to consider in the experiment. The scripts maps each satellite to
  their SSC number. If this SSC number is invalid STK will not be able to simulate this satellite properly. If the
  database file doesn't have the common CelesTrak (JSON) format, the script will not be able to parse it correctly. You can get
  their database [here](https://www.celestrak.org/NORAD/elements/). We recommend downloading the "Active Satellites"
  database that we also used in our runs of the experiment.

### Run it!

1. Start up STK with the scenario in `STK/STK_Exp1/`. (Or a custom one)
2. Run the following command
```bash
python experiment1.py
```

### Output

The script will output `results/report_Exp1.json` containing information about the run and details about the proximity 
of each potential protector and the respective decision delay.

## Experiment 2: Protection as a service offered by constellations

### Settings

You can play with the following settings:

- `time_window_start` and `time_window_end`: String representations that describe the start and end time of the
- experiment in a valid STK format. We recommend looking at the example in the sample experiment provided by us.
- `bit_rate`: In bits per second, see the paper for further details
- `celestrak_file`: This is the database of satellites to consider in the experiment. The scripts maps each satellite to
  their SSC number. If this SSC number is invalid STK will not be able to simulate this satellite properly. If the
  database file doesn't have the common CelesTrak (JSON) format, the script will not be able to parse it correctly. You can get
  their database [here](https://www.celestrak.org/NORAD/elements/). We recommend downloading the "Active Satellites"
  database that we also used in our runs of the experiment.
- `CONSTELLATIONS`: A list of constellation names. Since we went the lazy route and didn't want to define every single satellite and the satellites of a constellation usually contain the name of the constellation, you should search the CelesTrak database file for the common name for a constellation. The script will then check the database file and select all satellites that contain the name of the constellation
- `time_step_size`: How many seconds elapse between the measuring points during the experiments time window

### Run it!

1. Start up STK with the scenario in `STK/STK_Exp2/`.
2. Run the following command
```bash
python experiment2.py
```

### Output

he script will output `results/report_Exp2.json` containing information about the run and details about the proximity 
of each potential protector and the respective decision delay at each measuring point.

## Additional: Plot time windows

### Settings

You can play with the following settings in `decision_window_calc.py`:

- `bit_rate`: In bits per second
- `tail_size`: Size of the tail in bits 
- `AtoV`: Distance between attacker and victim in metres
- `AtoD`: Distance between attacker and defender in metres
- `DtoV`: Distance between defender and defender in metres

See the paper for further details!

### Run it!

```bash
python visualize_times.py
```

### Output
The script outputs a file with the name `TimeWindow.pdf`, which contains a visualisation of the time windows.


# Note
The scripts require a prefabricated STK scenario with at least two objects. Each object should be either a satellite or 
a facility (simulates a ground station). The name of the two objects does not matter as long as they contain the 
string attacker or victim so that the script can recognise them automatically. There is no need to add any sensors or 
similar, as our model assumes that the objects always have the necessary equipment to perform all actions. The analysis
period can be set arbitrarily as long as it encloses the target time explained later. We recommend keeping the 
analysis time window small.

Leave your STK running with your scenario while you run the script, as the script will try to connect to the STK 
instance during the experiment.