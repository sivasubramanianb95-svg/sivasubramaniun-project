from app.models import ComicLayout, PanelStory

def build_comic_layout(stories: list[PanelStory], image_paths: list[str]) -> list[ComicLayout]:
    if len(stories) != len(image_paths):
        raise ValueError("Every story panel must have exactly one image")
    return [ComicLayout(panel_number=p.panel_number, title=p.title, image_path=image_paths[i], scene_description=p.scene_description, caption=p.caption, narration=p.narration, dialogue=p.dialogue, image_prompt=p.image_prompt) for i, p in enumerate(stories)]
