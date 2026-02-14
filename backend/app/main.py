from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
import pandas as pd
import json

from .models import QueryRequest, QueryResponse, StatsResponse, UploadResponse
from .strict_rag import StrictRAG

app = FastAPI(
    title="Flash Financial StrictRAG",
    description="Zero-hallucination financial analysis",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG instance
rag: StrictRAG = None

@app.on_event("startup")
async def startup():
    global rag
    
    model_path = os.getenv("MODEL_PATH", "./models/flash-financial-q5_k_m.gguf")
    
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        print("   Starting in demo mode (queries will fail)")
    
    rag = StrictRAG(
        llm_path=model_path,
        db_path="./strict_db"
    )
    
    # Load sample data if exists
    if os.path.exists("sample_data.csv"):
        df = pd.read_csv("sample_data.csv")
        rag.ingest_data(df)
    
    print("✅ StrictRAG initialized")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": rag is not None,
        "has_data": rag.vector_store.get_stats()['total_documents'] > 0 if rag else False
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Strict RAG query - zero hallucination"""
    if not rag:
        raise HTTPException(503, "RAG not initialized")
    
    try:
        result = rag.query(
            question=request.question,
            strict_mode=request.strict_mode
        )
        return QueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/upload/csv", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload and index CSV/Excel data"""
    if not rag:
        raise HTTPException(503, "RAG not initialized")
    
    allowed = ['.csv', '.xlsx', '.xls', '.json']
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed:
        raise HTTPException(400, f"Only {allowed} files allowed")
    
    try:
        # Save file
        os.makedirs("./uploads", exist_ok=True)
        path = f"./uploads/{file.filename}"
        
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Load based on extension
        if ext == '.csv':
            df = pd.read_csv(path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(path)
        else:  # json
            df = pd.read_json(path)
        
        # Index
        count = rag.ingest_data(df)
        
        return UploadResponse(
            filename=file.filename,
            status="success",
            rows_processed=len(df),
            chunks_added=count
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/stats", response_model=StatsResponse)
async def stats():
    """Get system statistics"""
    if not rag:
        raise HTTPException(503, "RAG not initialized")
    
    return StatsResponse(**rag.get_stats())

@app.post("/reset")
async def reset():
    """Clear all data"""
    if not rag:
        raise HTTPException(503, "RAG not initialized")
    
    import shutil
    shutil.rmtree("./strict_db", ignore_errors=True)
    shutil.rmtree("./uploads", ignore_errors=True)
    
    # Reinitialize
    global rag
    rag = StrictRAG(
        llm_path=os.getenv("MODEL_PATH", "./models/flash-financial-q5_k_m.gguf"),
        db_path="./strict_db"
    )
    
    return {"status": "reset_complete"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)