import scipy

bit_rate = 9600  # in bits per second
tail_size = 6 * 8
tail_time = 1 / bit_rate * tail_size
# attacker to victim distance (m)
AtoV = 700 * 1000

# attacker to defender distance (m)
AtoD = 1000 * 1000

# Defender to victim distance (m)
DtoV = 200 * 1000


# function to calculate the time it takes for a signal to propagate (seconds)
def time(distance):
    return distance / scipy.constants.speed_of_light


def decisionDelay(AtoD, DtoV, AtoV, tailtime):
    # Defender receives beginning of tail before Victim -> advantage, offset is positive
    # Defender receives beginning of tail after Victim  -> disadvantage, offset is negative
    # In defender advantage chase: time(AtoD) < time(AtoV)
    defender_offset = time(AtoV) - time(AtoD)

    # default delay introduced by signal traveling time from defender to Victim
    # Advantage case subtracts time that the defender receives the signal ahead of Victim
    # Disadvantage case adds time that the defender receives the signal ahead of Victim
    delay = time(DtoV) - defender_offset

    # Tail time is the maximum size that the decision window would be if the Victim and Defender would be at the same
    # position
    # Subtracting the delay shortens the window by accounting for the signal traveling time and defender
    # advantage/disadvantage
    return tailtime - delay


def main():
    decision_delay = decisionDelay(AtoD, DtoV, AtoV, tail_time)
    print(f"Decision delay of {decision_delay*1000}ms")


if __name__ == "__main__":
    main()
