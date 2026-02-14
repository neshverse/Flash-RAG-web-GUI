import pandas as pd
from typing import Dict, List, Optional
import json
import time

from .vector_store import StrictVectorStore
from .strict_llm import StrictLLM

class StrictRAG:
    def __init__(self, llm_path: str, db_path: str = "./strict_db"):
        self.vector_store = StrictVectorStore(db_path)
        self.llm = StrictLLM(llm_path)
        self.query_history: List[Dict] = []
    
    def ingest_data(self, df: pd.DataFrame) -> int:
        """Load data into system"""
        count = self.vector_store.load_dataframe(df)
        print(f"✅ Indexed {count} records")
        return count
    
    def query(self, question: str, strict_mode: bool = True) -> Dict:
        """
        Execute strict RAG query
        
        Args:
            question: User query
            strict_mode: If True, never hallucinate; return INSUFFICIENT_DATA if not found
        """
        start_time = time.time()
        
        # Step 1: Try direct lookup (fastest)
        if self.vector_store.dataframe is not None:
            direct = self.llm.direct_lookup(question, self.vector_store.dataframe)
            if direct:
                direct['processing_time'] = time.time() - start_time
                self.query_history.append(direct)
                return direct
        
        # Step 2: Hybrid retrieval
        retrieval = self.vector_store.hybrid_search(question, n_results=10)
        
        if not retrieval['results']:
            result = {
                "query": question,
                "answer": "INSUFFICIENT_DATA: No relevant records found in database",
                "found_in_evidence": False,
                "confidence": "none",
                "citations": [],
                "source_data": [],
                "retrieval_stats": {"candidates": 0},
                "processing_time": time.time() - start_time,
                "method": "retrieval_failed"
            }
            self.query_history.append(result)
            return result
        
        # Step 3: Strict LLM generation
        llm_response = self.llm.generate_with_citations(
            question,
            retrieval['results']
        )
        
        # Step 4: Build final result
        result = {
            "query": question,
            "answer": llm_response['answer'],
            "found_in_evidence": llm_response['found_in_evidence'],
            "confidence": llm_response['confidence'],
            "citations": llm_response['citations'],
            "source_data": [
                retrieval['results'][i-1]['source_data']
                for i in llm_response.get('citations', [])
                if 1 <= i <= len(retrieval['results'])
            ],
            "raw_values": llm_response.get('raw_values', {}),
            "retrieval_stats": {
                "candidates": retrieval['total_candidates'],
                "entities_found": retrieval['entities_found']
            },
            "verification": llm_response.get('verification', {}),
            "warning": llm_response.get('warning'),
            "processing_time": time.time() - start_time,
            "method": "strict_rag"
        }
        
        self.query_history.append(result)
        return result
    
    def get_stats(self) -> Dict:
        """System statistics"""
        return {
            "vector_store": self.vector_store.get_stats(),
            "total_queries": len(self.query_history),
            "avg_confidence": self._calculate_avg_confidence(),
            "found_rate": self._calculate_found_rate()
        }
    
    def _calculate_avg_confidence(self) -> Optional[float]:
        if not self.query_history:
            return None
        
        scores = {'high': 3, 'medium': 2, 'low': 1, 'none': 0}
        total = sum(scores.get(q.get('confidence'), 0) for q in self.query_history)
        return total / len(self.query_history)
    
    def _calculate_found_rate(self) -> float:
        if not self.query_history:
            return 0.0
        
        found = sum(1 for q in self.query_history if q.get('found_in_evidence'))
        return found / len(self.query_history)