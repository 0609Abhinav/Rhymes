import json
import os
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:latest"

SYSTEM_PROMPT = """You are an expert children's 3D animation director and storyboard artist.
Given a prompt for a nursery rhyme or children's story, break it down into structured scenes.
Return ONLY valid JSON (no markdown fences, no explanatory text) with this format:
{
  "title": "Story Title",
  "characters": {
    "Pip": "Description of baby bunny character",
    "Twinkle": "Description of star character",
    "Fox": "Description of fox cub character"
  },
  "bpm": 90,
  "scenes": [
    {
      "scene_number": 1,
      "duration": 8,
      "lyric": "Lyric or voice narration line",
      "action": "Description of visual action and walking animation",
      "walking_character": "Pip",
      "walk_direction": "left_to_right",
      "camera": "Slow zoom in"
    }
  ]
}
"""

def generate_storyboard_with_mistral(user_prompt: str, num_scenes: int = 10, scene_dur: int = 8) -> dict:
    """Queries local Ollama Mistral model to generate a structured storyboard."""
    full_prompt = f"{SYSTEM_PROMPT}\nUser Prompt: {user_prompt}\nGenerate exactly {num_scenes} scenes of {scene_dur} seconds each."
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            },
            timeout=180
        )
        if response.status_code == 200:
            raw_text = response.json().get("response", "").strip()
            # Clean possible markdown wrap
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            data = json.loads(raw_text)
            if "scenes" in data and len(data["scenes"]) > 0:
                return data
    except Exception as e:
        print(f"[Ollama Mistral Warning]: {e}. Using intelligent fallback storyboard.")

    # Graceful intelligent fallback if Mistral is busy or offline
    return get_default_storyboard(user_prompt, num_scenes, scene_dur)

def get_default_storyboard(prompt: str, num_scenes: int = 10, scene_dur: int = 8) -> dict:
    lyrics = [
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
    actions = [
        ("Pip sits on windowsill gazing at Twinkle, head tilting with floating sparkle", "Pip", "bobbing"),
        ("Pip floats happily on fluffy cloud through glittering diamond stars", "Pip", "floating"),
        ("Smiling sun waves goodbye setting behind green hills as Pip waves back", "Pip", "waving"),
        ("Pip does a joyful toddler sway dance among glowing flowers and fireflies", "Pip", "dancing"),
        ("Fox walks along night forest path swinging his warm lantern, smiling up at Twinkle", "Fox", "walking_right"),
        ("Fox trots curiously down the sparkling stardust path illuminated by Twinkle", "Fox", "walking_right"),
        ("Pip snuggles in cozy bed as Twinkle peeks through window curtains and winks", "Pip", "sleeping"),
        ("Twinkle watches sleepy village as sunrise arrives, giving a sleepy cute yawn", "Twinkle", "floating"),
        ("Fox and Pip walk up the starry hill together to meet under Twinkle's light", "Fox_and_Pip", "walking_together"),
        ("Pip, Fox and Twinkle wave goodbye together from cloud pulling back to cosmos", "All", "waving")
    ]
    
    scenes = []
    for i in range(num_scenes):
        act_text, char, motion = actions[i % len(actions)]
        scenes.append({
            "scene_number": i + 1,
            "duration": scene_dur,
            "lyric": lyrics[i % len(lyrics)],
            "action": act_text,
            "walking_character": char,
            "motion_type": motion,
            "camera": "Slow cinematic move"
        })

    return {
        "title": "Twinkle Twinkle Little Star (3D Animated Nursery Rhyme)",
        "prompt": prompt,
        "bpm": 90,
        "characters": {
            "Pip": "Cream baby bunny with floppy ears and sky-blue star pyjamas",
            "Twinkle": "Smiling golden star with rosy cheeks and warm glow",
            "Fox": "Friendly orange cub with bushy tail and wooden lantern"
        },
        "scenes": scenes
    }
