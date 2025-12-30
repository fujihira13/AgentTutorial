import sys
from comic_agent.tools import develop_story, generate_panels, narrate_comic, publish_comic

def main():
    print("Testing Comic Agent Pipeline (Mock Mode)...")
    
    # 1. Develop Story
    print("1. Developing story...")
    story = develop_story(
        theme="Testing Pipeline", 
        characters="Tester, Bug", 
        tone="Witty", 
        twist="It works"
    )
    print(f"   Story created: {story.title}")
    
    # 2. Generate Panels (Mock Images)
    print("2. Generating panels...")
    story = generate_panels(story)
    print(f"   Images generated at: {story.output_dir}")
    
    # 3. Narrate (Mock TTS)
    print("3. Narrating...")
    story = narrate_comic(story)
    print(f"   Audio generated.")
    
    # 4. Publish
    print("4. Publishing...")
    html_path = publish_comic(story)
    print(f"   Published to: {html_path}")
    
    print("\nVerification Successful! Open output/index.html to view.")

if __name__ == "__main__":
    main()
