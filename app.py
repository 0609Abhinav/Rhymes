import os
import json
import threading
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai_engine
import video_engine
import git_engine

app = FastAPI(title="3D Nursery Rhyme Video AI Studio")

BASE_DIR = r"c:\Users\HP\Downloads\video generator"
STORYBOARD_FILE = os.path.join(BASE_DIR, "storyboard_and_prompts.json")
VIDEO_FILE = os.path.join(BASE_DIR, "Twinkle_Twinkle_Little_Star_3D.mp4")

# Mount static assets from React dist
REACT_DIST = os.path.join(BASE_DIR, "frontend", "dist")
if os.path.exists(REACT_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(REACT_DIST, "assets")), name="assets")

# Mount project files
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

# In-memory progress state
progress_state = {
    "status": "Ready",
    "percent": 0,
    "is_rendering": False
}

def update_progress(status: str, percent: int):
    progress_state["status"] = status
    progress_state["percent"] = percent

class StoryboardRequest(BaseModel):
    prompt: str
    num_scenes: int = 10
    scene_dur: int = 8

class VideoRenderRequest(BaseModel):
    voice: str = "en-US-JennyNeural"
    bpm: int = 90

class GitCommitRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
def index():
    react_index = os.path.join(REACT_DIST, "index.html")
    if os.path.exists(react_index):
        with open(react_index, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback to templates/index.html
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/storyboard")
def get_storyboard():
    if os.path.exists(STORYBOARD_FILE):
        with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenes": []}

@app.post("/api/generate-storyboard")
def generate_storyboard(req: StoryboardRequest):
    data = ai_engine.generate_storyboard_with_mistral(
        user_prompt=req.prompt,
        num_scenes=req.num_scenes,
        scene_dur=req.scene_dur
    )
    # Save storyboard
    with open(STORYBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Git track change
    git_engine.commit_changes(f"Mistral AI Storyboard generated for: {req.prompt[:40]}...")
    return data

def run_render_task(voice: str, bpm: int):
    progress_state["is_rendering"] = True
    update_progress("Starting animated walking & vocal pipeline...", 5)
    try:
        with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
            sb = json.load(f)
        sb["bpm"] = bpm
        video_engine.render_full_video_pipeline(sb, voice=voice, progress_cb=update_progress)
        # Git track newly rendered video
        git_engine.commit_changes(f"Rendered video with {voice} vocals and walking animation (BPM {bpm})")
    except Exception as e:
        print(f"Render error: {e}")
        update_progress(f"Error: {e}", 100)
    finally:
        progress_state["is_rendering"] = False

@app.post("/api/generate-video")
def generate_video(req: VideoRenderRequest, bg: BackgroundTasks):
    if progress_state["is_rendering"]:
        return JSONResponse({"status": "Already rendering", "percent": progress_state["percent"]})
    
    bg.add_task(run_render_task, req.voice, req.bpm)
    return {"status": "Rendering started"}

@app.get("/api/progress")
def get_progress():
    return progress_state

@app.get("/api/video")
def get_video():
    if os.path.exists(VIDEO_FILE):
        return FileResponse(VIDEO_FILE, media_type="video/mp4")
    return JSONResponse({"error": "Video not found"}, status_code=404)

@app.get("/api/git-history")
def get_git_history():
    commits = git_engine.get_git_history()
    return {"commits": commits}

@app.post("/api/git-commit")
def commit_checkpoint(req: GitCommitRequest):
    success = git_engine.commit_changes(req.message)
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
