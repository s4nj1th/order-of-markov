from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from services.llm_service import LLMService

load_dotenv()

app = FastAPI(
    title="Order of Markov API",
    description="AI-powered Markov model order recommendation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()


class ProblemRequest(BaseModel):
    problem: str = Field(..., min_length=10, description="Problem description (minimum 10 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem": "I want to predict weather patterns based on historical data"
            }
        }


class AnalysisResponse(BaseModel):
    order: int = Field(..., ge=1, le=5, description="Recommended Markov model order (1-5)")
    justification: str = Field(..., description="Explanation for the recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order": 3,
                "justification": "Natural language generation benefits from higher-order context...",
                "confidence": 0.85
            }
        }


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Order of Markov API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_problem(request: ProblemRequest):
    try:
        result = await llm_service.analyze_problem(request.problem)
        
        order = max(1, min(5, result.get("order", 2)))
        confidence = max(0.0, min(1.0, result.get("confidence", 0.7)))
        justification = result.get("justification", "Analysis completed.")
        
        return AnalysisResponse(
            order=order,
            justification=justification,
            confidence=confidence
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse LLM response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

# Test endpoint with hardcoded responses for development purposes
# @app.post("/api/analyze/test", response_model=AnalysisResponse)
# async def analyze_problem_test(request: ProblemRequest):
#     problem_lower = request.problem.lower()
    
#     if any(word in problem_lower for word in ['weather', 'stock', 'time series']):
#         return AnalysisResponse(
#             order=2,
#             justification="Weather and financial data often show dependencies on the previous two states. Recent conditions strongly influence the next state, making a 2nd-order model appropriate.",
#             confidence=0.85
#         )
#     elif any(word in problem_lower for word in ['text', 'language', 'sentence']):
#         return AnalysisResponse(
#             order=3,
#             justification="Natural language generation benefits from higher-order context. A 3rd-order model captures grammatical patterns effectively while remaining computationally feasible.",
#             confidence=0.82
#         )
#     elif any(word in problem_lower for word in ['game', 'chess', 'strategy']):
#         return AnalysisResponse(
#             order=4,
#             justification="Strategic games require deeper history to make informed predictions. A 4th-order model captures complex patterns and strategic dependencies.",
#             confidence=0.78
#         )
#     else:
#         return AnalysisResponse(
#             order=2,
#             justification="Based on the problem description, a 2nd-order model provides a good balance between capturing dependencies and computational efficiency.",
#             confidence=0.70
#         )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
