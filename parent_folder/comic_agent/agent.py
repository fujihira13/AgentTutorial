from google.adk.agents import Agent
from .tools import develop_story, generate_panels, narrate_comic, publish_comic

# Define the agent
root_agent = Agent(
    name="comic_agent",
    model="gemini-2.0-flash",
    description="An agent that creates multimedia 4-panel comics based on user input.",
    instruction=(
        "あなたは4コマ漫画を作成するクリエイティブなアシスタントです。\n"
        "ユーザーとの対話はすべて**日本語**で行ってください。\n\n"
        "以下の手順を順番に実行してください:\n"
        "1.  `develop_story` を呼び出し、ユーザーのテーマやキャラクターに基づいてストーリー構成を作成します。\n"
        "2.  その結果の story オブジェクトを使って `generate_panels` を呼び出し、画像を作成します。\n"
        "3.  更新された story オブジェクトを使って `narrate_comic` を呼び出し、音声を追加します。\n"
        "4.  最終的な story オブジェクトを使って `publish_comic` を呼び出し、HTMLビューアを生成します。\n\n"
        "最後に、生成された `index.html` へのパスをユーザーに**日本語で**報告してください。"
    ),
    tools=[develop_story, generate_panels, narrate_comic, publish_comic],
)
