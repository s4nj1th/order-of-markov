from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os
import json

load_dotenv()

app = FastAPI(title="Order of Markov")

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
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not found in environment")
    
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
                    "max_tokens": 2000
                }
            )
            
            print(f"OpenRouter status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"OpenRouter error response: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API error: {response.text}"
                )
            
            result = response.json()
            print(f"Full API response: {result}")
            
            if not result.get("choices") or len(result["choices"]) == 0:
                print("ERROR: No choices in response")
                raise HTTPException(
                    status_code=500,
                    detail=f"No choices in API response: {result}"
                )
            
            finish_reason = result["choices"][0].get("finish_reason")
            if finish_reason == "length":
                print("WARNING: Response was truncated due to max_tokens limit")
            
            content = result["choices"][0]["message"]["content"]
            
            print(f"Raw LLM response: '{content}'")
            
            content = content.strip()
            
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()
            
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]
            else:
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            
            print(f"Extracted JSON: {content}")
            
            parsed = json.loads(content)
            
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
    return {"message": "Order of Markov API", "endpoint": "/api/analyze"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)