# ComicCraft — AI Comic Story Creator

ComicCraft is a FastAPI + Jinja2 web application that turns a user's story prompt, character, setting, tone, and art style into a five-panel comic. The documented workflow is:

1. Gemini Flash creates a structured five-panel outline.
2. Gemini Pro expands the outline into narration and dialogue.
3. Stable Diffusion creates an illustration for each panel.
4. The layout builder joins text and images.
5. FPDF exports the result as a downloadable PDF.

The implementation keeps the AI providers behind small service modules so they can be replaced or tested independently.

## Project structure

```text
comiccraft/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── services/
│   │   ├── gemini_flash.py
│   │   ├── gemini_pro.py
│   │   ├── image_generator.py
│   │   ├── layout_builder.py
│   │   └── exporters.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── comic_preview.html
│   │   ├── export_success.html
│   │   └── error.html
│   └── static/
│       ├── css/style.css
│       ├── js/app.js
│       ├── panels/.gitkeep
│       └── exports/.gitkeep
├── tests/
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## VS Code setup — Windows

1. Install Python 3.11 or newer.
2. Open this folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

5. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Copy `.env.example` to `.env`.
7. For the fastest first run, leave `IMAGE_PROVIDER=mock`. Add a `GEMINI_API_KEY` to enable real Gemini text generation.
8. Start the server:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

## Real AI image generation

### Local Diffusers

Set:

```env
IMAGE_PROVIDER=local_diffusers
```

The first image generation downloads the Stable Diffusion model and can require several GB of disk/RAM/VRAM. A CUDA-capable GPU is strongly recommended.

### Hugging Face Inference

Set:

```env
IMAGE_PROVIDER=hf_inference
HF_API_KEY=your_token
HF_IMAGE_MODEL=runwayml/stable-diffusion-v1-5
```

This avoids loading the diffusion model into your local Python process. Provider/model availability can change, so use a currently accessible model if the documented model is unavailable to your account.

## Gemini configuration

The documentation specifies `models/gemini-1.5-flash` for outlines and `models/gemini-1.5-pro` for detailed stories. Those values are the defaults in `.env.example`. If your Google AI Studio account no longer exposes those IDs, replace them with model IDs currently available to your account.

## API

### `POST /generate-comic/json`

```json
{
  "story_prompt": "A brave fox exploring an enchanted forest",
  "character_name": "Finn",
  "setting": "enchanted forest",
  "tone": "dramatic",
  "art_style": "anime"
}
```

Returns a generated layout, panel image URLs, and a PDF download URL.

### `POST /test-image`

```json
{"prompt":"A brave fox in an enchanted forest, comic book panel"}
```

### `GET /health`

Returns service configuration and confirms the application is alive.

## Testing

With the virtual environment active:

```powershell
pytest -q
```

The tests use mock providers, so they do not require API keys or a GPU.

## Notes

- Generated images and PDFs are intentionally stored under `app/static/` for the simple local deployment described in the project documentation.
- The mock image provider creates deterministic placeholder panel art so the entire UI/PDF workflow can be verified without a GPU or image API.
- For production deployment, replace local file storage with object storage and add authentication, rate limiting, persistent jobs, and cleanup policies.
