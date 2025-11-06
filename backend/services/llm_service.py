import os
import json
import re
from typing import Dict, Any
import httpx


class LLMService:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        # Allow running in local/dev mode without an API key. When no key is provided,
        # the service will use the internal mock logic instead of calling the remote API.
        if not self.api_key or self.api_key.startswith('sk-REPLACE'):
            self.api_key = None
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = os.getenv('OPENROUTER_MODEL', "openai/o1-mini")
        
    async def analyze_problem(self, problem_description: str) -> Dict[str, Any]:
        # If we don't have an API key, return a local mock result (fast for dev/test)
        if not self.api_key:
            return self._local_mock(problem_description)

        prompt = self._build_prompt(problem_description)

        try:
            response = await self._call_api(prompt)
            result = self._parse_response(response)
            return result
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")

    def _local_mock(self, problem_description: str) -> Dict[str, Any]:
        lower = problem_description.lower()
        if any(k in lower for k in ["weather", "stock", "time series"]):
            return {"order": 2, "justification": "Mock: short-term time series depend on recent history.", "confidence": 0.85}
        if any(k in lower for k in ["text", "language", "sentence"]):
            return {"order": 3, "justification": "Mock: language benefits from longer context.", "confidence": 0.82}
        if any(k in lower for k in ["game", "chess", "strategy"]):
            return {"order": 4, "justification": "Mock: strategic domains need deeper history.", "confidence": 0.78}
        if any(k in lower for k in ["simple", "binary", "coin"]):
            return {"order": 1, "justification": "Mock: simple memoryless processes.", "confidence": 0.92}
        return {"order": 2, "justification": "Mock: default 2nd-order recommendation.", "confidence": 0.7}
    
    def _build_prompt(self, problem_description: str) -> str:
        return f"""You are an expert in Markov models and statistical modeling. Analyze the following problem description and determine the most appropriate order for a Markov model.

Problem Description:
{problem_description}

Your task:
1. Analyze how much historical context/memory is needed for accurate predictions
2. Consider the complexity and dependencies in the problem
3. Recommend a Markov model order (typically 1-5)
4. Provide clear justification
5. Assign a confidence score (0.0 to 1.0)

Respond ONLY with valid JSON in this exact format:
{{
  "order": <integer between 1 and 5>,
  "justification": "<2-3 sentence explanation of why this order is appropriate>",
  "confidence": <float between 0.0 and 1.0>
}}

Guidelines:
- 1st order: Current state only (memoryless, simple processes)
- 2nd order: Previous 2 states (weather, basic time series)
- 3rd order: Previous 3 states (text generation, moderate complexity)
- 4th+ order: Deeper history (complex games, strategic planning)

Do not include any text outside the JSON object."""

    async def _call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
        return data['choices'][0]['message']['content']
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            json_match = re.search(r'\{[^{}]*"order"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            order_match = re.search(r'"order"\s*:\s*(\d+)', response)
            justification_match = re.search(r'"justification"\s*:\s*"([^"]+)"', response)
            confidence_match = re.search(r'"confidence"\s*:\s*(0?\.\d+|1\.0|1)', response)
            
            if order_match and justification_match and confidence_match:
                return {
                    "order": int(order_match.group(1)),
                    "justification": justification_match.group(1),
                    "confidence": float(confidence_match.group(1))
                }
            
            raise ValueError("Could not parse LLM response into expected format")
        
        except Exception as e:
            raise ValueError(f"Response parsing failed: {str(e)}")