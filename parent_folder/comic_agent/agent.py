import os
import warnings
import click
from functools import wraps
# Optional warning suppression for noisy dependencies.
if os.getenv("COMIC_SUPPRESS_WARNINGS", "false").lower() == "true":
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

WELCOME_MESSAGE = "\n".join([
    "=" * 50,
    "4コマ漫画制作エージェントへようこそ！",
    "=" * 50,
    "入力例: 「猫が弁護士になる話」「宇宙旅行での失敗談」",
    "どのような4コマ漫画を作りたいか、日本語で入力してください。",
    "-" * 50,
])

def _patch_cli_preamble() -> None:
    try:
        from google.adk.cli import cli as adk_cli
    except Exception:
        return

    if getattr(adk_cli, "_comic_agent_patched", False):
        return

    original = adk_cli.run_interactively

    @wraps(original)
    async def run_interactively_with_preamble(*args, **kwargs):
        click.echo(WELCOME_MESSAGE)
        return await original(*args, **kwargs)

    adk_cli.run_interactively = run_interactively_with_preamble
    adk_cli._comic_agent_patched = True

_patch_cli_preamble()

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
        "2. 次に、どのような漫画にしたいか案内してください。入力例は**質問の直前**に日本語で提示します。\n"
        "   - **テーマ** (例: 猫のいたずら、宇宙旅行、日常の失敗)\n"
        "   - **登場人物** (例: 猫と飼い主、ロボット、女子高生)\n"
        "   - **雰囲気/トーン** (例: コメディ、シリアス、ほのぼの)\n"
        "   - **意外な展開/オチ** (任意)\n"
        "   - **外見/服装の特徴** (任意・登場人物に含めてもOK)\n\n"
        "ユーザーの入力が短くても、足りない情報は補完して進めてください。追加の聞き返しは最小限にします。\n\n"
        "**作成フロー:**\n"
        "ユーザーから情報を受け取ったら、以下の手順を実行してください:\n"
        "1.  `develop_story` を呼び出し、ストーリーを構成します。\n"
        "2.  **検証とリトライ:** 生成されたストーリーが以下の条件を満たしているか確認してください：\n"
        "    - パネル（panels）が**正確に4件**あるか。\n"
        "    - すべてのテキスト（シナリオ、台詞等）が**完全な日本語**であり、英語が混入していないか。\n"
        "    - 条件を満たさない場合、またはエラーが発生した場合は、失敗した理由をユーザーに短く報告し、**最大2回まで** `develop_story` を再実行して修正を試みてください。\n"
        "3.  ストーリーが確定したら、`generate_panels` を呼び出し画像を生成します。その際、**1枚の画像の中に4コマ**が収まるようにし、2x2のグリッドで順番（1→2→3→4）がわかる構成にしてください。余計なコマや挿入コマは作らないでください。\n"
        "4.  `narrate_comic` を呼び出し、音声を追加します。\n"
        "5.  `publish_comic` を呼び出し、HTMLビューアを生成します。\n\n"
        "最後に、生成された `index.html` のフルパスを表示し、どのように確認できるかをユーザーに**日本語で**丁寧に報告してください。"
    ),
    tools=[develop_story, generate_panels, narrate_comic, publish_comic],
)
