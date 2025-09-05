import os
import random
import time
import pygame
from threading import Thread
from datetime import datetime

class TracklistPlayer(Thread):
    def __init__(self, tracklist, sound_folder, slot_end_time, slotfadetime, crossfadetime):
        super().__init__()
        self.tracklist = tracklist
        self.sound_folder = sound_folder
        self.slot_end_time = slot_end_time
        self.slotfadetime = slotfadetime
        self.crossfadetime = crossfadetime
        self.volume = tracklist.get("volume", 0.1)
        self.randomise = tracklist.get("randomise", False)
        self.running = True
        self.active_channel = None

    def run(self):
        print(f"▶️ Startar Tracklist: {self.tracklist['id']}")
        self.fade_in_slot()

        while self.running:
            file = self.choose_file()
            full_path = os.path.join(self.sound_folder, file)

            try:
                sound = pygame.mixer.Sound(full_path)
                ch1 = sound.play()
                ch1.set_volume(self.volume)
                self.active_channel = ch1

                duration = sound.get_length()

                # Vänta tills det är dags att starta nästa ljud (dur - crossfade)
                wait_time = max(0, duration - self.crossfadetime)
                for _ in range(int(wait_time * 10)):
                    if not self.running or datetime.now().time() > self.slot_end_time:
                        self.fade_out_slot()
                        return
                    time.sleep(0.1)

                # Förbered nästa ljud om tiden tillåter
                if datetime.now().time() >= self.slot_end_time:
                    self.fade_out_slot()
                    return

                next_file = self.choose_file()
                full_path2 = os.path.join(self.sound_folder, next_file)
                sound2 = pygame.mixer.Sound(full_path2)
                ch2 = sound2.play()
                ch2.set_volume(0.0)

                self.crossfade(ch1, ch2)
                self.active_channel = ch2

            except Exception as e:
                print(f"❌ Fel vid uppspelning: {file} → {e}")
                return

    def choose_file(self):
        if self.randomise:
            return random.choice(self.tracklist["items"])
        return self.tracklist["items"][0]

    def fade_in_slot(self):
        print(f"🌅 Fade in slot: {self.tracklist['id']}")
        steps = 20
        step_time = self.slotfadetime / steps
        for i in range(steps):
            pygame.mixer.music.set_volume((i + 1) / steps * self.volume)
            time.sleep(step_time)

    def fade_out_slot(self):
        print(f"🌇 Fade out slot: {self.tracklist['id']}")
        if self.active_channel:
            steps = 20
            start_volume = self.active_channel.get_volume()
            step_time = self.slotfadetime / steps
            for i in range(steps):
                v = start_volume * (1 - (i + 1) / steps)
                self.active_channel.set_volume(v)
                time.sleep(step_time)
            self.active_channel.stop()

    def crossfade(self, ch_out, ch_in):
        print(f"🔀 Crossfade: {self.tracklist['id']}")
        steps = 20
        step_time = self.crossfadetime / steps
        for i in range(steps):
            if not self.running:
                return
            v_in = (i + 1) / steps * self.volume
            v_out = self.volume * (1 - (i + 1) / steps)
            ch_in.set_volume(v_in)
            ch_out.set_volume(v_out)
            time.sleep(step_time)

    def stop(self):
        print(f"🛑 Stoppar Tracklist: {self.tracklist['id']}")
        self.running = False
        self.fade_out_slot()
