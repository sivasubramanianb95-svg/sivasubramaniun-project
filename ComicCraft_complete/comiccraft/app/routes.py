from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.models import ImageTestRequest, PromptRequest
from app.services.exporters import save_pdf
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout

router = APIRouter()
settings = get_settings()
templates = Jinja2Templates(directory=str(__import__('pathlib').Path(__file__).resolve().parent / "templates"))

def run_pipeline(request_data: PromptRequest):
    outline = generate_outline(request_data, settings)
    stories = generate_story(request_data, outline, settings)
    image_paths = [generate_image(panel.image_prompt, settings, panel.panel_number) for panel in stories]
    layout = build_comic_layout(stories, image_paths)
    pdf_path = save_pdf(layout, settings)
    return outline, stories, layout, pdf_path

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"settings": settings})

@router.post("/generate", response_class=HTMLResponse)
async def generate_form(request: Request, story_prompt: str = Form(...), character_name: str = Form(...), setting: str = Form(...), tone: str = Form(...), art_style: str = Form(...)):
    try:
        data = PromptRequest(story_prompt=story_prompt, character_name=character_name, setting=setting, tone=tone, art_style=art_style)
        outline, stories, layout, pdf_path = run_pipeline(data)
        return templates.TemplateResponse(request=request, name="comic_preview.html", context={"layout": layout, "pdf_path": pdf_path, "request_data": data, "outline": outline, "stories": stories})
    except Exception as exc:
        return templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)}, status_code=500)

@router.post("/generate-comic/json")
async def generate_json(data: PromptRequest):
    try:
        _, _, layout, pdf_path = run_pipeline(data)
        return {"success": True, "layout": [p.model_dump() for p in layout], "pdf_path": pdf_path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf: str | None = None):
    return templates.TemplateResponse(request=request, name="export_success.html", context={"pdf_path": pdf})

@router.post("/test-image")
async def test_image(data: ImageTestRequest):
    try:
        path = generate_image(data.prompt, settings)
        return {"success": True, "image_path": path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/health")
async def health():
    return {"status": "ok", "image_provider": settings.image_provider, "gemini_configured": bool(settings.gemini_api_key)}
