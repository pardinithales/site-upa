from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import os
import sys
import json
from datetime import datetime

# Adiciona o diretório scripts ao Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_data_both import extract_from_pdf, extract_from_excel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        all_data = []
        for file in files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            if file.filename.endswith('.pdf'):
                data = extract_from_pdf(file_path)
                if data:
                    all_data.extend(json.loads(data))
            elif file.filename.endswith('.xlsx'):
                data = extract_from_excel(file_path)
                if data:
                    all_data.extend(json.loads(data))
            
            os.remove(file_path)
            
        return {"status": "success", "data": all_data}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def read_root():
    return {"message": "API está funcionando"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)