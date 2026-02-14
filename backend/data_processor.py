import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import json

class FinancialDataProcessor:
    """Process and optimize financial data for vector storage"""
    
    def __init__(self):
        self.processing_stats = {}
    
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """Load and validate CSV"""
        df = pd.read_csv(filepath)
        print(f"📊 Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns)}")
        return df
    
    def load_excel(self, filepath: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Load Excel with multiple sheet support"""
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        else:
            # Load first sheet by default
            xls = pd.ExcelFile(filepath)
            print(f"📑 Available sheets: {xls.sheet_names}")
            df = pd.read_excel(filepath, sheet_name=0)
        
        print(f"📊 Loaded {len(df)} rows from Excel")
        return df
    
    def load_json(self, filepath: str) -> pd.DataFrame:
        """Load JSON/JSONL"""
        try:
            # Try JSON first
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        except:
            # Try JSONL
            records = []
            with open(filepath, 'r') as f:
                for line in f:
                    records.append(json.loads(line))
            df = pd.DataFrame(records)
        
        print(f"📊 Loaded {len(df)} records from JSON")
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data"""
        original_count = len(df)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Handle missing values
        df = df.fillna({
            col: 0 if df[col].dtype in ['int64', 'float64'] else 'Unknown'
            for col in df.columns
        })
        
        # Convert date columns
        for col in df.columns:
            if 'date' in col or 'time' in col:
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass
        
        self.processing_stats['cleaning'] = {
            'original_rows': original_count,
            'final_rows': len(df),
            'removed': original_count - len(df)
        }
        
        print(f"🧹 Cleaned: {original_count} → {len(df)} rows")
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add computed fields for better retrieval"""
        
        # Detect numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Add summary statistics as text
        if len(numeric_cols) > 0:
            df['data_summary'] = df.apply(
                lambda row: self._create_summary(row, numeric_cols), 
                axis=1
            )
        
        # Add search-friendly text
        df['search_text'] = df.apply(
            lambda row: ' | '.join([f"{k}={v}" for k, v in row.items() if pd.notna(v)]),
            axis=1
        )
        
        print(f"✨ Enriched data with computed fields")
        return df
    
    def _create_summary(self, row, numeric_cols) -> str:
        """Create natural language summary of numeric data"""
        parts = []
        for col in numeric_cols:
            if pd.notna(row[col]):
                val = row[col]
                if isinstance(val, (int, float)):
                    if val > 1000000:
                        parts.append(f"{col}: ${val/1000000:.2f}M")
                    elif val > 1000:
                        parts.append(f"{col}: ${val/1000:.1f}K")
                    else:
                        parts.append(f"{col}: {val}")
        return "; ".join(parts)
    
    def chunk_large_dataset(self, df: pd.DataFrame, chunk_size: int = 1000) -> List[pd.DataFrame]:
        """Split large datasets for batch processing"""
        chunks = []
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size].copy()
            chunks.append(chunk)
        print(f"📦 Split into {len(chunks)} chunks of {chunk_size}")
        return chunks
    
    def get_stats(self) -> Dict:
        """Return processing statistics"""
        return self.processing_stats


# Usage
if __name__ == "__main__":
    processor = FinancialDataProcessor()
    
    # Load
    df = processor.load_csv("sales_data.csv")
    # or: df = processor.load_excel("data.xlsx")
    # or: df = processor.load_json("records.json")
    
    # Process
    df = processor.clean_data(df)
    df = processor.enrich_data(df)
    
    # Save processed
    df.to_csv("processed_data.csv", index=False)
    print(f"💾 Saved processed data")