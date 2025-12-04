import requests
from llama_index.core.llms.llm import LLM  # LLM 인터페이스 임포트

class OllamaLLM(LLM):
    def __init__(self, model_name="gemma2", api_url="http://localhost:11434/v1"):
        self.model_name = model_name
        self.api_url = api_url

    def query(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,  # "input" → "prompt" 수정
            "stream": False     # stream 옵션 추가
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(f"{self.api_url}/completions", json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()["choices"][0]["text"]  # 응답 구조 확인
        else:
            return f"Error: {response.status_code} - {response.text}"

