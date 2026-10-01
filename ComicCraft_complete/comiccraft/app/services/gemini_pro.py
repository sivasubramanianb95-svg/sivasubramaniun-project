import json
from typing import Any
from app.config import Settings
from app.models import PanelOutline, PanelStory, PromptRequest

class GeminiProService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    def _client_or_raise(self):
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    def generate_story(self, request: PromptRequest, outline: list[PanelOutline]) -> list[PanelStory]:
        if not self.settings.gemini_api_key:
            return self._fallback_story(request, outline)
        from google.genai import types
        client = self._client_or_raise()
        outline_json = json.dumps([p.model_dump() for p in outline], ensure_ascii=False)
        prompt = f"""Expand this comic outline into a polished 5-panel comic story.
Character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}
Outline:
{outline_json}

Return ONLY valid JSON as an array with one object per panel. Preserve panel_number, title, scene_description and image_prompt, and add:
caption: a short ambient/comic caption,
narration: 1-3 sentences,
dialogue: an array of 0-3 short spoken lines.
Keep continuity between panels and make dialogue natural.
"""
        response = client.models.generate_content(
            model=self.settings.gemini_pro_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9),
        )
        data = self._parse_json(response.text)
        return [PanelStory.model_validate(item) for item in data]

    @staticmethod
    def _parse_json(text: str) -> Any:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    def _fallback_story(self, request: PromptRequest, outline: list[PanelOutline]) -> list[PanelStory]:
        return [
            PanelStory(
                **panel.model_dump(),
                caption=f"{panel.title.upper()} — {request.tone.title()} mood",
                narration=panel.scene_description,
                dialogue=[f"{request.character_name}: We have to keep moving."] if i < len(outline) else [f"{request.character_name}: We did it."]
            ) for i, panel in enumerate(outline, 1)
        ]

def generate_story(request: PromptRequest, outline: list[PanelOutline], settings: Settings) -> list[PanelStory]:
    return GeminiProService(settings).generate_story(request, outline)
