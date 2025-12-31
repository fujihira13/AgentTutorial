import os
import warnings
# Optional warning suppression for noisy dependencies.
if os.getenv("COMIC_SUPPRESS_WARNINGS", "false").lower() == "true":
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

print("\n" + "="*50)
print(" 🎨 4コマ漫画制作エージェントへようこそ！")
print("="*50)
print("どのような4コマ漫画を作りたいか、日本語で入力してください。")
print("例：「猫が弁護士になる話」「宇宙旅行での失敗談」など")
print("-" * 50 + "\n")

from google.adk.agents import Agent
from .tools import develop_story, generate_panels, narrate_comic, publish_comic

# Define the agent
root_agent = Agent(
    name="comic_generator_agent",
    model="gemini-2.0-flash",
    description="テーマや登場人物を入力すると、自動でストーリー・画像・音声・HTMLを生成する4コマ漫画制作アシスタントです。",
    instruction=(
        "あなたはプロの4コマ漫画家アシスタントです。ユーザーがエージェントを起動した際（または挨拶された際）に、必ず「どのような4コマ漫画を作りたいか（テーマ、登場人物、トーンなど）」を尋ね、具体的な入力例を日本語で提示してください。\n"
        "対話はすべて**日本語**で行ってください。\n\n"
        "**開始時のフロー:**\n"
        "1. 起動したら、まずユーザーに挨拶し、これから4コマ漫画を作成することを伝えてください。\n"
        "2. 次に、どのような漫画にしたいか、以下の情報を入力してもらうよう親切に案内してください：\n"
        "   - **テーマ** (例: 猫のいたずら、宇宙旅行、日常の失敗)\n"
        "   - **登場人物** (例: 猫と飼い主、ロボット、女子高生)\n"
        "   - **雰囲気/トーン** (例: コメディ、シリアス、ほのぼの)\n"
        "   - **意外な展開/オチ** (もしあれば)\n\n"
        "**作成フロー:**\n"
        "ユーザーから情報を受け取ったら、以下の手順を実行してください:\n"
        "1.  `develop_story` を呼び出し、ストーリーを構成します。\n"
        "2.  **検証とリトライ:** 生成されたストーリーが以下の条件を満たしているか確認してください：\n"
        "    - パネル（panels）が**正確に4件**あるか。\n"
        "    - すべてのテキスト（シナリオ、台詞等）が**完全な日本語**であり、英語が混入していないか。\n"
        "    - 条件を満たさない場合、またはエラーが発生した場合は、失敗した理由をユーザーに短く報告し、**最大2回まで** `develop_story` を再実行して修正を試みてください。\n"
        "3.  ストーリーが確定したら、`generate_panels` を呼び出し画像を生成します。その際、必ず**各画像が1枚の単一パネル（single panel）**であることを確認し、グリッドやコラージュにならないよう徹底してください。\n"
        "4.  `narrate_comic` を呼び出し、音声を追加します。\n"
        "5.  `publish_comic` を呼び出し、HTMLビューアを生成します。\n\n"
        "最後に、生成された `index.html` のフルパスを表示し、どのように確認できるかをユーザーに**日本語で**丁寧に報告してください。"
    ),
    tools=[develop_story, generate_panels, narrate_comic, publish_comic],
)
