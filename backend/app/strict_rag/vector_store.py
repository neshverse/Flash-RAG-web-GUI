import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import re
import json
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

class StrictVectorStore:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="strict_financial",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dataframe: Optional[pd.DataFrame] = None
        self.schema: Dict = {}
    
    def load_dataframe(self, df: pd.DataFrame, text_column: str = None) -> int:
        """Load structured data with schema awareness"""
        self.dataframe = df.copy()
        
        # Infer schema
        self.schema = {
            'columns': list(df.columns),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'date_columns': df.select_dtypes(include=['datetime64']).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'sample_values': {col: df[col].dropna().head(3).tolist() for col in df.columns}
        }
        
        # Create structured text representations
        texts = []
        metadatas = []
        
        for idx, row in df.iterrows():
            text_parts = []
            for col in df.columns:
                if pd.notna(row[col]):
                    text_parts.append(f"{col}={row[col]}")
            
            text = " | ".join(text_parts)
            texts.append(text)
            
            # Store full source data
            source_dict = row.to_dict()
            # Convert all values to strings for JSON serialization
            source_dict = {k: str(v) if pd.notna(v) else "" for k, v in source_dict.items()}
            
            metadatas.append({
                'row_index': int(idx),
                'source_data': json.dumps(source_dict),
                **{f"field_{k}": str(v) for k, v in source_dict.items()}
            })
        
        # Add to vector store in batches
        batch_size = 1000
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            batch_texts = texts[i:end]
            batch_meta = metadatas[i:end]
            batch_ids = [f"row_{j}" for j in range(i, end)]
            
            embeddings = self.embedder.encode(batch_texts).tolist()
            
            self.collection.add(
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_meta,
                ids=batch_ids
            )
        
        return len(texts)
    
    def exact_lookup(self, field: str, value) -> List[Dict]:
        """Exact field-value match from dataframe"""
        if self.dataframe is None or field not in self.dataframe.columns:
            return []
        
        matches = self.dataframe[self.dataframe[field].astype(str) == str(value)]
        return matches.to_dict('records')
    
    def hybrid_search(self, query: str, filters: Dict = None, n_results: int = 5) -> Dict:
        """Vector search + exact match boosting"""
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Vector search
        query_embed = self.embedder.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embed,
            n_results=min(n_results * 3, 100),  # Get more for filtering
            where=filters,
            include=["documents", "metadatas", "distances"]
        )
        
        # Score and boost
        scored_results = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            score = 1 - dist
            
            # Boost exact entity matches
            for entity_type, entity_value in entities.items():
                if str(entity_value).lower() in doc.lower():
                    score += 0.15
            
            try:
                source_data = json.loads(meta.get('source_data', '{}'))
            except:
                source_data = {}
            
            scored_results.append({
                'document': doc,
                'metadata': meta,
                'score': min(score, 1.0),
                'source_data': source_data
            })
        
        # Sort and return top
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results[:n_results],
            'entities_found': entities,
            'total_candidates': len(scored_results)
        }
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract filter entities from query"""
        entities = {}
        query_lower = query.lower()
        
        # Date patterns
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            entities['year'] = year_match.group(1)
        
        quarter_match = re.search(r'\b(Q[1-4])\b', query, re.IGNORECASE)
        if quarter_match:
            entities['quarter'] = quarter_match.group(1).upper()
        
        # Check against dataframe values if loaded
        if self.dataframe is not None:
            for col in self.dataframe.columns:
                if col in ['year', 'quarter', 'month']:
                    continue
                    
                # Check unique values (limit to top 50 for performance)
                unique_vals = self.dataframe[col].dropna().unique()[:50]
                for val in unique_vals:
                    val_str = str(val).lower()
                    if len(val_str) > 2 and val_str in query_lower:
                        entities[col] = val
                        break
        
        return entities
    
    def sql_query(self, conditions: List[Tuple]) -> pd.DataFrame:
        """Execute pandas query with SQL-like conditions"""
        if self.dataframe is None:
            return pd.DataFrame()
        
        result = self.dataframe
        for col, op, val in conditions:
            if col not in result.columns:
                continue
                
            if op == '==':
                result = result[result[col].astype(str) == str(val)]
            elif op == '>':
                result = result[pd.to_numeric(result[col], errors='coerce') > float(val)]
            elif op == '<':
                result = result[pd.to_numeric(result[col], errors='coerce') < float(val)]
            elif op == 'contains':
                result = result[result[col].astype(str).str.contains(str(val), case=False, na=False)]
        
        return result
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        return {
            'total_documents': self.collection.count(),
            'schema': self.schema,
            'has_dataframe': self.dataframe is not None
        }