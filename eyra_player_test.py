import subprocess
import os

# Sökväg till Eyra Player
EYRA_PLAYER_PATH = "/Users/stefanbackas/Documents/000_EYRA/Kod/EyraPlayer_v0_565.py"

# Sökväg till config
CONFIG_PATH = "/Users/stefanbackas/Documents/000_EYRA/Eyra Soundscapes/Eyra_Home_General_Mixed_v1.0_CONFIG.json"

# Kör Eyra Player som bakgrundsprocess
subprocess.Popen(["python3", EYRA_PLAYER_PATH, CONFIG_PATH])

print("🎧 Eyra Player har startat.")
