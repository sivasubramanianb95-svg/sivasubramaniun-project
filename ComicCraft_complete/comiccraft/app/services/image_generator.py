import hashlib
import io
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import httpx
from app.config import Settings

class ImageGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._pipe = None

    def generate_image(self, prompt: str, panel_number: int | None = None) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", prompt)[:55].strip("_") or "panel"
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:10]
        filename = f"panel_{panel_number or 0}_{safe}_{digest}.png"
        target = self.settings.panels_dir / filename
        provider = self.settings.image_provider.lower()
        if provider == "mock":
            self._mock_image(prompt, target, panel_number)
        elif provider == "local_diffusers":
            self._diffusers_image(prompt, target)
        elif provider == "hf_inference":
            self._hf_image(prompt, target)
        else:
            raise RuntimeError(f"Unknown IMAGE_PROVIDER: {self.settings.image_provider}")
        return f"/static/panels/{filename}"

    def _mock_image(self, prompt: str, target: Path, panel_number: int | None):
        img = Image.new("RGB", (self.settings.image_width, self.settings.image_height), "#f3e8d0")
        draw = ImageDraw.Draw(img)
        margin = 32
        draw.rectangle((margin, margin, img.width-margin, img.height-margin), outline="#222", width=8)
        draw.ellipse((img.width//2-100, 180, img.width//2+100, 380), outline="#222", width=8)
        draw.arc((img.width//2-55, 245, img.width//2+55, 330), 20, 160, fill="#222", width=5)
        draw.ellipse((img.width//2-50, 245, img.width//2-25, 270), fill="#222")
        draw.ellipse((img.width//2+25, 245, img.width//2+50, 270), fill="#222")
        title = f"COMICCRAFT • PANEL {panel_number or '?'}"
        draw.text((55, 70), title, fill="#111")
        wrapped = self._wrap(prompt, 52)
        y = 440
        for line in wrapped[:8]:
            draw.text((60, y), line, fill="#333")
            y += 35
        draw.text((60, img.height-90), "Mock image — switch IMAGE_PROVIDER for AI art", fill="#555")
        img.save(target, format="PNG")

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words, lines, line = text.split(), [], ""
        for word in words:
            if len(line) + len(word) + 1 > width:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        return lines

    def _diffusers_image(self, prompt: str, target: Path):
        import torch
        from diffusers import StableDiffusionPipeline
        if self._pipe is None:
            model_id = self.settings.hf_image_model
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            self._pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
            self._pipe = self._pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        image = self._pipe(prompt, num_inference_steps=self.settings.image_steps, width=self.settings.image_width, height=self.settings.image_height).images[0]
        image.save(target)

    def _hf_image(self, prompt: str, target: Path):
        if not self.settings.hf_api_key:
            raise RuntimeError("HF_API_KEY is required when IMAGE_PROVIDER=hf_inference")
        url = f"https://api-inference.huggingface.co/models/{self.settings.hf_image_model}"
        headers = {"Authorization": f"Bearer {self.settings.hf_api_key}"}
        with httpx.Client(timeout=180.0) as client:
            response = client.post(url, headers=headers, json={"inputs": prompt})
        if response.status_code != 200:
            detail = response.text[:500]
            raise RuntimeError(f"Hugging Face image generation failed ({response.status_code}): {detail}")
        Image.open(io.BytesIO(response.content)).convert("RGB").save(target)

def generate_image(prompt: str, settings: Settings, panel_number: int | None = None) -> str:
    return ImageGenerator(settings).generate_image(prompt, panel_number)
