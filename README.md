# 🌟 Twinkle Twinkle Little Star — 3D Animation Production Package

A complete 10-scene, 80-second (8s per scene) 3D toddler nursery rhyme animation package with visual consistency, prompt engineering, keyframes, and audio design.

---

## 🎨 Visual Identity & Consistency Rules
* **Art Style:** Soft pastel colors, rounded glossy toy-like shapes, warm glowing light, big sparkly eyes, smooth gentle motion, vinyl/claymation CGI.
* **Negative Prompt (Essential for all engines):**
  > `text, subtitles, watermark, logo, scary, jagged edges, hyperrealistic skin pores, dark shadows, glitch, sudden jerk, low quality, noisy artifacts`
* **Aspect Ratio:** 16:9 (`--ar 16:9`)
* **Characters:**
  * **Pip:** Chubby cream baby bunny, floppy ears, brown eyes, pink nose, sky-blue pyjamas with tiny yellow stars.
  * **Twinkle:** Smiling yellow star, rosy cheeks, soft golden glow.
  * **Fox:** Friendly orange cub, fluffy tail, small warm lantern.

---

## 📁 Project Assets

* `keyframes/` — Generated high-resolution 3D keyframe concept renders:
  * `character_lineup_*.jpg`: Pip, Twinkle, and Fox character reference lineup.
  * `scene1_windowsill_*.jpg`: Scene 1 keyframe (Pip gazing from windowsill).
  * `scene5_fox_lantern_*.jpg`: Scene 5 keyframe (Fox in forest guided by Twinkle).
  * `scene10_cloud_wave_*.jpg`: Scene 10 finale keyframe (Pip, Fox & Twinkle waving from cloud).
* `storyboard_and_prompts.json` — Machine-readable production data with camera moves, prompts, audio cues, and timing.
* `storyboard_viewer.html` — Interactive visual storyboard web application. Open in any browser to inspect scenes and copy prompts with one click!

---

## 🎬 10-Scene Breakdown (8 Seconds Each)

| # | Time | Lyric Line | Setting & Action | Camera Movement |
|---|---|---|---|---|
| **1** | `00:00 - 00:08` | *Twinkle, twinkle, little star, how I wonder what you are* | Pip on windowsill at dusk gazes at Twinkle; question-mark sparkle floats. | Slow push-in toward Pip, gentle upward tilt |
| **2** | `00:08 - 00:16` | *Up above the world so high, like a diamond in the sky* | Pip floats on fluffy cloud over sleepy village into diamond stars; Twinkle glides in. | Crane-up and smooth forward drift |
| **3** | `00:16 - 00:24` | *When the sun has gone away, moon and stars come out to play* | Smiling sun sets behind green hills, waving goodbye; sky shifts to dusk; Pip waves back. | Slow panoramic pan across sunset horizon |
| **4** | `00:24 - 00:32` | *Then you shine your little light, twinkle softly through the night* | Stars ignite one by one; Twinkle shines brightest; Pip sways among glowing flowers. | Medium orbit around Pip tilting to star |
| **5** | `00:32 - 00:40` | *Then the traveller in the dark thanks you for your tiny spark* | Fox walks night forest with lantern; Twinkle beams light down; Fox bows thanks. | Slow tracking shot following Fox |
| **6** | `00:40 - 00:48` | *He could not see which way to go if you did not twinkle so* | Fox puzzled at wooden fork; Twinkle drops sparkling path; Fox follows happily. | Slight high-angle slow pull-back |
| **7** | `00:48 - 00:56` | *In the dark blue sky you keep, and often through my curtains peep* | Pip snug in bed; Twinkle peeks through curtains, winks; Pip giggles softly. | Slow dolly-in to cozy nursery bed |
| **8** | `00:56 - 01:04` | *You never shut your eye till the sun is in the sky* | Twinkle watches sleepy village as moon crosses and sunrise turns sky pink; Twinkle yawns. | Slow time-lapse sky pan to sunrise |
| **9** | `01:04 - 01:12` | *'Tis your bright and tiny spark lights the traveller in the dark* | Fox & Pip meet on starry hill; Twinkle wraps them in warm glow; Pip holds star gift. | Circular orbital pan around the 3 friends |
| **10** | `01:12 - 01:20` | *Though I know not what you are, twinkle, twinkle, little star* | Pip, Fox and Twinkle wave from cloud; camera pulls back into twinkling cosmos; fade out. | Wide cinematic pull-back (dolly-out) |

---

## 🎵 Audio and Local Animation

The finished local render is `Twinkle_Twinkle_Little_Star_Animated.mp4`.

To rebuild it:

1. Run `python generate_singing_track.py`. It creates an English sung vocal from the MusicXML score with the free Sinsy demo and saves `singing_vocals.wav`. The demo terms require the word ?Sinsy? to be shown when distributing generated vocals; the render includes that credit at the end.
2. Run `python make_singing_mix.py` to create the matching bell accompaniment and `mixed_singing.wav`. It fits the vocal to the video length and adds light warmth, compression, and room echo.
3. Run `.venv_animation\Scripts\python.exe build_local_animated_video.py` to animate character cutouts, drive mouth opening and broad vowel shapes from the sung vocal, and render the 80-second MP4.

The video animation and final render run locally on CPU. Vocal generation uses the free Sinsy web service, so it needs an internet connection and still sounds synthesized; a truly human voice requires a recorded singer. You can replace `singing_vocals.wav` with a singer recording before running the mix step. The mixer gently evens and warms the vocal, adds a small room echo, and fits the complete ending to the 80-second video. The mouth follows a smoothed vocal envelope and uses audio spectral brightness for broad vowel variation. This is an approximation, not exact phoneme timing or captured facial performance. Exact character-specific acting requires a driving video of those characters or a layered/rigged character model; a still illustration cannot provide that motion. The supplied reference clip is a visual style reference and has no audio stream.

* **Genre:** Toddler Lullaby / Nursery Rhyme
* **Tempo:** 120 BPM (4/4 time signature)
* **Instrumentation:** Music box, glockenspiel, orchestral concert harp, soft strings, toy shakers, gentle chimes.
* **Vocal Style:** Warm, soothing, whisper-soft female bedtime lullaby voice.
* **Prompt for Suno / Udio:**
  > `Gentle soothing female lullaby vocal singing Twinkle Twinkle Little Star, warm music box melody, glockenspiel sparkle, acoustic harp arpeggios, 90 bpm, dreamy nursery bedtime atmosphere, tender, peaceful, warm ambient reverb, pristine studio recording`
