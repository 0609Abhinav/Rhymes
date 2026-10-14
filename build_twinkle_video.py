import os
import glob
import subprocess
import numpy as np
import cv2
from PIL import Image
import imageio_ffmpeg

KEYFRAMES_DIR = r"c:\Users\HP\Downloads\video generator\keyframes"
OUTPUT_DIR = r"c:\Users\HP\Downloads\video generator"
AUDIO_PATH = os.path.join(OUTPUT_DIR, "lullaby_soundtrack.wav")
TEMP_VIDEO_PATH = os.path.join(OUTPUT_DIR, "temp_video.mp4")
FINAL_VIDEO_PATH = os.path.join(OUTPUT_DIR, "Twinkle_Twinkle_Little_Star_3D.mp4")

WIDTH = 1280
HEIGHT = 720
FPS = 24
SCENE_DURATION = 8.0 # seconds
NUM_SCENES = 10
TOTAL_DURATION = SCENE_DURATION * NUM_SCENES # 80.0s
FADE_DURATION = 1.0 # cross-dissolve seconds
SAMPLE_RATE = 44100

def find_image(pattern):
    matches = glob.glob(os.path.join(KEYFRAMES_DIR, pattern))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Pattern {pattern} not found in {KEYFRAMES_DIR}")

# 1. Synthesize gentle lullaby soundtrack (Music Box, Glockenspiel, Concert Harp)
def generate_lullaby_audio():
    print("Generating gentle lullaby music box soundtrack (90 BPM)...")
    total_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    audio = np.zeros(total_samples, dtype=np.float32)

    bpm = 90.0
    beat_dur = 60.0 / bpm # ~0.6667s

    # Note frequencies (Hz)
    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
        'C6': 1046.50
    }

    def synth_bell(freq, duration, volume=0.3, is_harp=False):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        if is_harp:
            decay = np.exp(-t * 2.5)
            wave = (np.sin(2 * np.pi * freq * t) +
                    0.5 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 4.0) +
                    0.25 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 6.0))
        else: # Music box / Glockenspiel
            decay = np.exp(-t * 3.5)
            # Metallic glockenspiel overtone ratios
            wave = (np.sin(2 * np.pi * freq * t) +
                    0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6.0) +
                    0.2 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 9.0))
        return (wave * decay * volume).astype(np.float32)

    def add_note(name, start_time, dur, vol=0.3, is_harp=False):
        if name not in notes:
            return
        freq = notes[name]
        tone = synth_bell(freq, dur * 2.2, volume=vol, is_harp=is_harp)
        start_idx = int(start_time * SAMPLE_RATE)
        end_idx = min(start_idx + len(tone), total_samples)
        available = end_idx - start_idx
        if available > 0:
            audio[start_idx:end_idx] += tone[:available]

    # Nursery rhyme melody:
    # Phrase A: C C G G A A G (2 beats each, except last note 4 beats)
    # Phrase B: F F E E D D C
    # Phrase C: G G F F E E D
    # Phrase D: G G F F E E D
    # Phrase E: C C G G A A G
    # Phrase F: F F E E D D C
    melody = [
        # (note, beat_duration)
        ('C5', 1), ('C5', 1), ('G5', 1), ('G5', 1), ('A5', 1), ('A5', 1), ('G5', 2),
        ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 1), ('D5', 1), ('C5', 2),
        ('G5', 1), ('G5', 1), ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 2),
        ('G5', 1), ('G5', 1), ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 2),
        ('C5', 1), ('C5', 1), ('G5', 1), ('G5', 1), ('A5', 1), ('A5', 1), ('G5', 2),
        ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 1), ('D5', 1), ('C5', 2),
    ]

    # Verse repeats across 80 seconds (each cycle is 48 beats = 32s)
    current_time = 1.0 # 1s intro chime
    # Intro sparkle chime
    add_note('C6', 0.2, 1.5, 0.25, is_harp=True)
    add_note('G5', 0.5, 1.5, 0.2, is_harp=True)
    add_note('E5', 0.8, 1.5, 0.2, is_harp=True)

    while current_time < TOTAL_DURATION - 4.0:
        for note, length in melody:
            if current_time >= TOTAL_DURATION - 3.0:
                break
            # Glockenspiel / Music box lead
            add_note(note, current_time, length * beat_dur, vol=0.35)
            # Gentle soft harp bass accompaniment
            if length >= 2 or (current_time % (beat_dur * 2) < 0.1):
                base_note = 'C4' if 'C' in note else ('G4' if 'G' in note else 'F4')
                add_note(base_note, current_time, 2.0, vol=0.2, is_harp=True)
            current_time += length * beat_dur

    # Gentle outro
    add_note('C5', TOTAL_DURATION - 2.5, 3.0, vol=0.25)
    add_note('G4', TOTAL_DURATION - 2.2, 3.0, vol=0.2, is_harp=True)
    add_note('E4', TOTAL_DURATION - 1.9, 3.0, vol=0.2, is_harp=True)
    add_note('C4', TOTAL_DURATION - 1.6, 4.0, vol=0.2, is_harp=True)

    # Soft ambient reverb simulation (simple FIR echo decay)
    delay_samples = int(SAMPLE_RATE * 0.22)
    reverb_audio = np.copy(audio)
    reverb_audio[delay_samples:] += audio[:-delay_samples] * 0.35
    delay_samples2 = int(SAMPLE_RATE * 0.44)
    reverb_audio[delay_samples2:] += audio[:-delay_samples2] * 0.18

    # Normalize gently
    max_val = np.max(np.abs(reverb_audio))
    if max_val > 0:
        reverb_audio = (reverb_audio / max_val) * 0.85

    # Export 16-bit PCM wav
    pcm16 = (reverb_audio * 32767).astype(np.int16)
    import wave
    with wave.open(AUDIO_PATH, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm16.tobytes())
    print(f"Audio saved to {AUDIO_PATH}")

def load_and_prep_images():
    scene_patterns = [
        "scene1_windowsill*.jpg",
        "scene2_cloud_stars*.jpg",
        "scene3_sunset*.jpg",
        "scene4_night_dance*.jpg",
        "scene5_fox_lantern*.jpg",
        "scene6_fork_path*.jpg",
        "scene7_cozy_bed*.jpg",
        "scene8_sunrise_yawn*.jpg",
        "scene9_starry_hill*.jpg",
        "scene10_cloud_wave*.jpg"
    ]
    imgs = []
    for pat in scene_patterns:
        path = find_image(pat)
        print(f"Loading scene: {os.path.basename(path)}")
        img = cv2.imread(path)
        img = cv2.resize(img, (WIDTH, HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        imgs.append(img)
    return imgs

def generate_scene_frame(img, progress, scene_idx):
    # Progress: 0.0 to 1.0
    # Apply subtle, gentle, toddler-friendly cinematic camera motion
    h, w = img.shape[:2]
    
    if scene_idx == 0: # Scene 1: Slow push-in toward Pip
        zoom = 1.0 + 0.08 * progress
        cx, cy = 0.52 * w, 0.48 * h
    elif scene_idx == 1: # Scene 2: Gentle float up and drift right
        zoom = 1.0 + 0.06 * progress
        cx = (0.50 + 0.04 * progress) * w
        cy = (0.50 - 0.03 * progress) * h
    elif scene_idx == 2: # Scene 3: Pan slowly right toward the waving bunny
        zoom = 1.04
        cx = (0.45 + 0.08 * progress) * w
        cy = 0.50 * h
    elif scene_idx == 3: # Scene 4: Soft toddler sway / breathing pulse
        sway = np.sin(progress * np.pi * 2) * 0.02
        zoom = 1.04 + sway
        cx, cy = 0.50 * w, 0.50 * h
    elif scene_idx == 4: # Scene 5: Tracking right along Fox's lantern path
        zoom = 1.05
        cx = (0.46 + 0.07 * progress) * w
        cy = 0.50 * h
    elif scene_idx == 5: # Scene 6: Slow pull back revealing the sparkling trail
        zoom = 1.08 - 0.06 * progress
        cx, cy = 0.50 * w, 0.50 * h
    elif scene_idx == 6: # Scene 7: Gentle slow push-in to cozy bed & wink
        zoom = 1.0 + 0.07 * progress
        cx = (0.48 + 0.03 * progress) * w
        cy = 0.52 * h
    elif scene_idx == 7: # Scene 8: Pan slowly across village to morning sunrise
        zoom = 1.05
        cx = (0.45 + 0.08 * progress) * w
        cy = (0.50 - 0.02 * progress) * h
    elif scene_idx == 8: # Scene 9: Soft orbital float around the two friends
        angle_shift = np.sin(progress * np.pi) * 0.02
        zoom = 1.03 + 0.04 * progress
        cx = (0.50 + angle_shift) * w
        cy = 0.50 * h
    else: # Scene 10: Grand slow cinematic pull-back (zoom out) into the stars
        zoom = 1.10 - 0.09 * progress
        cx, cy = 0.50 * w, 0.50 * h

    crop_w = int(w / zoom)
    crop_h = int(h / zoom)
    x1 = max(0, min(w - crop_w, int(cx - crop_w / 2)))
    y1 = max(0, min(h - crop_h, int(cy - crop_h / 2)))
    
    cropped = img[y1:y1+crop_h, x1:x1+crop_w]
    frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    # Fade to black at very end of scene 10
    if scene_idx == 9 and progress > 0.85:
        fade_out = 1.0 - (progress - 0.85) / 0.15
        frame = (frame * fade_out).astype(np.uint8)

    return frame

def render_video():
    images = load_and_prep_images()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(TEMP_VIDEO_PATH, fourcc, FPS, (WIDTH, HEIGHT))

    frames_per_scene = int(SCENE_DURATION * FPS) # 192 frames
    fade_frames = int(FADE_DURATION * FPS) # 24 frames

    print(f"Rendering {NUM_SCENES} scenes ({frames_per_scene * NUM_SCENES} total frames)...")

    for s in range(NUM_SCENES):
        print(f"Rendering Scene {s+1}/{NUM_SCENES}...")
        for f in range(frames_per_scene):
            prog = f / float(frames_per_scene)
            current_frame = generate_scene_frame(images[s], prog, s)

            # Cross-dissolve into next scene during the last fade_frames
            if s < NUM_SCENES - 1 and f >= (frames_per_scene - fade_frames):
                alpha = (f - (frames_per_scene - fade_frames)) / float(fade_frames)
                next_prog = (f - (frames_per_scene - fade_frames)) / float(frames_per_scene)
                next_frame = generate_scene_frame(images[s+1], next_prog, s+1)
                final_frame = cv2.addWeighted(current_frame, 1.0 - alpha, next_frame, alpha, 0)
            else:
                final_frame = current_frame

            out.write(final_frame)

    out.release()
    print(f"Video track written to {TEMP_VIDEO_PATH}")

def mux_final_video():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"Muxing audio and video with ffmpeg ({ffmpeg_exe})...")
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", TEMP_VIDEO_PATH,
        "-i", AUDIO_PATH,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_VIDEO_PATH
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(TEMP_VIDEO_PATH):
        os.remove(TEMP_VIDEO_PATH)
    print(f"SUCCESS! Finished video: {FINAL_VIDEO_PATH}")

if __name__ == "__main__":
    generate_lullaby_audio()
    render_video()
    mux_final_video()
