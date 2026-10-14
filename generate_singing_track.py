"""Generate an English sung vocal from the public-domain Twinkle score via Sinsy."""
import os
import requests
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
XML_PATH = os.path.join(ROOT, "twinkle_score.musicxml")
WAV_PATH = os.path.join(ROOT, "singing_vocals.wav")
API = "https://sinsy.sp.nitech.ac.jp/api/synthesize"

# One syllable per note, with note rests between lines represented by phrasing
# and held final notes. Syllabification is explicit for English input.
PHRASES = [
    "twin-kle twin-kle lit-tle star",
    "how I won-der what you are",
    "up a-bove the world so high",
    "like a di-a-mond in the sky",
    "when the sun has gone a-way",
    "moon and stars come out to play",
    "then you shine your lit-tle light",
    "twin-kle soft-ly through the night",
    "then the trav-el-ler in the dark",
    "thanks you for your ti-ny spark",
    "he could not see which way to go",
    "if you did not twin-kle so",
    "in the dark blue sky you keep",
    "and of-ten through my cur-tains peep",
    "for you nev-er shut your eye",
    "till the sun is in the sky",
    "as your bright and ti-ny spark",
    "lights the trav-el-ler in the dark",
    "though I know not what you are",
    "twin-kle twin-kle lit-tle star",
]
MELODY = [60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60]


def add_note(measure, pitch=None, duration=1, lyric=None, syllabic=None):
    note = ET.SubElement(measure, "note")
    if pitch is None:
        ET.SubElement(note, "rest")
    else:
        step_names = ["C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B"]
        alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
        octave = pitch // 12 - 1
        pc = pitch % 12
        p = ET.SubElement(note, "pitch")
        ET.SubElement(p, "step").text = step_names[pc]
        if alters[pc]:
            ET.SubElement(p, "alter").text = "1"
        ET.SubElement(p, "octave").text = str(octave)
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "type").text = "half" if duration == 2 else "quarter"
    if lyric:
        lyr = ET.SubElement(note, "lyric", number="1")
        if syllabic:
            ET.SubElement(lyr, "syllabic").text = syllabic
        ET.SubElement(lyr, "text").text = lyric


def build_score():
    score = ET.Element("score-partwise", version="3.1")
    work = ET.SubElement(score, "work")
    ET.SubElement(work, "work-title").text = "Twinkle Twinkle Little Star"
    part_list = ET.SubElement(score, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(score_part, "part-name").text = "Voice"
    part = ET.SubElement(score, "part", id="P1")
    measure_no = 1
    m = ET.SubElement(part, "measure", number=str(measure_no))
    attrs = ET.SubElement(m, "attributes")
    ET.SubElement(attrs, "divisions").text = "1"
    key = ET.SubElement(attrs, "key")
    ET.SubElement(key, "fifths").text = "0"
    time = ET.SubElement(attrs, "time")
    ET.SubElement(time, "beats").text = "4"
    ET.SubElement(time, "beat-type").text = "4"
    clef = ET.SubElement(attrs, "clef")
    ET.SubElement(clef, "sign").text = "G"
    ET.SubElement(clef, "line").text = "2"
    sound = ET.SubElement(m, "direction")
    direction_type = ET.SubElement(sound, "direction-type")
    metronome = ET.SubElement(direction_type, "metronome")
    ET.SubElement(metronome, "beat-unit").text = "quarter"
    ET.SubElement(metronome, "per-minute").text = "120"
    ET.SubElement(sound, "sound", tempo="120")
    add_note(m, None, 1)

    beat_in_measure = 1
    for phrase_i, phrase in enumerate(PHRASES):
        syllables = phrase.split()
        tokens = []
        for word in syllables:
            parts = word.split("-")
            for i, part_text in enumerate(parts):
                label = "single" if len(parts) == 1 else ("begin" if i == 0 else ("end" if i == len(parts)-1 else "middle"))
                tokens.append((part_text, label))
        n = len(tokens)
        durations = [1] * n
        if n == 7:
            durations[-1] = 2
        elif n < 7:
            durations[-1] += 7 - n
        # Eight syllables fit eight beats across two measures; keep the cadence
        # and note sequence melodic by using the standard tune's pitch arc.
        for i, (text, syllabic) in enumerate(tokens):
            duration = durations[i]
            if beat_in_measure + duration > 4:
                measure_no += 1
                m = ET.SubElement(part, "measure", number=str(measure_no))
                beat_in_measure = 0
            add_note(m, MELODY[(phrase_i % 2) * 7 + min(i, 6)], duration, text, syllabic)
            beat_in_measure += duration
            if beat_in_measure == 4:
                measure_no += 1
                m = ET.SubElement(part, "measure", number=str(measure_no))
                beat_in_measure = 0
    if len(m) == 0:
        part.remove(m)
    ET.ElementTree(score).write(XML_PATH, encoding="utf-8", xml_declaration=True)


def main():
    build_score()
    with open(XML_PATH, "rb") as score_file:
        response = requests.post(
            API,
            params={"voice_name": "f00002e_dnn_beta5", "alpha": 0.42, "vibpow": 0.7, "f0shift": 0},
            files={"score": (os.path.basename(XML_PATH), score_file, "application/vnd.recordare.musicxml+xml")},
            timeout=600,
        )
    response.raise_for_status()
    data = response.json()
    wav_url = data.get("links", {}).get("wav") or data.get("files", {}).get("resultWav")
    if not wav_url:
        raise RuntimeError("Sinsy returned no WAV audio: " + str(data)[:800])
    if wav_url.startswith("/"):
        wav_url = "https://sinsy.sp.nitech.ac.jp" + wav_url
    audio = requests.get(wav_url, timeout=120)
    audio.raise_for_status()
    with open(WAV_PATH, "wb") as f:
        f.write(audio.content)
    print("Saved English singing vocal:", WAV_PATH, "bytes:", len(audio.content))


if __name__ == "__main__":
    main()
