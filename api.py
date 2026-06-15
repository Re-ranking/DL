import sys
from fastapi import FastAPI, UploadFile, File
import shutil
import subprocess
import json
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
CV_DIR = BASE_DIR / "cv_dataset_one"
RESULT_PATH = BASE_DIR / "result_json" / "ontology_match_result.json"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend")
async def recommend(file: UploadFile = File(...)):
    CV_DIR.mkdir(exist_ok=True)

    for old_file in CV_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()

    file_path = CV_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    subprocess.run([sys.executable, "ontology_match.py"], check=True)

    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return result