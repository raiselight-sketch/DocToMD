import os
import aiohttp
import asyncio
import json
from typing import Optional

class AIPostProcessor:
    """
    AI를 사용하여 변환된 Markdown의 품질을 개선하는 후처리기.
    Ollama(Gemma4) 또는 Gemini API를 지원합니다.
    """

    def __init__(self, provider: str = "ollama", model: str = "gemma4:latest", api_key: Optional[str] = None, base_url: str = "http://localhost:11434"):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    async def process(self, text: str) -> str:
        """텍스트를 AI에 전달하여 정제된 결과를 반환합니다."""
        system_prompt = (
            "당신은 문서 변환 전문가입니다. 입력된 Markdown 텍스트에서 다음 작업을 수행하세요:\n"
            "1. 문맥상 끊긴 줄바꿈을 자연스럽게 연결하세요.\n"
            "2. 오타나 맞춤법 오류를 교정하세요.\n"
            "3. 의미 없는 특수문자나 노이즈를 제거하세요.\n"
            "원본의 의미와 구조(헤더, 리스트 등)는 최대한 유지하며 텍스트의 가독성만 높이세요."
        )
        
        if self.provider == "ollama":
            return await self._call_ollama(system_prompt, text)
        elif self.provider == "gemini":
            return await self._call_gemini(system_prompt, text)
        else:
            return text

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.3}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/chat", json=payload, timeout=600) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content", user_prompt)
                    return user_prompt
        except Exception:
            return user_prompt

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return user_prompt
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\n[TEXT TO PROCESS]\n{user_prompt}"}]
            }],
            "generationConfig": {"temperature": 0.3}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['candidates'][0]['content']['parts'][0]['text']
                    return user_prompt
        except Exception:
            return user_prompt
