# scruf/llm_client.py
import os
import json
import re
from openai import AzureOpenAI



class LLMClient:
    """Backend-agnostic LLM client. Currently wraps Azure OpenAI."""

    def __init__(self, model=None, **kwargs):
        self.client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        self.deployment = model 

    def generate(self, prompt: str, system: str = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            response_format={"type": "json_object"},  # enforce JSON output
            temperature=0.0,
        )
        return response.choices[0].message.content

    @staticmethod
    def extract_json(text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Could not parse JSON from LLM response: {text}")