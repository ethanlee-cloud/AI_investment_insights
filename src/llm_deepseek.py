import json
import os
from typing import Dict, Any, List
import requests


def _load_prompt(rel_path: str) -> str:
    with open(rel_path, "r", encoding="utf-8") as f:
        return f.read()


class DeepSeekClient:
    """
    Minimal DeepSeek chat client wrapper.

    NOTE:
    DeepSeek API shapes can differ by plan/version.
    If your response format differs, adjust _call_chat().
    """
    def __init__(self, api_key: str, base_url: str, model: str, timeout_sec: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec

        self.prompt_summarize = _load_prompt("prompts/summarize.txt")
        self.prompt_themes = _load_prompt("prompts/themes_and_etfs.txt")
        self.prompt_priced = _load_prompt("prompts/priced_in_analysis.txt")

    def _call_chat(self, system: str, user: str) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }

        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_sec)
        r.raise_for_status()
        data = r.json()
        # Typical OpenAI-like shape:
        return data["choices"][0]["message"]["content"]

    def _json_or_raise(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            # Sometimes models wrap JSON in ```json
            cleaned = text.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)

    def summarize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        user = json.dumps({
            "title": article.get("title"),
            "url": article.get("url"),
            "published": article.get("published"),
            "text": article.get("text", "")[:25000]  # protect token usage
        }, ensure_ascii=False)

        out = self._call_chat(system=self.prompt_summarize, user=user)
        data = self._json_or_raise(out)

        # Enforce keys
        data.setdefault("summary_bullets", [])
        data.setdefault("evidence_snippets", [])
        data.setdefault("sentiment_score", 0.0)
        return data

    def cluster_themes(self, articles: List[Dict[str, Any]], etf_map: Dict[str, Any]) -> Dict[str, Any]:
        user_payload = {
            "etf_map": etf_map,
            "articles": [
                {
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "published": a.get("published"),
                    "summary_bullets": (a.get("summary") or {}).get("summary_bullets", []),
                }
                for a in articles
            ]
        }
        out = self._call_chat(system=self.prompt_themes, user=json.dumps(user_payload, ensure_ascii=False))
        return self._json_or_raise(out)

    def priced_in_analysis(self, theme_block: Dict[str, Any]) -> Dict[str, Any]:
        out = self._call_chat(system=self.prompt_priced, user=json.dumps(theme_block, ensure_ascii=False))
        return self._json_or_raise(out)
