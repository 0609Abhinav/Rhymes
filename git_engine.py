import subprocess
import os

REPO_DIR = r"c:\Users\HP\Downloads\video generator"

def get_git_history():
    """Returns list of recent git commits."""
    try:
        cmd = ["git", "log", "-n", "15", "--pretty=format:%h|%an|%ar|%s"]
        res = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")
        commits = []
        for line in lines:
            if "|" in line:
                parts = line.split("|", 3)
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return commits
    except Exception as e:
        print(f"Git log error: {e}")
        return []

def commit_changes(message: str) -> bool:
    """Stages all changes and commits them with a tracking message."""
    try:
        subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
        cmd = ["git", "commit", "-m", message]
        res = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True)
        return res.returncode == 0 or "nothing to commit" in res.stdout
    except Exception as e:
        print(f"Git commit error: {e}")
        return False

def get_git_status():
    """Returns working tree status."""
    try:
        res = subprocess.run(["git", "status", "--short"], cwd=REPO_DIR, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        return str(e)
