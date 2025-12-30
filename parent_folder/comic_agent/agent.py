from google.adk.agents import Agent
from .tools import develop_story, generate_panels, narrate_comic, publish_comic

# Define the agent
comic_agent = Agent(
    name="comic_agent",
    model="gemini-2.0-flash",
    description="An agent that creates multimedia 4-panel comics based on user input.",
    instruction=(
        "You are a creative assistant that builds 4-panel comics. "
        "Follow this strictly sequential process:\n"
        "1.  Call `develop_story` with the user's theme/characters to create the story structure.\n"
        "2.  Call `generate_panels` with the resulting story object to create images.\n"
        "3.  Call `narrate_comic` with the updated story object to add audio.\n"
        "4.  Call `publish_comic` with the final story object to generate the HTML viewer.\n\n"
        "Always report the path to the final `index.html` to the user."
    ),
    tools=[develop_story, generate_panels, narrate_comic, publish_comic],
)
