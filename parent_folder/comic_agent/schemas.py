from typing import List, Optional
from pydantic import BaseModel, Field

class Panel(BaseModel):
    panel_number: int = Field(..., description="The sequence number of the panel (1-4)")
    scenario: str = Field(..., description="Description of the scene and action")
    dialogue: str = Field(..., description="Character dialogue (if any)")
    visual_description: str = Field(..., description="Detailed visual description for the artist")
    image_prompt: str = Field(..., description="Optimized prompt for image generation model")
    image_path: Optional[str] = Field(None, description="Path to the generated image file")
    audio_path: Optional[str] = Field(None, description="Path to the generated audio file")

class ComicStory(BaseModel):
    title: str = Field(..., description="Title of the comic strip")
    characters: List[str] = Field(..., description="List of main characters")
    theme: str = Field(..., description="Theme of the comic")
    panels: List[Panel] = Field(..., description="List of 4 panels making up the story")
    output_dir: str = Field("output", description="Directory to save artifacts")
