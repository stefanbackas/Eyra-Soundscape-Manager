import random
from datetime import datetime, timedelta

# Funktion för att generera slumpmässiga tider inom ett intervall
def generate_random_time(min_time, max_time):
    return random.randint(min_time, max_time)

# Funktion för att generera hela schemat
def generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count):
    current_time = start_time
    schedule = {pool: [] for pool in range(pool_count)}

    # Fortsätt skapa tider tills vi når sluttiden
    while current_time < end_time:
        for pool in range(pool_count):
            # Generera slumpmässig spellängd
            play_duration = generate_random_time(min_play, max_play)
            play_time = timedelta(minutes=play_duration)

            # Generera slumpmässig paustid
            pause_duration = generate_random_time(min_pause, max_pause)
            pause_time = timedelta(minutes=pause_duration)

            # Kontrollera att nästa spelning inte överstiger sluttiden
            if current_time + play_time > end_time:
                break

            # Sluttiden för poolens spelning
            end_play_time = current_time + play_time

            # Lägg till poolens speltid till schemat
            schedule[pool].append({
                "start_time": current_time.strftime("%H:%M:%S"),
                "end_time": end_play_time.strftime("%H:%M:%S")
            })

            # Uppdatera tiden efter speltiden och pausen
            current_time += play_time + pause_time

            # Kontrollera igen att vi inte överstiger sluttiden
            if current_time >= end_time:
                break

    return schedule

# Funktion för att skriva schemat till terminalen i det specifika formatet
def print_schedule(schedule):
    for pool, times in schedule.items():
        time_sequences = ','.join(f"{t['start_time']}" for t in times)
        print(f'"* * {time_sequences} * * * *"')

# Hämta indata från användaren
start_time_str = input("Ange starttid (HH:MM): ")
end_time_str = input("Ange sluttid (HH:MM): ")
min_play = int(input("Ange minsta spellängd (minuter): "))
max_play = int(input("Ange största spellängd (minuter): "))
min_pause = int(input("Ange minsta paustid (minuter): "))
max_pause = int(input("Ange största paustid (minuter): "))
pool_count = int(input("Ange antal ljudpooler: "))

# Konvertera start- och sluttider till datetime-objekt
start_time = datetime.strptime(start_time_str, "%H:%M")
end_time = datetime.strptime(end_time_str, "%H:%M")

# Generera schemat
schedule = generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count)

# Skriv ut schemat direkt till terminalen i det nya formatet
print("\nKopiera följande scheman för varje pool:\n")
print_schedule(schedule)
