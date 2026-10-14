import os
os.environ.setdefault("U2NET_HOME", os.path.join(os.path.dirname(__file__), ".models"))
import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove
import subprocess
import glob
import wave

ROOT = os.path.dirname(os.path.abspath(__file__))
KEYFRAMES = os.path.join(ROOT, "keyframes")
OUT_VIDEO = os.path.join(ROOT, "Twinkle_Twinkle_Little_Star_Animated.mp4")
RAW_VIDEO = os.path.join(ROOT, "animated_picture_lock.mp4")
MUSIC = os.path.join(ROOT, "mixed_singing.wav")
VOCALS = os.path.join(ROOT, "singing_vocals.wav")
WIDTH, HEIGHT, FPS, SCENE_SECONDS = 1280, 720, 24, 8
FFMPEG = r"C:\Python37\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win64-v4.2.2.exe"

# Boxes tightly frame the foreground character in each 16:9 keyframe.
# Coordinates use the 1280x720 render canvas.
SCENES = [
    ("scene1_windowsill*.jpg", [("bunny", (380, 145, 770, 715)), ("star", (850, 95, 970, 235))]),
    ("scene2_cloud_stars*.jpg", [("bunny", (235, 55, 650, 525)), ("star", (785, 120, 990, 370))]),
    ("scene3_sunset*.jpg", [("sun", (185, 205, 545, 565)), ("bunny", (700, 55, 1005, 715))]),
    ("scene4_night_dance*.jpg", [("bunny", (300, 245, 695, 710)), ("star", (635, 70, 865, 335))]),
    ("scene5_fox_lantern*.jpg", [("fox", (470, 240, 855, 715)), ("star", (760, 55, 965, 285))]),
    ("scene6_fork_path*.jpg", [("fox", (490, 235, 865, 715)), ("star", (755, 45, 965, 285))]),
    ("scene7_cozy_bed*.jpg", [("bunny", (195, 250, 660, 710)), ("star", (770, 135, 1010, 420))]),
    ("scene8_sunrise_yawn*.jpg", [("star", (455, 65, 820, 505))]),
    ("scene9_starry_hill*.jpg", [("fox", (300, 255, 635, 715)), ("bunny", (635, 215, 1005, 715)), ("star", (510, 45, 820, 325))]),
    ("scene10_cloud_wave*.jpg", [("bunny", (175, 250, 565, 715)), ("fox", (760, 250, 1135, 715)), ("star", (545, 365, 835, 690))]),
]


def find_image(pattern):
    hits = glob.glob(os.path.join(KEYFRAMES, pattern))
    if not hits:
        raise FileNotFoundError(f"No keyframe matches {pattern}")
    return hits[0]


def segment_sprite(image, box, session):
    x1, y1, x2, y2 = box
    crop = image[y1:y2, x1:x2]
    rgba = remove(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)), session=session)
    rgba = np.array(rgba.convert("RGBA"))
    rgba[:, :, :3] = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    # Remove tiny segmentation flecks and soften the edge for clean compositing.
    alpha = rgba[:, :, 3]
    alpha[alpha < 32] = 0
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.65)
    rgba[:, :, 3] = alpha
    sprite = rgba
    mask = np.zeros(image.shape[:2], np.uint8)
    mask[y1:y2, x1:x2] = (alpha > 24).astype(np.uint8) * 255
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    return sprite, mask, (x1, y1, x2, y2)


def make_scene(pattern, entity_specs, session):
    src = cv2.imread(find_image(pattern))
    base = cv2.resize(src, (WIDTH, HEIGHT), interpolation=cv2.INTER_LANCZOS4)
    entities, combined_mask = [], np.zeros((HEIGHT, WIDTH), np.uint8)
    for name, box in entity_specs:
        sprite, mask, box = segment_sprite(base, box, session)
        entities.append({"name": name, "sprite": sprite, "box": box})
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    # Fill behind the moving cutouts so their original positions do not ghost.
    background = cv2.inpaint(base, combined_mask, 9, cv2.INPAINT_TELEA)
    return {"background": background, "entities": entities}


def alpha_composite(frame, rgba, cx, cy, scale, angle, name, scene_i, t):
    h, w = rgba.shape[:2]
    rgba = rgba.copy()
    sample_i = min(len(VOICE_ENVELOPE)-1, max(0, int(t * FPS)))
    level = float(VOICE_ENVELOPE[sample_i])
    if name in ("bunny", "fox", "sun") and level > 0.12:
        # Local audio-driven mouth shapes. The spectral brightness estimate makes
        # sustained vowels vary between wider and rounder shapes, while the
        # smoothed vocal envelope controls jaw opening.
        if name == "bunny":
            positions = {0: (0.79, 0.38), 3: (0.63, 0.31), 6: (0.43, 0.35),
                         8: (0.27, 0.34), 9: (0.80, 0.22)}
            if scene_i not in positions:
                return alpha_composite(frame, rgba, cx, cy, scale, angle, "", scene_i, t)
            mx, my = int(w * positions[scene_i][0]), int(h * positions[scene_i][1])
        elif name == "fox":
            positions = {4: (0.56, 0.34), 5: (0.54, 0.29), 8: (0.79, 0.27), 9: (0.10, 0.24)}
            if scene_i not in positions:
                return alpha_composite(frame, rgba, cx, cy, scale, angle, "", scene_i, t)
            mx, my = int(w * positions[scene_i][0]), int(h * positions[scene_i][1])
        elif name == "sun":
            positions = {2: (0.52, 0.49)}
        if scene_i not in positions:
            return alpha_composite(frame, rgba, cx, cy, scale, angle, "", scene_i, t)
        mx, my = int(w * positions[scene_i][0]), int(h * positions[scene_i][1])
        brightness = float(VOICE_BRIGHTNESS[sample_i])
        opening = np.clip((level - 0.10) / 0.85, 0.0, 1.0)
        # Low-brightness vowels tend to be rounded; bright vowels spread wider.
        roundness = np.clip((0.62 - brightness) / 0.42, 0.0, 1.0)
        rx = max(2, int(w * (0.013 + 0.025 * opening) * (1.0 - 0.30*roundness)))
        ry = max(2, int(h * (0.004 + 0.032 * opening) * (0.72 + 0.45*roundness)))
        cv2.ellipse(rgba, (mx, my), (rx + 1, ry + 1), 0, 0, 360,
                    (75, 47, 62, 220), -1, cv2.LINE_AA)
        cv2.ellipse(rgba, (mx, my), (rx, ry), 0, 0, 360,
                    (35, 20, 32, 250), -1, cv2.LINE_AA)
        if opening > 0.42:
            tongue_y = my + max(1, int(ry * 0.48))
            cv2.ellipse(rgba, (mx, tongue_y), (max(2, int(rx*0.56)), max(1, int(ry*0.30))),
                        0, 0, 180, (118, 118, 220, 230), -1, cv2.LINE_AA)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    sprite = cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    center = (nw / 2.0, nh / 2.0)
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    ca, sa = abs(mat[0, 0]), abs(mat[0, 1])
    rw, rh = int(nh * sa + nw * ca), int(nh * ca + nw * sa)
    mat[0, 2] += rw / 2 - center[0]
    mat[1, 2] += rh / 2 - center[1]
    sprite = cv2.warpAffine(sprite, mat, (rw, rh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    x, y = int(cx - rw / 2), int(cy - rh / 2)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(WIDTH, x + rw), min(HEIGHT, y + rh)
    if x0 >= x1 or y0 >= y1:
        return frame
    patch = sprite[y0-y:y1-y, x0-x:x1-x]
    alpha = patch[:, :, 3:4].astype(np.float32) / 255.0
    frame[y0:y1, x0:x1] = (patch[:, :, :3] * alpha + frame[y0:y1, x0:x1] * (1-alpha)).astype(np.uint8)
    return frame


def animate_entity(entity, scene_index, t, progress, camera_zoom, camera_x, camera_y):
    x1, y1, x2, y2 = entity["box"]
    name = entity["name"]
    base_cx, base_cy = (x1+x2)/2, (y1+y2)/2
    phase = scene_index * 0.77 + (0.0 if name == "bunny" else 1.7)
    if name == "star":
        bob = 15*np.sin(t*2.0 + phase)
        drift = 13*np.sin(t*0.75 + phase)
        scale = 1 + 0.035*np.sin(t*2.5 + phase)
        angle = 2.5*np.sin(t*1.2 + phase)
    elif name == "sun":
        bob = 5*np.sin(t*1.1 + phase) + 10*progress
        drift = -13*progress
        scale = 1 + 0.015*np.sin(t*1.2)
        angle = 0
    else:
        bob = 7*np.sin(t*2.0 + phase)
        if scene_index in (3, 4, 5, 8):
            bob += 3*np.sin(t*4.0 + phase)
        drift = 7*np.sin(t*1.1 + phase)
        if scene_index in (4, 5):
            drift += 8*progress
        scale = 1 + 0.012*np.sin(t*1.7 + phase)
        angle = 0.7*np.sin(t*1.2 + phase)
    cx = (base_cx - WIDTH/2)*camera_zoom + WIDTH/2 + camera_x + drift
    cy = (base_cy - HEIGHT/2)*camera_zoom + HEIGHT/2 + camera_y + bob
    return cx, cy, scale*camera_zoom, angle


def draw_atmosphere(frame, scene_index, t):
    # Gentle moving glints and fireflies; avoid covering the characters.
    overlay = frame.copy()
    for i in range(16):
        seed = i * 13.37 + scene_index * 8.1
        x = int((seed*47 + 22*np.sin(t*0.35 + seed)) % WIDTH)
        y = int((seed*73 - t*(8 + i%4) + 18*np.cos(t*0.5 + seed)) % HEIGHT)
        r = 1 + (i % 2)
        pulse = 0.45 + 0.55*(0.5 + 0.5*np.sin(t*2 + seed))
        color = (int(145*pulse), int(205*pulse), int(255*pulse))
        cv2.circle(overlay, (x, y), r*3, color, -1, cv2.LINE_AA)
        cv2.circle(overlay, (x, y), r, (235, 245, 255), -1, cv2.LINE_AA)
    return cv2.addWeighted(frame, 0.88, overlay, 0.12, 0)


def render():
    global VOICE_ENVELOPE, VOICE_BRIGHTNESS
    os.makedirs(os.path.join(ROOT, ".models"), exist_ok=True)
    with wave.open(VOCALS, "rb") as wav:
        rate = wav.getframerate()
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32)
    # Analyze 40 ms windows at the render frame rate. RMS supplies jaw movement;
    # spectral centroid provides a lightweight vowel-shape cue. Smooth both to
    # avoid chatter at frame boundaries and normalize across quiet/loud passages.
    step = max(1, int(rate / FPS))
    env, brightness = [], []
    for i in range(0, len(pcm), step):
        chunk = pcm[i:i+step]
        if not len(chunk):
            continue
        env.append(float(np.sqrt(np.mean(chunk * chunk))))
        spectrum = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
        freqs = np.fft.rfftfreq(len(chunk), 1.0 / rate)
        voice_band = (freqs >= 250) & (freqs <= 4000)
        band = spectrum[voice_band]
        hz = freqs[voice_band]
        brightness.append(float(np.sum(hz * band) / max(float(np.sum(band)), 1e-6)))
    env = np.asarray(env, dtype=np.float32)
    brightness = np.asarray(brightness, dtype=np.float32)
    env /= max(float(np.percentile(env, 95)), 1.0)
    VOICE_ENVELOPE = np.clip(env, 0, 1)
    VOICE_ENVELOPE = cv2.GaussianBlur(VOICE_ENVELOPE.reshape(-1, 1), (1, 5), 0).ravel()
    VOICE_BRIGHTNESS = np.clip((brightness - 650.0) / 2300.0, 0, 1)
    print("Loading lightweight CPU character-segmentation model...")
    session = new_session("u2netp", providers=["CPUExecutionProvider"])
    scenes = []
    for i, (pattern, entities) in enumerate(SCENES):
        print(f"Preparing character cutouts for scene {i+1}/10")
        scenes.append(make_scene(pattern, entities, session))

    writer = cv2.VideoWriter(RAW_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("Could not create intermediate video")
    frames_per_scene = SCENE_SECONDS * FPS
    fade_frames = int(0.5 * FPS)
    total = len(scenes) * frames_per_scene
    print("Rendering 80 seconds of moving character scenes...")
    for frame_no in range(total):
        scene_i = min(frame_no // frames_per_scene, len(scenes)-1)
        local = frame_no - scene_i*frames_per_scene
        progress = local / frames_per_scene
        t = frame_no / FPS
        zoom = 1.0 + 0.025*progress + 0.008*np.sin(t*0.22 + scene_i)
        cam_x = 10*np.sin(t*0.18 + scene_i*0.5)
        cam_y = 7*np.cos(t*0.16 + scene_i*0.45)
        mat = np.float32([[zoom, 0, (1-zoom)*WIDTH/2+cam_x], [0, zoom, (1-zoom)*HEIGHT/2+cam_y]])
        frame = cv2.warpAffine(scenes[scene_i]["background"], mat, (WIDTH, HEIGHT), borderMode=cv2.BORDER_REFLECT)
        for entity in scenes[scene_i]["entities"]:
            cx, cy, scale, angle = animate_entity(entity, scene_i, t, progress, zoom, cam_x, cam_y)
            frame = alpha_composite(frame, entity["sprite"], cx, cy, scale, angle,
                                    entity["name"], scene_i, t)
        frame = draw_atmosphere(frame, scene_i, t)
        # Crossfade into the next scene during the final half second.
        if scene_i < len(scenes)-1 and local >= frames_per_scene-fade_frames:
            a = (local-(frames_per_scene-fade_frames))/fade_frames
            next_i = scene_i+1
            next_bg = scenes[next_i]["background"]
            next_frame = next_bg.copy()
            next_prog = (local-(frames_per_scene-fade_frames))/fade_frames
            for entity in scenes[next_i]["entities"]:
                cx, cy, scale, angle = animate_entity(entity, next_i, t, next_prog, 1.0, 0, 0)
                next_frame = alpha_composite(next_frame, entity["sprite"], cx, cy, scale, angle,
                                             entity["name"], next_i, t)
            next_frame = draw_atmosphere(next_frame, next_i, t)
            frame = cv2.addWeighted(frame, 1-a, next_frame, a, 0)
        if t >= 76.0:
            # Sinsy's demo terms require its name to appear when generated vocals
            # are distributed; keep a small readable credit on the closing shot.
            label = "Singing voice: Sinsy"
            cv2.putText(frame, label, (WIDTH-345, HEIGHT-24), cv2.FONT_HERSHEY_SIMPLEX,
                        0.68, (24, 28, 42), 4, cv2.LINE_AA)
            cv2.putText(frame, label, (WIDTH-345, HEIGHT-24), cv2.FONT_HERSHEY_SIMPLEX,
                        0.68, (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(frame)
        if frame_no % (FPS*8) == 0:
            print(f"Rendered {frame_no//FPS}s / 80s")
    writer.release()
    print("Adding the generated sung vocal and matching music-box accompaniment...")
    subprocess.run([
        FFMPEG, "-y", "-i", RAW_VIDEO, "-i", MUSIC,
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "fast",
        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-shortest", OUT_VIDEO
    ], check=True)
    os.remove(RAW_VIDEO)
    print(f"Done: {OUT_VIDEO}")


if __name__ == "__main__":
    render()
