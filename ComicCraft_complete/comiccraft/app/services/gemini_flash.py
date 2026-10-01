import json
from typing import Any
from app.config import Settings
from app.models import PanelOutline, PromptRequest

class GeminiFlashService:
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

    def generate_outline(self, request: PromptRequest) -> list[PanelOutline]:
        if not self.settings.gemini_api_key:
            return self._fallback_outline(request)
        from google.genai import types
        client = self._client_or_raise()
        prompt = f"""Create exactly 5 panels for a comic.
Story prompt: {request.story_prompt}
Main character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}

Return ONLY valid JSON as an array of 5 objects. Each object must contain:
panel_number (integer 1-5), title, scene_description, image_prompt.
Make the protagonist visually consistent across every image prompt.
"""
        response = client.models.generate_content(
            model=self.settings.gemini_flash_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.8),
        )
        data = self._parse_json(response.text)
        panels = [PanelOutline.model_validate(item) for item in data]
        if len(panels) != self.settings.panel_count:
            raise RuntimeError(f"Gemini returned {len(panels)} panels; expected {self.settings.panel_count}")
        return panels

    @staticmethod
    def _parse_json(text: str) -> Any:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    def _fallback_outline(self, request: PromptRequest) -> list[PanelOutline]:
        stages = [
            ("The Beginning", f"{request.character_name} encounters the central mystery in {request.setting}."),
            ("Into the Unknown", f"{request.character_name} moves deeper into the challenge, following clues from the opening."),
            ("The Turning Point", f"A surprising obstacle forces {request.character_name} to make a difficult choice."),
            ("The Final Challenge", f"{request.character_name} confronts the main conflict in a dramatic scene."),
            ("A New Dawn", f"The conflict resolves and {request.character_name} leaves {request.setting} changed by the adventure."),
        ]
        return [
            PanelOutline(
                panel_number=i,
                title=title,
                scene_description=desc,
                image_prompt=f"{request.art_style} comic panel, {desc} Main character: {request.character_name}. Setting: {request.setting}. Tone: {request.tone}. Consistent character design, cinematic composition, expressive faces, no text, no speech bubbles.",
            ) for i, (title, desc) in enumerate(stages, 1)
        ]

def generate_outline(request: PromptRequest, settings: Settings) -> list[PanelOutline]:
    return GeminiFlashService(settings).generate_outline(request)
