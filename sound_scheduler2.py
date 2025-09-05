import random
from datetime import datetime, timedelta

# Funktion för att generera slumpmässiga tider inom ett intervall
def generate_random_time(min_time, max_time):
    return random.randint(min_time, max_time)

# Funktion för att generera hela schemat
def generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count):
    current_time = start_time
    schedule = []

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

            # Lägg till poolens speltid till schemat
            schedule.append({
                "pool": pool + 1,
                "start_time": current_time.strftime("%H:%M"),
                "play_duration": play_duration,
                "pause_duration": pause_duration
            })

            # Uppdatera tiden efter speltiden och pausen
            current_time += play_time + pause_time

            # Kontrollera igen att vi inte överstiger sluttiden
            if current_time >= end_time:
                break

    return schedule

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

# Skriv ut schemat
print("\nGenererat schema:")
for entry in schedule:
    print(f"Pool {entry['pool']} spelar från {entry['start_time']} i {entry['play_duration']} minuter, paus i {entry['pause_duration']} minuter.")
