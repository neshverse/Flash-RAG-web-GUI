from llama_cpp import Llama
import json
import re
from typing import List, Dict, Tuple, Optional
import pandas as pd

class StrictLLM:
    def __init__(self, model_path: str):
        print(f"🔄 Loading GGUF model: {model_path}")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            n_batch=512,
            verbose=False
        )
        print("✅ Model loaded")
    
    def generate_with_citations(self, query: str, evidence: List[Dict]) -> Dict:
        """Generate with mandatory citations and verification"""
        
        if not evidence:
            return {
                "found_in_evidence": False,
                "answer": "INSUFFICIENT_DATA: No relevant records found in database",
                "citations": [],
                "confidence": "none",
                "raw_values": {},
                "verification": {"total_claims": 0, "verified": 0, "unverified": 0}
            }
        
        # Build evidence string
        evidence_text = ""
        for i, ev in enumerate(evidence, 1):
            evidence_text += f"[{i}] {ev['document']}\n"
        
        # STRICT prompt
        prompt = f"""You are a STRICT data retrieval system. EXTRACT only from provided evidence. NO generation. NO inference.

RULES:
1. ONLY use information in evidence [1] through [{len(evidence)}]
2. If answer not found: say "INSUFFICIENT_DATA"
3. Cite EVERY fact with [number]
4. NO calculations unless shown in evidence
5. NO external knowledge

EVIDENCE:
{evidence_text}

USER QUESTION: {query}

RESPONSE FORMAT (JSON):
{{
    "found_in_evidence": true/false,
    "answer": "extracted answer or INSUFFICIENT_DATA message",
    "citations": [1, 2],
    "confidence": "high/medium/low/none",
    "raw_values": {{"field_name": "value"}}
}}

JSON:"""
        
        # Generate with zero temperature
        output = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.0,
            top_p=1.0,
            top_k=1,
            stop=["</s>", "User:", "Query:", "Human:"],
            echo=False
        )
        
        response_text = output['choices'][0]['text'].strip()
        
        # Parse JSON
        try:
            # Extract JSON block
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response_text)
        except:
            # Fallback parsing
            parsed = self._fallback_parse(response_text)
        
        # Validate
        validated = self._validate_response(parsed, evidence)
        return validated
    
    def _fallback_parse(self, text: str) -> Dict:
        """Parse non-JSON responses"""
        found = "insufficient" not in text.lower() and "not found" not in text.lower()
        
        # Extract citations
        citations = [int(n) for n in re.findall(r'\[(\d+)\]', text)]
        
        return {
            "found_in_evidence": found,
            "answer": text[:500],
            "citations": list(set(citations)),
            "confidence": "low" if found else "none",
            "raw_values": {}
        }
    
    def _validate_response(self, parsed: Dict, evidence: List[Dict]) -> Dict:
        """Verify claims against evidence"""
        
        answer = parsed.get('answer', '')
        citations = parsed.get('citations', [])
        
        # Clean citations
        citations = [c for c in citations if isinstance(c, int) and 1 <= c <= len(evidence)]
        parsed['citations'] = citations
        
        # Extract claims
        claims = self._extract_claims(answer)
        
        # Verify each claim
        verified = 0
        unverified = 0
        
        for claim in claims:
            claim_verified = False
            for cite_idx in citations:
                ev_doc = evidence[cite_idx - 1]['document']
                if self._claim_in_evidence(claim, ev_doc):
                    claim_verified = True
                    break
            
            if claim_verified:
                verified += 1
            else:
                unverified += 1
        
        # Update confidence
        if unverified > 0:
            parsed['confidence'] = 'low'
            parsed['warning'] = f'{unverified} claims unverified'
        elif verified == 0 and parsed.get('found_in_evidence'):
            parsed['confidence'] = 'medium'
        elif verified > 0:
            parsed['confidence'] = 'high'
        
        parsed['verification'] = {
            'total_claims': len(claims),
            'verified': verified,
            'unverified': unverified
        }
        
        return parsed
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims"""
        claims = []
        
        # Skip insufficient data messages
        if 'insufficient' in text.lower():
            return claims
        
        # Number patterns
        patterns = [
            r'\$\d[\d,]*(?:\.\d+)?',  # Currency
            r'\d[\d,]*(?:\.\d+)?\s*(?:units?|items?|products?)',
            r'\d+(?:\.\d+)?%',
            r'(?:increased|decreased|growth|decline)[^\.\n]*?\d+',
            r'(?:total|sum|revenue|sales)[^\.\n]*?\d+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            claims.extend(matches)
        
        return list(set(claims))
    
    def _claim_in_evidence(self, claim: str, evidence: str) -> bool:
        """Check claim against evidence"""
        # Normalize
        claim_norm = re.sub(r'[^\d]', '', claim)
        ev_norm = re.sub(r'[^\d]', '', evidence)
        
        if claim_norm and claim_norm in ev_norm:
            return True
        
        # Fuzzy match for text
        claim_clean = claim.lower().replace('$', '').replace(',', '').replace('%', '').strip()
        ev_clean = evidence.lower()
        
        return claim_clean in ev_clean
    
    def direct_lookup(self, query: str, df: pd.DataFrame) -> Optional[Dict]:
        """Bypass LLM for simple lookups"""
        
        # Pattern: "What is X for Y?" or "Value of X where Y=Z"
        patterns = [
            r'what\s+is\s+(?:the\s+)?(\w+)(?:\s+for|\s+of)?\s+(\w+)',
            r'(\w+)\s+(?:for|of)\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                field1, field2 = match.groups()
                
                # Find matching column
                for col in df.columns:
                    if field1 in col.lower():
                        # Find row where another field matches
                        for _, row in df.iterrows():
                            row_str = ' '.join(str(v).lower() for v in row.values)
                            if field2 in row_str:
                                value = row[col]
                                return {
                                    "found_in_evidence": True,
                                    "answer": f"{col} is {value}",
                                    "citations": [1],
                                    "confidence": "high",
                                    "raw_values": {col: str(value)},
                                    "method": "direct_lookup"
                                }
        
        return None