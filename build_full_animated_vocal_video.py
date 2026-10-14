import os
import glob
import subprocess
import numpy as np
import cv2
import imageio_ffmpeg

OUTPUT_DIR = r"c:\Users\HP\Downloads\video generator"
KEYFRAMES_DIR = os.path.join(OUTPUT_DIR, "keyframes")
VOCALS_DIR = os.path.join(OUTPUT_DIR, "vocals")
ANIMATED_SCENES_DIR = os.path.join(OUTPUT_DIR, "animated_scenes")
os.makedirs(VOCALS_DIR, exist_ok=True)

FINAL_VIDEO = os.path.join(OUTPUT_DIR, "Twinkle_Twinkle_Little_Star_Animated.mp4")
TEMP_VIDEO = os.path.join(OUTPUT_DIR, "temp_animated.mp4")
VOCAL_AUDIO = os.path.join(OUTPUT_DIR, "full_vocals.wav")
MUSIC_AUDIO = os.path.join(OUTPUT_DIR, "lullaby_soundtrack.wav")
MIXED_AUDIO = os.path.join(OUTPUT_DIR, "mixed_soundtrack.wav")
# Supply a sung vocal recording here. The previous Edge TTS workflow spoke each
# line and could not produce the natural melody and phrasing this rhyme needs.
SINGING_AUDIO = os.path.join(OUTPUT_DIR, "singing_vocals.wav")

WIDTH = 1280
HEIGHT = 720
FPS = 24
SCENE_DUR = 8.0 # seconds per scene
NUM_SCENES = 10
TOTAL_DUR = SCENE_DUR * NUM_SCENES # 80 seconds
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SCENE_LYRICS = [
    "Twinkle, twinkle, little star, how I wonder what you are.",
    "Up above the world so high, like a diamond in the sky.",
    "When the sun has gone away, moon and stars come out to play.",
    "Then you shine your little light, twinkle softly through the night.",
    "Then the traveller in the dark, thanks you for your tiny spark.",
    "He could not see which way to go, if you did not twinkle so.",
    "In the dark blue sky you keep, and often through my curtains peep.",
    "For you never shut your eye, till the sun is in the sky.",
    "As your bright and tiny spark, lights the traveller in the dark.",
    "Though I know not what you are, twinkle, twinkle, little star."
]

def find_image(pattern):
    matches = glob.glob(os.path.join(KEYFRAMES_DIR, pattern))
    if not matches:
        raise FileNotFoundError(f"Missing image for pattern {pattern}")
    return matches[0]

# --- 1. PREPARE A SUNG VOCAL TRACK ---
def prepare_singing_track():
    if not os.path.isfile(SINGING_AUDIO):
        raise FileNotFoundError(
            f"Add a sung vocal recording at {SINGING_AUDIO}. "
            "This project no longer uses speech TTS, which sounds like reading."
        )
    print("Preparing sung vocal recording for the 80-second video...")
    subprocess.run([
        FFMPEG, "-y", "-i", SINGING_AUDIO,
        "-af", f"apad,atrim=0:{TOTAL_DUR}",
        "-ar", "44100", "-ac", "1", VOCAL_AUDIO
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Saved prepared singing track to {VOCAL_AUDIO}")

def mix_vocals_and_music():
    print("Mixing vocals with music box lullaby...")
    # Mix: Vocal track boosted + Music box lullaby balanced underneath + warm reverb
    cmd = [
        FFMPEG, "-y",
        "-i", MUSIC_AUDIO,
        "-i", VOCAL_AUDIO,
        "-filter_complex",
        "[0:a]volume=0.45[music];[1:a]volume=1.4[vox];[music][vox]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-ar", "44100",
        MIXED_AUDIO
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Mixed soundtrack saved to {MIXED_AUDIO}")

# --- 2. DYNAMIC ANIMATED VIDEO RENDERING ---
class ParticleSystem:
    def __init__(self, count=35):
        self.count = count
        np.random.seed(42)
        self.x = np.random.uniform(0, WIDTH, count)
        self.y = np.random.uniform(0, HEIGHT, count)
        self.size = np.random.uniform(2, 6, count)
        self.speed_y = np.random.uniform(-0.8, -0.2, count)
        self.speed_x = np.random.uniform(-0.4, 0.4, count)
        self.pulse_phase = np.random.uniform(0, 2*np.pi, count)
        self.color = np.random.choice([0, 1, 2], count) # 0: gold, 1: warm white, 2: soft cyan

    def update_and_draw(self, frame, t):
        overlay = frame.copy()
        for i in range(self.count):
            self.x[i] = (self.x[i] + self.speed_x[i] + np.sin(t*1.5 + self.pulse_phase[i])*0.5) % WIDTH
            self.y[i] = (self.y[i] + self.speed_y[i]) % HEIGHT

            brightness = 0.5 + 0.5 * np.sin(t * 3.0 + self.pulse_phase[i])
            r = int(self.size[i] * (0.8 + 0.4 * brightness))
            
            px, py = int(self.x[i]), int(self.y[i])
            # Draw glowing particle
            if self.color[i] == 0:
                col = (int(130 * brightness), int(220 * brightness), int(255 * brightness)) # Gold BGR
            elif self.color[i] == 1:
                col = (int(255 * brightness), int(255 * brightness), int(255 * brightness)) # White
            else:
                col = (int(255 * brightness), int(230 * brightness), int(160 * brightness)) # Cyan-blue

            # Soft glow halo
            cv2.circle(overlay, (px, py), r * 2, col, -1)
            cv2.circle(overlay, (px, py), max(1, r // 2), (255, 255, 255), -1)

        return cv2.addWeighted(frame, 0.75, overlay, 0.25, 0)

def draw_star_flare(frame, cx, cy, t, scale=1.0):
    # Dynamic starburst pulsation for Twinkle
    flare_layer = frame.copy()
    pulse = 1.0 + 0.25 * np.sin(t * 4.0)
    ray_len = int(35 * pulse * scale)
    glow_rad = int(24 * pulse * scale)

    # Ambient radial glow
    cv2.circle(flare_layer, (cx, cy), glow_rad, (120, 230, 255), -1)
    # 4-point star rays
    cv2.line(flare_layer, (cx - ray_len, cy), (cx + ray_len, cy), (180, 245, 255), 2)
    cv2.line(flare_layer, (cx, cy - ray_len), (cx, cy + ray_len), (180, 245, 255), 2)
    diag = int(ray_len * 0.6)
    cv2.line(flare_layer, (cx - diag, cy - diag), (cx + diag, cy + diag), (200, 250, 255), 1)
    cv2.line(flare_layer, (cx - diag, cy + diag), (cx + diag, cy - diag), (200, 250, 255), 1)

    return cv2.addWeighted(frame, 0.7, flare_layer, 0.3, 0)

def render_scene_frame(img, prog, scene_idx, global_time, particles):
    h, w = img.shape[:2]

    # Camera choreography
    if scene_idx == 0:
        zoom = 1.0 + 0.08 * prog
        cx, cy = 0.52 * w, 0.48 * h
        star_pos = (int(w * 0.72), int(h * 0.22))
    elif scene_idx == 1:
        zoom = 1.0 + 0.07 * prog
        cx = (0.50 + 0.04 * prog) * w
        cy = (0.50 - 0.03 * prog) * h
        star_pos = (int(w * 0.70), int(h * 0.30))
    elif scene_idx == 2:
        zoom = 1.04
        cx = (0.45 + 0.07 * prog) * w
        cy = 0.50 * h
        star_pos = None # Sun scene
    elif scene_idx == 3:
        sway = np.sin(prog * np.pi * 2) * 0.02
        zoom = 1.04 + sway
        cx, cy = 0.50 * w, 0.50 * h
        star_pos = (int(w * 0.54), int(h * 0.22))
    elif scene_idx == 4:
        zoom = 1.05
        cx = (0.46 + 0.07 * prog) * w
        cy = 0.50 * h
        star_pos = (int(w * 0.63), int(h * 0.18))
    elif scene_idx == 5:
        zoom = 1.08 - 0.06 * prog
        cx, cy = 0.50 * w, 0.50 * h
        star_pos = (int(w * 0.65), int(h * 0.23))
    elif scene_idx == 6:
        zoom = 1.0 + 0.07 * prog
        cx = (0.48 + 0.03 * prog) * w
        cy = 0.52 * h
        star_pos = (int(w * 0.75), int(h * 0.32))
    elif scene_idx == 7:
        zoom = 1.05
        cx = (0.45 + 0.07 * prog) * w
        cy = (0.50 - 0.02 * prog) * h
        star_pos = (int(w * 0.51), int(h * 0.30))
    elif scene_idx == 8:
        angle_shift = np.sin(prog * np.pi) * 0.02
        zoom = 1.03 + 0.04 * prog
        cx = (0.50 + angle_shift) * w
        cy = 0.50 * h
        star_pos = (int(w * 0.50), int(h * 0.18))
    else: # Scene 10
        zoom = 1.10 - 0.09 * prog
        cx, cy = 0.50 * w, 0.50 * h
        star_pos = (int(w * 0.52), int(h * 0.60))

    crop_w = int(w / zoom)
    crop_h = int(h / zoom)
    x1 = max(0, min(w - crop_w, int(cx - crop_w / 2)))
    y1 = max(0, min(h - crop_h, int(cy - crop_h / 2)))

    cropped = img[y1:y1+crop_h, x1:x1+crop_w]
    frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    # Star flare animation
    if star_pos:
        frame = draw_star_flare(frame, star_pos[0], star_pos[1], global_time)

    # Particle system animation
    frame = particles.update_and_draw(frame, global_time)

    # Scene 10 final soft fade to black
    if scene_idx == 9 and prog > 0.85:
        fade = 1.0 - (prog - 0.85) / 0.15
        frame = (frame * fade).astype(np.uint8)

    return frame

def render_animated_video():
    clip_paths = [os.path.join(ANIMATED_SCENES_DIR, f"scene_{i:02d}.mp4") for i in range(1, NUM_SCENES + 1)]
    if all(os.path.isfile(path) for path in clip_paths):
        print("Assembling generated animated scene clips...")
        cmd = [FFMPEG, "-y"]
        for path in clip_paths:
            cmd.extend(["-i", path])
        clip_inputs = "".join(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={FPS},trim=duration={SCENE_DUR},"
            f"setpts=PTS-STARTPTS,format=yuv420p[v{i}];"
            for i in range(NUM_SCENES)
        )
        concat_inputs = "".join(f"[v{i}]" for i in range(NUM_SCENES))
        filter_graph = f"{clip_inputs}{concat_inputs}concat=n={NUM_SCENES}:v=1:a=0[outv]"
        cmd.extend([
            "-filter_complex", filter_graph, "-map", "[outv]", "-an",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-r", str(FPS), TEMP_VIDEO
        ])
        subprocess.run(cmd, check=True)
        return

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
    images = []
    for pat in scene_patterns:
        path = find_image(pat)
        img = cv2.imread(path)
        img = cv2.resize(img, (WIDTH, HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        images.append(img)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    frames_per_scene = int(SCENE_DUR * FPS) # 192 frames
    fade_frames = int(1.0 * FPS) # 24 frames
    particles = ParticleSystem(count=40)

    print("Rendering animated video frames with dynamic particles and star flares...")
    for s in range(NUM_SCENES):
        print(f"Animating Scene {s+1}/10...")
        for f in range(frames_per_scene):
            prog = f / float(frames_per_scene)
            global_time = (s * SCENE_DUR) + (f / float(FPS))
            frame_curr = render_scene_frame(images[s], prog, s, global_time, particles)

            if s < NUM_SCENES - 1 and f >= (frames_per_scene - fade_frames):
                alpha = (f - (frames_per_scene - fade_frames)) / float(fade_frames)
                next_prog = (f - (frames_per_scene - fade_frames)) / float(frames_per_scene)
                frame_next = render_scene_frame(images[s+1], next_prog, s+1, global_time, particles)
                final_frame = cv2.addWeighted(frame_curr, 1.0 - alpha, frame_next, alpha, 0)
            else:
                final_frame = frame_curr

            out.write(final_frame)

    out.release()
    print("Video frame generation finished!")

def mux_final():
    print("Muxing animated video and mixed vocal/music audio...")
    cmd = [
        FFMPEG, "-y",
        "-i", TEMP_VIDEO,
        "-i", MIXED_AUDIO,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_VIDEO
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
    print(f"COMPLETE! Master video with vocal singing and animation: {FINAL_VIDEO}")

if __name__ == "__main__":
    prepare_singing_track()
    mix_vocals_and_music()
    render_animated_video()
    mux_final()
