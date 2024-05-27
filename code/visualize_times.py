from matplotlib import pyplot as plt, transforms
from matplotlib.collections import PolyCollection

from decision_window_calc import *

graph_scale = 1000

# Initial tail arrival times
attacker_starts_sending_tail = 0

tail_victim_start_arrival = time(AtoV)
tail_defender_start_arrival = time(AtoD)

tail_victim_arrival_window = (attacker_starts_sending_tail, attacker_starts_sending_tail + tail_victim_start_arrival)
tail_defender_arrival_window = (
    attacker_starts_sending_tail, attacker_starts_sending_tail + tail_defender_start_arrival)

# Tail full arrival window
tail_victim_end_arrival = attacker_starts_sending_tail + tail_victim_start_arrival + tail_time

full_tail_victim_arrival_window = (tail_victim_arrival_window[1], tail_victim_end_arrival)

# Defender to Victim signal delay
defender_latest_jamming_start = tail_victim_end_arrival - time(DtoV)

defender_latest_jamming_arrival_window = (defender_latest_jamming_start, tail_victim_end_arrival)

# Decision Window
defender_decision_window = (tail_defender_arrival_window[1], defender_latest_jamming_start)

graph_bars = {
    1: {
        "name": "Victim\nProcessing",
        "color": "black",
        "bars": {
            "Tail arrival window": full_tail_victim_arrival_window
        }
    },
    2: {
        "name": "Defender\nProcessing",
        "color": "black",
        "bars": {
            "Decision Window": defender_decision_window
        }
    },
    3: {
        "name": "Defender\nto\nVictim",
        "color": "black",
        "bars": {
            "Signal \n Delay": defender_latest_jamming_arrival_window
        }
    },
    4: {
        "name": "Attacker\nto\nVictim",
        "color": "black",
        "bars": {
            "Tail start arrival delay": tail_victim_arrival_window
        }
    },
    5: {
        "name": "Attacker\nto\nDefender",
        "color": "black",
        "bars": {
            "Tail start arrival delay": tail_defender_arrival_window
        }
    }
}

verts = []
colors = []

for id in graph_bars.keys():
    values = graph_bars[id]
    v = []
    for window in values["bars"].values():
        # Add a box
        v.append((window[0] * graph_scale, id - .4))
        v.append((window[0] * graph_scale, id + .4))
        v.append((window[1] * graph_scale, id + .4))
        v.append((window[1] * graph_scale, id - .4))
        v.append((window[0] * graph_scale, id - .4))

    verts.append(v)
    colors.append(values["color"])

bars = PolyCollection(verts, facecolors=colors)

fig, ax = plt.subplots()
ax.add_collection(bars)
ax.autoscale()

# Add x labels
x_points = {
    0: "0ms \n Attacker starts\n sending tail",
    tail_victim_start_arrival * graph_scale: f"{round(tail_victim_start_arrival * 1000, 2)}ms \n Victim starts\n receiving",
    tail_defender_start_arrival * graph_scale: f"{round(tail_defender_start_arrival * 1000, 2)}ms \n Defender starts\n receiving",
    tail_victim_end_arrival * graph_scale: f"{round(tail_victim_end_arrival * 1000, 2)}ms \n Tails was\n received entirely",
    defender_latest_jamming_start * graph_scale: f"{round(defender_latest_jamming_start * 1000, 2)}ms \n Latest jamming\n start time"
}
plt.xticks(list(x_points.keys()), list(x_points.values()))
plt.xticks(rotation=45, fontsize=9)

# Add y labels
ax.set_yticks(list(graph_bars.keys()))
ax.set_yticklabels([value["name"] for value in graph_bars.values()])
plt.yticks(fontsize=10)

# apply offset transform to all x tick that overlaps
dx, dy = -15/72, 0/72.
offset = transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
label = ax.xaxis.get_majorticklabels()[4]
label.set_transform(label.get_transform() + offset)

# Add text
for id in graph_bars.keys():
    values = graph_bars[id]
    v = []
    for name in values["bars"].keys():
        window = values["bars"][name]
        x = (window[0] * graph_scale + window[1] * graph_scale) / 2
        y = id
        time_window = round((window[1] - window[0]) * 1000, 2)
        label = f"{name} \n {time_window}ms"
        plt.text(x, y, label, horizontalalignment="center", verticalalignment="center", weight='bold', fontsize=7, color="white")

fig.set_figwidth(7)

plt.subplots_adjust(bottom=0.3, left=0.12)
plt.savefig('TimeWindow.pdf')
#plt.show()
