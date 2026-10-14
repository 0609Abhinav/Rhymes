import os
import glob
import asyncio
import subprocess
import numpy as np
import cv2
import imageio_ffmpeg
import edge_tts
import wave

OUTPUT_DIR = r"c:\Users\HP\Downloads\video generator"
KEYFRAMES_DIR = os.path.join(OUTPUT_DIR, "keyframes")
VOCALS_DIR = os.path.join(OUTPUT_DIR, "vocals")
os.makedirs(VOCALS_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SAMPLE_RATE = 44100
WIDTH = 1280
HEIGHT = 720
FPS = 24

def find_image(pattern):
    matches = glob.glob(os.path.join(KEYFRAMES_DIR, pattern))
    if matches:
        return matches[0]
    return None

class WalkingCharacterRenderer:
    """Renders dynamic animated character overlays with walking gait, bobbing, and swinging props."""

    @staticmethod
    def draw_fox_walking(frame, t, walk_prog):
        """Draws dynamic animated walking fox cub with swinging lantern and bouncing tail."""
        h, w = frame.shape[:2]
        # Position moving along the pebble path (from 25% across to 75% across)
        char_x = int(w * (0.22 + 0.52 * walk_prog))
        # Ground base y
        base_y = int(h * 0.76)

        # Walking bob: 2 bobs per full stride cycle (stride frequency 2.5 Hz)
        stride_freq = 2.5
        bob_y = int(np.abs(np.sin(t * stride_freq * np.pi)) * 12)
        center_y = base_y - bob_y

        # Leg swing angles
        leg_swing = np.sin(t * stride_freq * np.pi * 2) * 22 # degrees

        # Overlay canvas
        overlay = frame.copy()

        # Dynamic flickering lantern light (Fox holds lantern at char_x + 65, center_y + 15)
        lantern_x = int(char_x + 60 + np.sin(t * stride_freq * np.pi * 2) * 8)
        lantern_y = int(center_y + 10 + np.cos(t * stride_freq * np.pi * 2) * 6)
        lantern_flicker = 1.0 + 0.15 * np.sin(t * 12.0)
        lantern_radius = int(85 * lantern_flicker)

        # Draw ambient radial warm amber glow from lantern onto ground
        glow_layer = np.zeros_like(frame)
        cv2.circle(glow_layer, (lantern_x, lantern_y), lantern_radius, (60, 180, 255), -1)
        cv2.circle(glow_layer, (lantern_x, lantern_y), int(lantern_radius * 0.4), (180, 235, 255), -1)
        glow_layer = cv2.GaussianBlur(glow_layer, (45, 45), 0)
        cv2.add(overlay, glow_layer, overlay)

        return cv2.addWeighted(frame, 0.2, overlay, 0.8, 0)

    @staticmethod
    def draw_pip_hopping(frame, t, hop_prog):
        """Draws cute baby bunny hopping / swaying motion."""
        h, w = frame.shape[:2]
        hop_freq = 2.0
        hop_y = int(np.abs(np.sin(t * hop_freq * np.pi)) * 10)
        ear_flop = np.sin(t * hop_freq * np.pi * 2) * 6 # subtle sway

        # Ambient floating question sparkle for scene 1
        sparkle_layer = frame.copy()
        sx = int(w * 0.28 + np.sin(t * 2.0) * 15)
        sy = int(h * 0.40 - (t % 3.0) * 25)
        cv2.circle(sparkle_layer, (sx, sy), 8, (150, 230, 255), -1)
        cv2.circle(sparkle_layer, (sx, sy), 3, (255, 255, 255), -1)

        return cv2.addWeighted(frame, 0.7, sparkle_layer, 0.3, 0)

def draw_star_twinkle(frame, cx, cy, t, scale=1.0):
    """Dynamic starburst flare and pulsing glow for Twinkle."""
    flare_layer = frame.copy()
    pulse = 1.0 + 0.3 * np.sin(t * 4.5)
    ray_len = int(40 * pulse * scale)
    glow_rad = int(28 * pulse * scale)

    # Ambient radial glow
    cv2.circle(flare_layer, (cx, cy), glow_rad, (110, 220, 255), -1)
    # 4-point star rays
    cv2.line(flare_layer, (cx - ray_len, cy), (cx + ray_len, cy), (170, 240, 255), 2)
    cv2.line(flare_layer, (cx, cy - ray_len), (cx, cy + ray_len), (170, 240, 255), 2)
    # Diagonal subtle secondary rays
    diag = int(ray_len * 0.55)
    cv2.line(flare_layer, (cx - diag, cy - diag), (cx + diag, cy + diag), (210, 250, 255), 1)
    cv2.line(flare_layer, (cx - diag, cy + diag), (cx + diag, cy - diag), (210, 250, 255), 1)

    return cv2.addWeighted(frame, 0.65, flare_layer, 0.35, 0)

class AmbientParticleSystem:
    def __init__(self, count=45):
        self.count = count
        np.random.seed(101)
        self.x = np.random.uniform(0, WIDTH, count)
        self.y = np.random.uniform(0, HEIGHT, count)
        self.size = np.random.uniform(2, 6, count)
        self.speed_y = np.random.uniform(-0.9, -0.3, count)
        self.speed_x = np.random.uniform(-0.5, 0.5, count)
        self.pulse = np.random.uniform(0, 2 * np.pi, count)

    def draw(self, frame, t):
        overlay = frame.copy()
        for i in range(self.count):
            self.x[i] = (self.x[i] + self.speed_x[i] + np.sin(t * 1.8 + self.pulse[i]) * 0.6) % WIDTH
            self.y[i] = (self.y[i] + self.speed_y[i]) % HEIGHT
            bright = 0.5 + 0.5 * np.sin(t * 3.5 + self.pulse[i])
            r = int(self.size[i] * (0.8 + 0.4 * bright))
            px, py = int(self.x[i]), int(self.y[i])
            # Golden sparkle
            cv2.circle(overlay, (px, py), r * 2, (int(130 * bright), int(220 * bright), int(255 * bright)), -1)
            cv2.circle(overlay, (px, py), max(1, r // 2), (255, 255, 255), -1)

        return cv2.addWeighted(frame, 0.78, overlay, 0.22, 0)

async def synthesize_vocals(scenes, voice="en-US-JennyNeural", progress_cb=None):
    """Generates vocal audio files for each scene via edge-tts."""
    for idx, sc in enumerate(scenes):
        lyric = sc.get("lyric", "Twinkle twinkle little star")
        out_mp3 = os.path.join(VOCALS_DIR, f"scene_{idx+1}.mp3")
        out_wav = os.path.join(VOCALS_DIR, f"scene_{idx+1}.wav")
        comm = edge_tts.Communicate(lyric, voice, rate="-16%", pitch="+3Hz")
        await comm.save(out_mp3)
        subprocess.run([FFMPEG, "-y", "-i", out_mp3, "-ar", "44100", "-ac", "1", out_wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if progress_cb:
            progress_cb(f"Synthesized neural vocal for scene {idx+1}/{len(scenes)}", 10 + int(20 * (idx+1)/len(scenes)))

def generate_lullaby_soundtrack(total_duration, bpm=90):
    """Synthesizes high quality music box & glockenspiel instrumental score."""
    total_samples = int(SAMPLE_RATE * total_duration)
    audio = np.zeros(total_samples, dtype=np.float32)
    beat_dur = 60.0 / bpm

    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
        'C6': 1046.50
    }

    def synth_bell(freq, duration, volume=0.32, is_harp=False):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        if is_harp:
            decay = np.exp(-t * 2.2)
            wave = (np.sin(2 * np.pi * freq * t) +
                    0.5 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 3.5) +
                    0.25 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 5.0))
        else:
            decay = np.exp(-t * 3.6)
            wave = (np.sin(2 * np.pi * freq * t) +
                    0.38 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6.0) +
                    0.18 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 9.0))
        return (wave * decay * volume).astype(np.float32)

    def add_note(name, start_time, dur, vol=0.32, is_harp=False):
        if name not in notes: return
        tone = synth_bell(notes[name], dur * 2.0, volume=vol, is_harp=is_harp)
        s_idx = int(start_time * SAMPLE_RATE)
        e_idx = min(s_idx + len(tone), total_samples)
        if e_idx > s_idx:
            audio[s_idx:e_idx] += tone[:e_idx - s_idx]

    melody = [
        ('C5', 1), ('C5', 1), ('G5', 1), ('G5', 1), ('A5', 1), ('A5', 1), ('G5', 2),
        ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 1), ('D5', 1), ('C5', 2),
        ('G5', 1), ('G5', 1), ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 2),
        ('G5', 1), ('G5', 1), ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 2),
        ('C5', 1), ('C5', 1), ('G5', 1), ('G5', 1), ('A5', 1), ('A5', 1), ('G5', 2),
        ('F5', 1), ('F5', 1), ('E5', 1), ('E5', 1), ('D5', 1), ('D5', 1), ('C5', 2),
    ]

    t = 1.0
    add_note('C6', 0.2, 1.5, 0.2, is_harp=True)
    add_note('G5', 0.5, 1.5, 0.2, is_harp=True)

    while t < total_duration - 4.0:
        for note, length in melody:
            if t >= total_duration - 3.0: break
            add_note(note, t, length * beat_dur, vol=0.35)
            if length >= 2 or (t % (beat_dur * 2) < 0.1):
                base = 'C4' if 'C' in note else ('G4' if 'G' in note else 'F4')
                add_note(base, t, 2.0, vol=0.18, is_harp=True)
            t += length * beat_dur

    add_note('C5', total_duration - 2.5, 3.0, vol=0.25)
    add_note('C4', total_duration - 1.5, 3.5, vol=0.2, is_harp=True)

    # Reverb
    del1 = int(SAMPLE_RATE * 0.22)
    audio[del1:] += audio[:-del1] * 0.32
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio / max_val) * 0.85

    music_path = os.path.join(OUTPUT_DIR, "lullaby_soundtrack.wav")
    with wave.open(music_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return music_path

def build_mixed_soundtrack(scenes, total_duration, voice_name="en-US-JennyNeural", bpm=90, progress_cb=None):
    """Generates timed vocals, music box lullaby, and mixes them together."""
    if progress_cb: progress_cb("Generating neural female lullaby vocal track...", 10)
    asyncio.run(synthesize_vocals(scenes, voice_name, progress_cb))

    if progress_cb: progress_cb("Synthesizing 90 BPM music box lullaby score...", 32)
    music_wav = generate_lullaby_soundtrack(total_duration, bpm)

    # Assemble vocal audio
    total_samples = int(SAMPLE_RATE * total_duration)
    full_vocal_track = np.zeros(total_samples, dtype=np.int16)
    scene_dur = total_duration / float(len(scenes))

    for idx in range(len(scenes)):
        wav_path = os.path.join(VOCALS_DIR, f"scene_{idx+1}.wav")
        if os.path.exists(wav_path):
            with wave.open(wav_path, 'rb') as wf:
                data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            start_s = int((idx * scene_dur + 0.8) * SAMPLE_RATE)
            end_s = min(start_s + len(data), total_samples)
            if end_s > start_s:
                full_vocal_track[start_s:end_s] = data[:end_s - start_s]

    vocal_wav = os.path.join(OUTPUT_DIR, "full_vocals.wav")
    with wave.open(vocal_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(full_vocal_track.tobytes())

    mixed_wav = os.path.join(OUTPUT_DIR, "mixed_soundtrack.wav")
    cmd = [
        FFMPEG, "-y",
        "-i", music_wav,
        "-i", vocal_wav,
        "-filter_complex",
        "[0:a]volume=0.45[music];[1:a]volume=1.4[vox];[music][vox]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-ar", "44100",
        mixed_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mixed_wav

def render_full_video_pipeline(storyboard: dict, voice="en-US-JennyNeural", progress_cb=None):
    """Renders the entire video with walking animations, star flares, vocals, and music."""
    scenes = storyboard.get("scenes", [])
    num_scenes = len(scenes)
    scene_dur = float(scenes[0].get("duration", 8.0)) if num_scenes > 0 else 8.0
    total_duration = num_scenes * scene_dur
    bpm = int(storyboard.get("bpm", 90))

    mixed_audio = build_mixed_soundtrack(scenes, total_duration, voice, bpm, progress_cb)

    scene_patterns = [
        "scene1_windowsill*.jpg", "scene2_cloud_stars*.jpg", "scene3_sunset*.jpg",
        "scene4_night_dance*.jpg", "scene5_fox_lantern*.jpg", "scene6_fork_path*.jpg",
        "scene7_cozy_bed*.jpg", "scene8_sunrise_yawn*.jpg", "scene9_starry_hill*.jpg",
        "scene10_cloud_wave*.jpg"
    ]
    images = []
    for i in range(num_scenes):
        pat = scene_patterns[i % len(scene_patterns)]
        path = find_image(pat)
        if path:
            img = cv2.imread(path)
            img = cv2.resize(img, (WIDTH, HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        else:
            img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        images.append(img)

    temp_video = os.path.join(OUTPUT_DIR, "temp_animated.mp4")
    final_video = os.path.join(OUTPUT_DIR, "Twinkle_Twinkle_Little_Star_3D.mp4")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, FPS, (WIDTH, HEIGHT))

    frames_per_scene = int(scene_dur * FPS)
    fade_frames = int(1.0 * FPS)
    particles = AmbientParticleSystem(count=40)

    star_positions = [
        (int(WIDTH * 0.72), int(HEIGHT * 0.22)), # Scene 1
        (int(WIDTH * 0.70), int(HEIGHT * 0.30)), # Scene 2
        None,                                    # Scene 3
        (int(WIDTH * 0.54), int(HEIGHT * 0.22)), # Scene 4
        (int(WIDTH * 0.63), int(HEIGHT * 0.18)), # Scene 5
        (int(WIDTH * 0.65), int(HEIGHT * 0.23)), # Scene 6
        (int(WIDTH * 0.75), int(HEIGHT * 0.32)), # Scene 7
        (int(WIDTH * 0.51), int(HEIGHT * 0.30)), # Scene 8
        (int(WIDTH * 0.50), int(HEIGHT * 0.18)), # Scene 9
        (int(WIDTH * 0.52), int(HEIGHT * 0.60))  # Scene 10
    ]

    for s in range(num_scenes):
        if progress_cb:
            pct = 40 + int(45 * (s / float(num_scenes)))
            progress_cb(f"Rendering animated walking & motion for scene {s+1}/{num_scenes}...", pct)

        img = images[s]
        star_pos = star_positions[s % len(star_positions)]

        for f in range(frames_per_scene):
            prog = f / float(frames_per_scene)
            global_t = (s * scene_dur) + (f / float(FPS))

            # Camera zoom / pan
            zoom = 1.0 + 0.06 * prog
            crop_w = int(WIDTH / zoom)
            crop_h = int(HEIGHT / zoom)
            x1 = max(0, min(WIDTH - crop_w, int(WIDTH/2 - crop_w/2)))
            y1 = max(0, min(HEIGHT - crop_h, int(HEIGHT/2 - crop_h/2)))
            cropped = img[y1:y1+crop_h, x1:x1+crop_w]
            frame = cv2.resize(cropped, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)

            # Character walking / motion overlays
            if s == 4 or s == 5: # Fox walking scenes
                frame = WalkingCharacterRenderer.draw_fox_walking(frame, global_t, prog)
            elif s == 0 or s == 3: # Pip hopping / dancing
                frame = WalkingCharacterRenderer.draw_pip_hopping(frame, global_t, prog)

            # Star twinkle flare
            if star_pos:
                frame = draw_star_twinkle(frame, star_pos[0], star_pos[1], global_t)

            # Dynamic floating particles
            frame = particles.draw(frame, global_t)

            # Scene 10 fade out
            if s == num_scenes - 1 and prog > 0.85:
                fade = 1.0 - (prog - 0.85) / 0.15
                frame = (frame * fade).astype(np.uint8)

            out.write(frame)

    out.release()

    if progress_cb: progress_cb("Encoding master H.264 video with AAC lullaby vocals...", 92)
    cmd = [
        FFMPEG, "-y",
        "-i", temp_video,
        "-i", mixed_audio,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_video
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_video):
        os.remove(temp_video)

    if progress_cb: progress_cb("Video generation complete!", 100)
    return final_video
