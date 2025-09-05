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

            if current_time + play_time > end_time:
                break

            end_play_time = current_time + play_time

            pause_duration = generate_random_time(min_pause, max_pause)
            pause_time = timedelta(minutes=pause_duration)

            # Lägg till poolens speltid till schemat (start och sluttid)
            schedule[pool].append({
                "start_time": current_time,
                "end_time": end_play_time,
                "play_duration": play_duration,  # Längden på uppspelningen i minuter
                "pause_duration": pause_duration  # Längden på pausen i minuter
            })

            current_time += play_time + pause_time

            if current_time >= end_time:
                break

    return schedule

# Funktion för att skriva schemat till GUI i det exakta formatet du efterfrågar
def print_schedule(schedule):
    output = ""
    for pool, times in schedule.items():
        output += f"Pool {pool + 1}:\n"  # Lägg till poolens namn/nummer
        for t in times:
            output += f"{t['start_time'].strftime('%H:%M:%S')}-{t['end_time'].strftime('%H:%M:%S')}\n"
        output += "\n"  # Lägg till en tom rad mellan poolerna
    return output



# Funktion för att visa alla tidsintervaller i kronologisk ordning och längden på pauserna
def print_combined_schedule_with_pauses(schedule):
    intervals = []
    
    # Samla alla tidsintervaller från alla pooler
    for pool, times in schedule.items():
        for t in times:
            intervals.append((t['start_time'], t['end_time'], t['play_duration'], t['pause_duration']))
    
    # Sortera tidsintervallerna efter starttid
    intervals.sort(key=lambda x: x[0])

    # Skapa textrepresentationen
    combined_output = ""
    for i, (start, end, play_duration, pause_duration) in enumerate(intervals):
        combined_output += f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({play_duration} min)"
        
        # Lägg till pausens längd om det finns en paus efter
        if i < len(intervals) - 1:
            combined_output += f" | Paus: {pause_duration} min\n"
        else:
            combined_output += "\n"

    return combined_output

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

        # Validering: min- och maxvärden
        if min_play > max_play:
            raise ValueError("Minsta spellängd kan inte vara större än största spellängd.")
        if min_pause > max_pause:
            raise ValueError("Minsta paustid kan inte vara större än största paustid.")
        if pool_count <= 0:
            raise ValueError("Antal ljudpooler måste vara större än 0.")

        # Konvertera start- och sluttid till datetime-objekt
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")

        # Validering: starttid måste vara tidigare än sluttid
        if start_time >= end_time:
            raise ValueError("Starttiden måste vara tidigare än sluttiden.")

        # Generera schemat
        schedule = generate_schedule(start_time, end_time, min_play, max_play, min_pause, max_pause, pool_count)

        # Skriv ut schemat i textområdet (i det exakta formatet)
        schedule_output = print_schedule(schedule)
        text_output.delete(1.0, tk.END)  # Rensa tidigare utdata
        text_output.insert(tk.END, schedule_output)

        # Skriv ut sammanlagt schema med längd på uppspelning och pauser
        combined_output = print_combined_schedule_with_pauses(schedule)
        combined_output_text.delete(1.0, tk.END)  # Rensa tidigare utdata
        combined_output_text.insert(tk.END, combined_output)

    except ValueError as ve:
        messagebox.showerror("Fel", f"Indatafel: {str(ve)}")
    except Exception as e:
        messagebox.showerror("Fel", f"Ett oväntat fel uppstod: {str(e)}")

def clear_fields():
    entry_start_time.delete(0, tk.END)
    entry_end_time.delete(0, tk.END)
    entry_min_play.delete(0, tk.END)
    entry_max_play.delete(0, tk.END)
    entry_min_pause.delete(0, tk.END)
    entry_max_pause.delete(0, tk.END)
    entry_pool_count.delete(0, tk.END)
    text_output.delete(1.0, tk.END)  # Töm textfältet för schemat
    combined_output_text.delete(1.0, tk.END)  # Töm textfältet för kombinerad output


# Skapa GUI med Tkinter
root = tk.Tk()
root.title("Ljudpool Schemagenerator")

# Justera fönsterstorleken
root.geometry("500x800")  # Storleken på huvudfönstret

# Konfigurera rutorna för att göra layouten flexibel
root.grid_rowconfigure(8, weight=1)  # Låt rad 8 ta extra utrymme vertikalt
root.grid_rowconfigure(9, weight=1)  # Låt rad 9 ta extra utrymme vertikalt
root.grid_columnconfigure(0, weight=1)  # Låt kolumn 0 ta upp extra utrymme horisontellt
root.grid_columnconfigure(1, weight=1)  # Låt kolumn 1 ta upp extra utrymme horisontellt

# GUI-komponenter
label_start_time = tk.Label(root, text="Starttid (HH:MM):")
label_end_time = tk.Label(root, text="Sluttid (HH:MM):")
label_min_play = tk.Label(root, text="Minsta spellängd (min):")
label_max_play = tk.Label(root, text="Största spellängd (min):")
label_min_pause = tk.Label(root, text="Minsta paustid (min):")
label_max_pause = tk.Label(root, text="Största paustid (min):")
label_pool_count = tk.Label(root, text="Antal ljudpooler:")

entry_start_time = tk.Entry(root, width=10)
entry_end_time = tk.Entry(root, width=10)
entry_min_play = tk.Entry(root, width=10)
entry_max_play = tk.Entry(root, width=10)
entry_min_pause = tk.Entry(root, width=10)
entry_max_pause = tk.Entry(root, width=10)
entry_pool_count = tk.Entry(root, width=10)

# Layout med grid
label_start_time.grid(row=0, column=0, padx=5, pady=2, sticky='e')
entry_start_time.grid(row=0, column=1, padx=5, pady=2, sticky='w')
label_end_time.grid(row=1, column=0, padx=5, pady=2, sticky='e')
entry_end_time.grid(row=1, column=1, padx=5, pady=2, sticky='w')
label_min_play.grid(row=2, column=0, padx=5, pady=2, sticky='e')
entry_min_play.grid(row=2, column=1, padx=5, pady=2, sticky='w')
label_max_play.grid(row=3, column=0, padx=5, pady=2, sticky='e')
entry_max_play.grid(row=3, column=1, padx=5, pady=2, sticky='w')
label_min_pause.grid(row=4, column=0, padx=5, pady=2, sticky='e')
entry_min_pause.grid(row=4, column=1, padx=5, pady=2, sticky='w')
label_max_pause.grid(row=5, column=0, padx=5, pady=2, sticky='e')
entry_max_pause.grid(row=5, column=1, padx=5, pady=2, sticky='w')
label_pool_count.grid(row=6, column=0, padx=5, pady=2, sticky='e')
entry_pool_count.grid(row=6, column=1, padx=5, pady=2, sticky='w')

# Symmetriska knappar
button_generate = tk.Button(root, text="Generera schema", command=generate)
button_generate.grid(row=7, column=0, padx=5, pady=10, sticky='ew')

button_clear = tk.Button(root, text="Töm", command=clear_fields)
button_clear.grid(row=7, column=1, padx=5, pady=10, sticky='ew')

# Textfält för att visa schemat (i det exakta formatet)
text_output = tk.Text(root, height=12, width=60)
text_output.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

# Textfält för att visa det sammanlagda schemat med uppspelningstider och pauser
combined_output_text = tk.Text(root, height=12, width=60)
combined_output_text.grid(row=9, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

# Starta GUI-loop
root.mainloop()
