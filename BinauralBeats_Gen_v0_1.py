from pydub.generators import Sine
from pydub import AudioSegment
from pydub.playback import play

def create_binaural_beats(frequency_left=440, frequency_right=445, duration_ms=5000):
    """
    Skapar binaural beats genom att generera två sinusvågor med olika frekvenser.
    
    :param frequency_left: Frekvensen för vänster kanal (i Hz)
    :param frequency_right: Frekvensen för höger kanal (i Hz)
    :param duration_ms: Längden på ljudet (i millisekunder)
    :return: AudioSegment med binaural beats
    """
    # Skapa vänster kanal med en frekvens
    left_tone = Sine(frequency_left).to_audio_segment(duration=duration_ms)
    
    # Skapa höger kanal med en annan frekvens
    right_tone = Sine(frequency_right).to_audio_segment(duration=duration_ms)
    
    # Kombinera tonerna till stereokanaler (vänster och höger)
    binaural_beats = AudioSegment.from_mono_audiosegments(left_tone, right_tone)
    
    return binaural_beats

# Generera binaural beats (440 Hz i vänster öra och 445 Hz i höger öra)
binaural = create_binaural_beats(440, 445, duration_ms=10000)  # 10 sekunder

# Spela upp ljudet
play(binaural)
