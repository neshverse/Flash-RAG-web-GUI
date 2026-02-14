from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    question: str
    strict_mode: bool = True  # Default to strict
    top_k: int = 5
    temperature: float = 0.0  # Always 0 for strict mode

class QueryResponse(BaseModel):
    query: str
    answer: str
    found_in_evidence: bool
    confidence: str
    citations: List[int]
    source_data: List[Dict[str, Any]]
    raw_values: Dict[str, str]
    retrieval_stats: Dict[str, Any]
    verification: Dict[str, int]
    warning: Optional[str] = None
    processing_time: float
    method: str

class StatsResponse(BaseModel):
    vector_store: Dict[str, Any]
    total_queries: int
    avg_confidence: Optional[float]
    found_rate: float

class UploadResponse(BaseModel):
    filename: str
    status: str
    rows_processed: int
    chunks_added: int