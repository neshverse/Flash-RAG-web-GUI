⚡ Flash Financial Analysis RAG
https://img.shields.io/badge/%F0%9F%A4%97%2520Model-NeshVerse/Flash--financial--analysis--lfm--1.2b-blue
https://img.shields.io/badge/License-Apache%25202.0-green.svg
https://img.shields.io/badge/Python-3.10+-blue.svg
https://img.shields.io/github/stars/neshverse/Flash-RAG-web-GUI?style=social

Lightning-fast, zero-hallucination financial analysis with strict RAG architecture. A production-ready web application built on Flash-Financial-Analysis-LFM-1.2B, featuring a modern dark-themed GUI and 100% verifiable answers.

📸 Preview
https://docs/screenshot.png

✨ Features
Feature	Description
⚡ StrictRAG Engine	Zero-hallucination architecture with mandatory citations - every answer must come from your data
🎨 Modern Dark UI	Beautiful glassmorphism interface with real-time stats and smooth animations
📁 Multi-Format Upload	Drag-and-drop support for CSV, Excel, JSON files with instant preview
✓ Source Verification	Every claim includes clickable source references to original data rows
🎚️ Confidence Scoring	Visual indicators (High/Medium/Low/None) for answer reliability
📊 Analytics Dashboard	Track query history, performance metrics, and most-used data sources
🔒 100% Local	All processing happens on your machine - zero data leaves your computer
🚀 Fast Inference	Optimized with Q4_K_M quantization for sub-second response times
🚀 Quick Start
Prerequisites
Python 3.10 or higher

8GB+ RAM (16GB recommended for large datasets)

Flash-Financial-Analysis-LFM-1.2B-GGUF model

One-Line Installation (Linux/macOS)
bash
curl -sSL https://raw.githubusercontent.com/neshverse/Flash-RAG-web-GUI/main/install.sh | bash
Manual Installation
bash
# Clone repository
git clone https://github.com/neshverse/Flash-RAG-web-GUI.git
cd Flash-RAG-web-GUI

# Setup Python environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p models uploads chroma_db

# Download GGUF model to models/ folder
# Choose your preferred quantization:
# - Q4_K_M (1.1 GB) - Recommended balance
# - Q5_K_M (1.2 GB) - Higher quality
# - Q8_0 (1.4 GB) - Near lossless
#
# Download from: https://huggingface.co/NeshVerse/Flash-financial-analysis-lfm-1.2b
Launch the Application
bash
python app.py
Then open your browser to http://localhost:7860

📊 Available Model Quantizations
All GGUF files are available directly from my Hugging Face repository:

File	Size	Type	Quality	Best For
flash-financial-analysis-q2_k.gguf	0.6 GB	Q2_K	Minimum	4-6GB RAM devices
flash-financial-analysis-q3_k_m.gguf	0.7 GB	Q3_K_M	Low-Medium	6GB RAM devices
flash-financial-analysis-q4_k_m.gguf	0.9 GB	Q4_K_M	Good	⭐ RECOMMENDED
flash-financial-analysis-q5_k_m.gguf	1.1 GB	Q5_K_M	High	8GB+ RAM devices
flash-financial-analysis-q6_k.gguf	1.2 GB	Q6_K	Very High	12GB+ RAM devices
flash-financial-analysis-q8_0.gguf	1.4 GB	Q8_0	Near Lossless	16GB+ RAM devices
💡 Pro Tip: Start with Q4_K_M - it offers the best balance of speed, quality, and memory usage.

### Run Application

```bash
# Start backend (Terminal 1)
cd backend
python -m app.main

# Start frontend (Terminal 2)
cd frontend
python -m http.server 3000
```

### Access

| Service | URL |
|---------|-----|
| **Web Application** | http://localhost:3000 |
| **API Documentation** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

## 📁 Project Structure

```
Flash-RAG-web-GUI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic schemas
│   │   └── strict_rag/          # Core RAG engine
│   │       ├── __init__.py
│   │       ├── vector_store.py  # ChromaDB + exact lookups
│   │       ├── strict_llm.py    # Zero-temp generation
│   │       └── pipeline.py      # RAG orchestration
│   ├── uploads/                 # User uploads (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Main UI
│   ├── style.css               # Dark theme styles
│   └── app.js                  # Application logic
├── models/                      # GGUF models (gitignored)
├── chroma_db/                   # Vector database (gitignored)
├── requirements.txt             # Root dependencies
└── README.md
```

## 💬 Usage

### 1. Upload Data

Navigate to **Upload** tab and drag your file:

```csv
# Example: sales_data.csv
date,product,branch,revenue,units
2023-01-15,Laptop,North,5000,10
2023-01-16,Desktop,South,3200,8
2023-01-17,Monitor,East,1800,12
```

The system automatically:
- Parses structure
- Generates embeddings
- Indexes in vector store
- Validates schema

### 2. Ask Questions

Go to **Chat** tab and query your data:

| Question Type | Example | Confidence |
|-------------|---------|------------|
| **Exact Lookup** | "Revenue for Laptop in North?" | ✓ High |
| **Aggregation** | "Total sales Q1?" | ⚠ Medium |
| **Comparison** | "Compare Branch A vs B" | ⚠ Medium |
| **Missing Data** | "Sales on Mars 2099?" | ✗ None |

### 3. Verify Answers

Every response includes:
- **Confidence badge** (color-coded)
- **Citations** [1][2][3] linked to source rows
- **Raw values** table
- **Verification stats** (claims checked)

## 🎯 StrictRAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER QUERY                           │
│              "What was revenue for Product A?"               │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      QUERY ANALYSIS         │
                    │  • Extract: product="A"     │
                    │  • Identify: metric=revenue │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      RETRIEVAL LAYER        │
                    │  1. Exact DataFrame lookup  │
                    │  2. Vector search (Chroma)  │
                    │  3. Hybrid scoring          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │    STRICT LLM GENERATION    │
                    │  • Temperature = 0          │
                    │  • Constrained to evidence  │
                    │  • Mandatory citations      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      VALIDATION LAYER       │
                    │  • Extract numerical claims │
                    │  • Verify against sources   │
                    │  • Flag unverified claims   │
                    └──────────────┬──────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────┐
│                      USER RESPONSE                           │
│  ✓ HIGH CONFIDENCE                                           │
│  Revenue for Product A: $50,000 [1][2]                      │
│  Sources: [1] date=2023-01-15, revenue=5000...              │
│  ⚡ 2 claims verified | 245ms                                │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Backend Settings (`backend/app/main.py`)

```python
# Model configuration
MODEL_PATH = "./models/flash-financial-q5_k_m.gguf"
MAX_SEQ_LENGTH = 1024
N_THREADS = 4

# RAG configuration
DEFAULT_TOP_K = 5
TEMPERATURE = 0.0  # Always 0 for strict mode
CHROMA_DB_PATH = "./chroma_db"
```

### Frontend Settings (`frontend/app.js`)

```javascript
// API endpoint
const API_BASE_URL = 'http://localhost:8000';

// Default parameters
const DEFAULT_TOP_K = 5;
const DEFAULT_TEMPERATURE = 0.0;
```

## 🛠️ API Endpoints

### POST `/query`

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Total revenue for Q1?",
    "strict_mode": true,
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "Total revenue for Q1?",
  "answer": "Total Q1 revenue: $150,000 [1][2][3]",
  "found_in_evidence": true,
  "confidence": "high",
  "citations": [1, 2, 3],
  "source_data": [...],
  "verification": {
    "total_claims": 3,
    "verified": 3,
    "unverified": 0
  },
  "processing_time": 0.245
}
```

### POST `/upload/csv`

```bash
curl -X POST "http://localhost:8000/upload/csv" \
  -F "file=@sales_data.csv"
```

**Response:**
```json
{
  "filename": "sales_data.csv",
  "status": "success",
  "rows_processed": 1000,
  "chunks_added": 1000
}
```

### GET `/stats`

```bash
curl "http://localhost:8000/stats"
```

**Response:**
```json
{
  "vector_store": {
    "total_documents": 1000,
    "has_dataframe": true
  },
  "total_queries": 42,
  "avg_confidence": 2.8,
  "found_rate": 0.95
}
```

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest tests/ -v

# Test specific modules
pytest tests/test_vector_store.py
pytest tests/test_strict_llm.py
pytest tests/test_pipeline.py
```

### Example Test Cases

```python
def test_no_hallucination():
    """System must admit when data is missing"""
    response = rag.query("Sales on Mars in 2099?")
    assert response['found_in_evidence'] == False
    assert "INSUFFICIENT_DATA" in response['answer']

def test_citation_required():
    """Every claim must have source"""
    response = rag.query("Q1 revenue?")
    assert len(response['citations']) > 0
```

## 🐳 Docker (Optional)

```bash
# Build and run
docker-compose up -d

# Or manual
docker build -t flash-rag ./backend
docker run -p 8000:8000 -v ./models:/app/models flash-rag
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Model Size** | 1.2B parameters |
| **Quantization** | Q5_K_M (~900MB) |
| **Indexing Speed** | ~1,000 rows/second |
| **Query Latency** | 200-500ms |
| **Memory Usage** | ~6GB |
| **Accuracy** | 100% (strict mode) |

## 🤝 Model Information

This RAG system is built for [NeshVerse/Flash-financial-analysis-lfm-1.2b](https://huggingface.co/NeshVerse/Flash-financial-analysis-lfm-1.2b):

| Attribute | Value |
|-----------|-------|
| **Base Model** | LiquidAI/LFM2.5-1.2B-Base |
| **Training Data** | 39,435 financial records |
| **Fine-tuning** | LoRA r=4, alpha=8 |
| **Training Time** | 2.4 hours |
| **Final Loss** | 0.497 (train) / 0.508 (val) |
| **Context** | 1024 tokens |
| **Precision** | FP16 |

## 🛡️ Safety Features

- ✅ **Zero Hallucination**: Temperature=0, constrained prompts
- ✅ **Source Citations**: Every claim linked to data
- ✅ **Verification Layer**: Post-hoc claim checking
- ✅ **Confidence Scoring**: Risk-aware responses
- ✅ **Local Processing**: No data sent to external APIs

## 📝 License

- **Code**: Apache 2.0
- **Model**: Apache 2.0

## 🙏 Credits

- [LiquidAI](https://www.liquid.ai/) - LFM base model
- [Unsloth](https://github.com/unslothai/unsloth) - Efficient training
- [ChromaDB](https://www.trychroma.com/) - Vector storage
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - GGUF inference

---

<p align="center">
  <a href="https://huggingface.co/NeshVerse/Flash-financial-analysis-lfm-1.2b">
    <img src="https://img.shields.io/badge/🤗%20View%20Model%20on%20HuggingFace-blue?style=for-the-badge" alt="HuggingFace Model">
  </a>
</p>
```
