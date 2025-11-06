import os
import json
import re
from typing import Dict, Any
import httpx


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528-qwen3-8b:free")
        self.use_mock = not self.api_key or self.api_key.startswith("sk-REPLACE")
        
    async def analyze_problem(self, problem_description: str) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock_analysis(problem_description)
        
        try:
            prompt = self._build_prompt(problem_description)
            response_text = await self._call_openrouter(prompt)
            return self._parse_json(response_text)
        except Exception as e:
            return self._mock_analysis(problem_description)
    
    def _build_prompt(self, problem: str) -> str:
        return f"""Analyze this problem and recommend a Markov model order (1-5).

Problem: {problem}

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "order": <1-5>,
  "justification": "<2-3 sentences explaining why>",
  "confidence": <0.0-1.0>
}}

Guidelines:
- Order 1: Memoryless (coin flips, simple random)
- Order 2: Short memory (weather, stock prices)
- Order 3: Medium memory (text generation, dialogue)
- Order 4-5: Long memory (chess, complex strategy)"""
    
    async def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://order-of-markov.vercel.app",
                    "X-Title": "Order of Markov"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        match = re.search(r'\{[^{}]*"order"[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        order = re.search(r'"order"\s*:\s*(\d+)', text)
        justification = re.search(r'"justification"\s*:\s*"([^"]*)"', text)
        confidence = re.search(r'"confidence"\s*:\s*(0?\.\d+|1\.0)', text)
        
        if order and justification and confidence:
            return {
                "order": int(order.group(1)),
                "justification": justification.group(1),
                "confidence": float(confidence.group(1))
            }
        
        return {
            "order": 2,
            "justification": "Unable to parse LLM response, using default recommendation.",
            "confidence": 0.5
        }
    
    def _mock_analysis(self, problem: str) -> Dict[str, Any]:
        lower = problem.lower()
        
        patterns = [
            (["weather", "stock", "price", "forecast"], 2, "Time series patterns suggest 2nd-order dependencies.", 0.85),
            (["text", "language", "sentence", "word"], 3, "Natural language requires 3rd-order context for coherent generation.", 0.82),
            (["game", "chess", "strategy", "move"], 4, "Strategic decision-making benefits from deeper historical context.", 0.78),
            (["random", "coin", "dice", "binary"], 1, "Simple memoryless process needs only current state.", 0.92),
        ]
        
        for keywords, order, justification, confidence in patterns:
            if any(k in lower for k in keywords):
                return {"order": order, "justification": justification, "confidence": confidence}
        
        return {
            "order": 2,
            "justification": "Second-order model balances complexity and performance for most applications.",
            "confidence": 0.7
        }