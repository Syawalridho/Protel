from fastapi import FastAPI, File, UploadFile
import os
import shutil

app = FastAPI()
UPLOAD_DIR = "tree_results_uploaded"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-tree-detection")
async def upload_tree_detection(file: UploadFile = File(...)):
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "success", "message": f"File saved to {save_path}"}
