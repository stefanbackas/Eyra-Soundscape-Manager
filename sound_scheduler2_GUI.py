import random
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox

# Funktion för att generera slumpmässiga tider inom ett intervall
def generate_random_time(min_time, max_time):
    return random.randint(min_time, max_time)

# Funktion för att generera hela schemat
def generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count):
    current_time = start_time
    schedule = {pool: [] for pool in range(pool_count)}

    while current_time < end_time:
        for pool in range(pool_count):
            play_duration = generate_random_time(min_play, max_play)
            play_time = timedelta(minutes=play_duration)

            pause_duration = generate_random_time(min_pause, max_pause)
            pause_time = timedelta(minutes=pause_duration)

            if current_time + play_time > end_time:
                break

            end_play_time = current_time + play_time

            # Lägg till poolens speltid till schemat (start och sluttid)
            schedule[pool].append({
                "start_time": current_time.strftime("%H:%M:%S"),
                "end_time": end_play_time.strftime("%H:%M:%S")
            })

            current_time += play_time + pause_time

            if current_time >= end_time:
                break

    return schedule

# Funktion för att skriva schemat till GUI i det specifika formatet
def print_schedule(schedule):
    output = ""
    for pool, times in schedule.items():
        time_sequences = ','.join(f"{t['start_time']}-{t['end_time']}" for t in times)
        output += f'"* * {time_sequences} * * * *"\n'
    return output

# Funktion som körs när användaren klickar på "Generera schema"
def generate():
    try:
        # Hämta indata från GUI och kontrollera om något fält är tomt
        start_time_str = entry_start_time.get()
        end_time_str = entry_end_time.get()
        min_play = entry_min_play.get()
        max_play = entry_max_play.get()
        min_pause = entry_min_pause.get()
        max_pause = entry_max_pause.get()
        pool_count = entry_pool_count.get()

        if not (start_time_str and end_time_str and min_play and max_play and min_pause and max_pause and pool_count):
            raise ValueError("Alla fält måste vara ifyllda.")

        # Konvertera strängar till heltal
        min_play = int(min_play)
        max_play = int(max_play)
        min_pause = int(min_pause)
        max_pause = int(max_pause)
        pool_count = int(pool_count)

        # Konvertera start- och sluttid till datetime-objekt
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")

        # Generera schemat
        schedule = generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count)

        # Skriv ut schemat i textområdet
        schedule_output = print_schedule(schedule)
        text_output.delete(1.0, tk.END)  # Rensa tidigare utdata
        text_output.insert(tk.END, schedule_output)

    except ValueError as ve:
        messagebox.showerror("Fel", f"Indatafel: {str(ve)}")
    except Exception as e:
        messagebox.showerror("Fel", f"Ett oväntat fel uppstod: {str(e)}")

# Skapa GUI med Tkinter
root = tk.Tk()
root.title("Ljudpool Schemagenerator")

# GUI-komponenter
label_start_time = tk.Label(root, text="Starttid (HH:MM):")
label_start_time.grid(row=0, column=0)

entry_start_time = tk.Entry(root)
entry_start_time.grid(row=0, column=1)

label_end_time = tk.Label(root, text="Sluttid (HH:MM):")
label_end_time.grid(row=1, column=0)

entry_end_time = tk.Entry(root)
entry_end_time.grid(row=1, column=1)

label_min_play = tk.Label(root, text="Minsta spellängd (min):")
label_min_play.grid(row=2, column=0)

entry_min_play = tk.Entry(root)
entry_min_play.grid(row=2, column=1)

label_max_play = tk.Label(root, text="Största spellängd (min):")
label_max_play.grid(row=3, column=0)

entry_max_play = tk.Entry(root)
entry_max_play.grid(row=3, column=1)

label_min_pause = tk.Label(root, text="Minsta paustid (min):")
label_min_pause.grid(row=4, column=0)

entry_min_pause = tk.Entry(root)
entry_min_pause.grid(row=4, column=1)

label_max_pause = tk.Label(root, text="Största paustid (min):")
label_max_pause.grid(row=5, column=0)

entry_max_pause = tk.Entry(root)
entry_max_pause.grid(row=5, column=1)

label_pool_count = tk.Label(root, text="Antal ljudpooler:")
label_pool_count.grid(row=6, column=0)

entry_pool_count = tk.Entry(root)
entry_pool_count.grid(row=6, column=1)

# Generera knapp
button_generate = tk.Button(root, text="Generera schema", command=generate)
button_generate.grid(row=7, column=0, columnspan=2)

# Textfält för att visa schemat
text_output = tk.Text(root, height=10, width=50)
text_output.grid(row=8, column=0, columnspan=2)

# Starta GUI-loop
root.mainloop()
