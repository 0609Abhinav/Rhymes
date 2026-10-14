"""Build a bell accompaniment and warm mix for the Sinsy nursery-rhyme vocal."""
import os
import subprocess
import wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RATE = 44100
TEMPO = 120.0
PHRASES = [
    "twin-kle twin-kle lit-tle star", "how I won-der what you are",
    "up a-bove the world so high", "like a di-a-mond in the sky",
    "when the sun has gone a-way", "moon and stars come out to play",
    "then you shine your lit-tle light", "twin-kle soft-ly through the night",
    "then the trav-el-ler in the dark", "thanks you for your ti-ny spark",
    "he could not see which way to go", "if you did not twin-kle so",
    "in the dark blue sky you keep", "and of-ten through my cur-tains peep",
    "for you nev-er shut your eye", "till the sun is in the sky",
    "as your bright and ti-ny spark", "lights the trav-el-ler in the dark",
    "though I know not what you are", "twin-kle twin-kle lit-tle star",
]
MELODY = [60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60]


def make_music():
    # Keep the full Sinsy release/tail before matching its 84-second file to
    # the 80-second picture in the final mix.
    total = 84.0
    audio = np.zeros(int(RATE * total), dtype=np.float64)
    time_cursor = 0.5  # match the score's one-beat pickup rest at 120 BPM
    beat = 60.0 / TEMPO
    for phrase_i, phrase in enumerate(PHRASES):
        syllables = [p for word in phrase.split() for p in word.split("-")]
        lengths = [1] * len(syllables)
        if len(syllables) == 7:
            lengths[-1] = 2
        elif len(syllables) < 7:
            lengths[-1] += 7 - len(syllables)
        for i, length in enumerate(lengths):
            dur = length * beat
            start = int(time_cursor * RATE)
            count = min(int(dur * RATE), len(audio) - start)
            if count > 0:
                t = np.arange(count) / RATE
                midi = MELODY[(phrase_i % 2) * 7 + min(i, 6)]
                freq = 440.0 * (2 ** ((midi - 69) / 12))
                tone = (np.sin(2 * np.pi * freq * t)
                        + 0.30 * np.sin(2 * np.pi * freq * 2.73 * t)
                        + 0.12 * np.sin(2 * np.pi * freq * 5.2 * t))
                env = np.exp(-t * (2.2 if length > 1 else 4.0))
                audio[start:start + count] += tone * env * 0.10
                # Soft fifth below the melody adds a warm music-box bed.
                bass = freq / 2
                audio[start:start + count] += np.sin(2 * np.pi * bass * t) * np.exp(-t * 2.8) * 0.045
            time_cursor += dur
    # Gentle final C chord holds the rhyme through Sinsy's vocal release.
    start = int(time_cursor * RATE)
    count = max(0, min(int((total - time_cursor) * RATE), len(audio) - start))
    if count:
        t = np.arange(count) / RATE
        chord = (np.sin(2 * np.pi * 130.81 * t)
                 + 0.45 * np.sin(2 * np.pi * 261.63 * t)
                 + 0.32 * np.sin(2 * np.pi * 392.00 * t))
        audio[start:start + count] += 0.025 * chord * np.exp(-t * 0.8)
    # Gentle echo softens the synthetic bell attack.
    dry = audio.copy()
    for delay, gain in ((0.18, 0.20), (0.34, 0.11)):
        offset = int(delay * RATE)
        audio[offset:] += dry[:-offset] * gain
    peak = max(np.max(np.abs(audio)), 1e-8)
    audio = np.clip(audio / peak * 0.68, -1, 1)
    with wave.open(os.path.join(ROOT, "singing_accompaniment.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes((audio * 32767).astype(np.int16).tobytes())


def main():
    make_music()
    ffmpeg = r"C:\Python37\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win64-v4.2.2.exe"
    subprocess.run([
        ffmpeg, "-y", "-i", os.path.join(ROOT, "singing_accompaniment.wav"),
        "-i", os.path.join(ROOT, "singing_vocals.wav"), "-filter_complex",
        "[0:a]volume=0.20,afade=t=out:st=81:d=3[m];"
        "[1:a]asetpts=PTS-STARTPTS,"
        "highpass=f=90,equalizer=f=3200:t=q:w=1:g=-1.2,"
        "acompressor=threshold=0.08:ratio=2:attack=15:release=160:makeup=1.3,"
        "aecho=0.8:0.12:70|135:0.08|0.04,volume=1.1[v];"
        "[m][v]amix=inputs=2:duration=longest:dropout_transition=1,"
        "atempo=1.05,atrim=0:80,alimiter=limit=0.95[out]",
        "-map", "[out]", "-t", "80", "-ar", str(RATE), "-ac", "1",
        os.path.join(ROOT, "mixed_singing.wav")
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Created an 80-second sung vocal mix with a matched bell accompaniment.")


if __name__ == "__main__":
    main()
