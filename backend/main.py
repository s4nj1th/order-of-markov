from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import os
import json

load_dotenv()

app = FastAPI(title="Markov Order Analyzer")

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

    url = "https://openrouter.ai/api/v1/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
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

            status = response.status_code
            text = response.text
            print(f"OpenRouter URL: {url}")
            print(f"OpenRouter status code: {status}")
            print(f"OpenRouter response text: {text}")

            if status != 200:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"OpenRouter API returned non-200 status. url={url} status={status} "
                        f"response={text}"
                    )
                )

            try:
                result = response.json()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Failed to decode OpenRouter JSON response. url={url} "
                        f"status={status} error={type(e).__name__}:{str(e)} response_text={text}"
                    )
                )

            try:
                content = result["choices"][0]["message"]["content"]
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"OpenRouter response missing expected fields. url={url} "
                        f"status={status} error={type(e).__name__}:{str(e)} result_keys={list(result.keys())} "
                        f"response_text={text}"
                    )
                )

            print(f"Raw LLM response: {content}")

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

            try:
                parsed = json.loads(content)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Failed to parse JSON extracted from LLM content. url={url} "
                        f"error={type(e).__name__}:{str(e)} extracted_text={content}"
                    )
                )

            try:
                return AnalyzeResponse(
                    order=parsed["order"],
                    justification=parsed["justification"],
                    confidence=parsed["confidence"]
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Parsed JSON missing expected keys. url={url} "
                        f"error={type(e).__name__}:{str(e)} parsed_keys={list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__} "
                        f"parsed_value={parsed}"
                    )
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Network error while contacting OpenRouter. url={url} "
                f"error_type={type(e).__name__} error={str(e)}"
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Unexpected error in analyze_markov_order. error_type={type(e).__name__} error={str(e)}"
            )
        )

@app.get("/")
async def root():
    return {"message": "Markov Order Analyzer API", "endpoint": "/api/analyze"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)