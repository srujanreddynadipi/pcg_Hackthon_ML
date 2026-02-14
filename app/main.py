"""
ITSM AI-Driven Intelligent Ticketing API
FastAPI application for hackathon demo
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
from datetime import datetime

# Import utilities
import sys
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.model_loader import ModelLoader
from utils.predictor import TicketPredictor
from utils.rag_engine import RAGEngine
from config.settings import API_TITLE, API_VERSION, API_DESCRIPTION

# Initialize FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models
models = None
predictor = None
rag_engine = None

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    global models, predictor, rag_engine
    
    print("🚀 Starting ITSM AI API...")
    print("📥 Loading models from HuggingFace...")
    
    # Load models
    loader = ModelLoader()
    models = loader.download_models()
    
    # Initialize predictor and RAG engine
    predictor = TicketPredictor(models)
    rag_engine = RAGEngine(models['sentence_bert'])
    
    print("✅ All models loaded successfully!")
    print("🎯 API ready to receive requests")

# Request/Response Models
class TicketRequest(BaseModel):
    user: str = Field(..., description="User who created the ticket")
    title: str = Field(..., description="Ticket title/summary")
    description: str = Field(..., description="Detailed ticket description")
    historical_tickets: Optional[List[Dict[str, Any]]] = Field(None, description="Historical tickets for duplicate detection")
    knowledge_base: Optional[List[Dict[str, Any]]] = Field(None, description="Knowledge base articles")

class TicketResponse(BaseModel):
    ticket_id: str
    predictions: Dict[str, Any]
    rag_insights: Dict[str, Any]
    audit_trail: Dict[str, Any]
    processing_time_ms: float
    timestamp: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": API_TITLE,
        "version": API_VERSION,
        "models_loaded": models is not None,
        "endpoints": ["/predict", "/health"]
    }

@app.get("/health")
async def health_check():
    """Health check with model status"""
    return {
        "status": "healthy",
        "models_loaded": models is not None,
        "predictor_ready": predictor is not None,
        "rag_engine_ready": rag_engine is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=TicketResponse)
async def predict_ticket(request: TicketRequest):
    """
    🎯 **Main Prediction Endpoint**
    
    Takes a ticket and returns:
    - Category prediction (11 categories)
    - Priority prediction (Critical/High/Medium/Low)
    - Resolver group routing (7 teams)
    - Duplicate detection (similar tickets)
    - Knowledge base search (relevant solutions)
    - Auto-draft response (resolution template)
    - Proactive insights (patterns, trends, SLA risks)
    - Detailed audit trail (reasoning + confidence)
    """
    
    if not models or not predictor or not rag_engine:
        raise HTTPException(status_code=503, detail="Models not loaded yet. Please wait...")
    
    start_time = time.time()
    
    try:
        # Generate ticket ID
        ticket_id = f"TICKET-{int(time.time() * 1000)}"
        
        # Handle empty title/description
        title = request.title.strip() if request.title else "No title provided"
        description = request.description.strip() if request.description else "No description provided"
        
        # 1. PREDICT CATEGORY (with confidence)
        category_result = predictor.predict_category(title, description)
        
        # 2. PREDICT PRIORITY (Impact × Urgency)
        priority_result = predictor.predict_priority(title, description, category_result['category'])
        
        # 3. PREDICT RESOLVER GROUP (ML-based routing)
        resolver_result = predictor.predict_resolver(
            title, 
            description,
            category_result['category'],
            priority_result['impact'],
            priority_result['urgency']
        )
        
        # 4. FIND DUPLICATES (Sentence-BERT similarity)
        duplicate_result = predictor.find_duplicates(
            title, 
            description, 
            request.historical_tickets
        )
        
        # 5. SEARCH KNOWLEDGE BASE (RAG)
        kb_result = rag_engine.search_knowledge_base(
            title,
            description,
            category_result['category'],
            request.knowledge_base
        )
        
        # 6. GENERATE AUTO-RESPONSE (template + KB)
        auto_response_result = rag_engine.generate_auto_response(
            category_result['category'],
            title,
            description,
            kb_result['kb_articles']
        )
        
        # 7. DETECT PATTERNS (recurring issues)
        pattern_result = rag_engine.detect_patterns(
            category_result['category'],
            duplicate_result['similar_tickets']
        )
        
        # 8. PROACTIVE INSIGHTS (SLA risk, recommendations)
        insights_result = rag_engine.generate_proactive_insights(
            category_result['category'],
            priority_result['priority'],
            duplicate_result['similar_tickets'],
            kb_result['kb_articles']
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Build comprehensive response
        response = {
            "ticket_id": ticket_id,
            "predictions": {
                "category": {
                    "predicted": category_result['category'],
                    "confidence": category_result['confidence'],
                    "top_3_predictions": category_result['top_3']
                },
                "priority": {
                    "predicted": priority_result['priority'],
                    "impact": priority_result['impact'],
                    "urgency": priority_result['urgency'],
                    "confidence": priority_result['confidence']
                },
                "resolver_group": {
                    "assigned_to": resolver_result['resolver_group'],
                    "confidence": resolver_result['confidence']
                },
                "duplicates": {
                    "has_duplicates": duplicate_result['has_duplicates'],
                    "count": duplicate_result['duplicate_count'],
                    "similar_tickets": duplicate_result['similar_tickets']
                }
            },
            "rag_insights": {
                "knowledge_base": {
                    "articles_found": len(kb_result['kb_articles']),
                    "has_solution": kb_result['has_known_solution'],
                    "articles": kb_result['kb_articles']
                },
                "auto_response": {
                    "draft": auto_response_result['auto_response'],
                    "confidence": auto_response_result['confidence'],
                    "kb_incorporated": auto_response_result['kb_incorporated']
                },
                "patterns": {
                    "detected": pattern_result['pattern_detected'],
                    "type": pattern_result['pattern_type'],
                    "insights": pattern_result['insights']
                },
                "proactive_insights": {
                    "insights": insights_result['insights'],
                    "count": insights_result['insight_count'],
                    "has_critical": insights_result['has_critical_insights']
                }
            },
            "audit_trail": {
                "category_reasoning": {
                    "top_features": category_result['feature_importance'][:5],
                    "keyword_matches": category_result['keyword_matches'],
                    "confidence_score": category_result['confidence']
                },
                "priority_reasoning": {
                    "explanation": priority_result['reasoning'],
                    "factors": {
                        "impact": priority_result['impact'],
                        "urgency": priority_result['urgency']
                    }
                },
                "resolver_reasoning": {
                    "explanation": resolver_result['reasoning'],
                    "mapping": "Category-based deterministic routing"
                },
                "duplicate_reasoning": {
                    "explanation": duplicate_result['reasoning'],
                    "method": "Sentence-BERT cosine similarity"
                },
                "kb_reasoning": {
                    "explanation": kb_result['reasoning'],
                    "method": "Embedding-based semantic search"
                }
            },
            "processing_time_ms": round(processing_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
