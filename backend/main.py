from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os
import json

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Markov Order Analyzer")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    problem: str

class AnalyzeResponse(BaseModel):
    order: int
    justification: str
    confidence: float

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_markov_order(request: AnalyzeRequest):
    """
    Analyze the problem and determine the appropriate Markov model order.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not found in environment")
    
    # Construct the prompt for the LLM
    prompt = f"""Analyze the following problem and determine the most appropriate order for a Markov model.

Problem: {request.problem}

Respond ONLY with a JSON object in the following format (no additional text, preamble, or markdown):
{{
    "order": <integer from 1-5>,
    "justification": "<brief explanation of why this order is appropriate>",
    "confidence": <float between 0 and 1>
}}

Consider:
- Order 1 (first-order): Current state depends only on the previous state
- Order 2 (second-order): Current state depends on the previous 2 states
- Higher orders: Current state depends on more historical states

Choose the order that best balances model complexity with the problem's temporal dependencies."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            print(f"OpenRouter status code: {response.status_code}")
            print(f"OpenRouter response: {response.text}")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API error: {response.text}"
                )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Debug: print raw response
            print(f"Raw LLM response: {content}")
            
            # Clean up the response (remove markdown code blocks if present)
            content = content.strip()
            
            # DeepSeek R1 may include reasoning tags, extract JSON from them
            if "<think>" in content:
                # Remove thinking section
                content = content.split("</think>")[-1].strip()
            
            # Try to find JSON object in the content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]
            else:
                # Fallback: remove markdown code blocks
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            
            print(f"Extracted JSON: {content}")
            
            # Parse the JSON response
            parsed = json.loads(content)
            
            # Validate and return
            return AnalyzeResponse(
                order=parsed["order"],
                justification=parsed["justification"],
                confidence=parsed["confidence"]
            )
            
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response as JSON: {str(e)}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to OpenRouter: {str(e)}"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected response format from LLM: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Markov Order Analyzer API", "endpoint": "/api/analyze"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)