from typing import List, Optional
from pydantic import BaseModel, Field

class CharacterDesign(BaseModel):
    name: str = Field(..., description="Character name")
    description: str = Field(..., description="Japanese description of consistent visual design")

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
    panels: List[Panel] = Field(..., min_length=4, max_length=4, description="List of exactly 4 panels making up the story")
    comic_image_path: Optional[str] = Field(None, description="Path to the combined 4-panel comic image file")
    character_designs: List[CharacterDesign] = Field(default_factory=list, description="List of character design constraints")
    output_dir: str = Field("output", description="Directory to save artifacts")
    generation_notes: List[str] = Field(default_factory=list, description="Warnings or notes about generation")
