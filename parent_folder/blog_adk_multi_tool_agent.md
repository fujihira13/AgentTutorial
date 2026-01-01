---
title: "Google ADKでマルチツールエージェントを作ってみた"
emoji: "🤖"
type: "tech"
topics: ["adk", "gemini", "python", "agent"]
published: false
---

## はじめに

この記事では、Google ADK (Agent Development Kit) を使用して、天気と時刻を教えてくれるマルチツールエージェントを作成する手順を紹介します。

## Google ADKとは

Google ADK (Agent Development Kit) は、Googleが提供するエージェント開発フレームワークです。Gemini APIを活用して、複数のツール（関数）を持つエージェントを簡単に構築できます。

### 公式ドキュメント
- [ADK公式ドキュメント](https://google.github.io/adk-docs/)
- [Quickstartガイド](https://google.github.io/adk-docs/get-started/quickstart/)

## 前提条件

- Python 3.10以上
- Gemini API キー（[Google AI Studio](https://aistudio.google.com/app/apikey)で取得可能）

## セットアップ手順

### 1. プロジェクトディレクトリの作成

```bash
mkdir parent_folder
cd parent_folder
```

### 2. 仮想環境の作成と有効化

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化（Windows）
.venv\Scripts\activate

# 仮想環境の有効化（Mac/Linux）
source .venv/bin/activate
```

### 3. Google ADKのインストール

```bash
pip install google-adk
```

## プロジェクト構成

以下のようなディレクトリ構成を作成します：

```
parent_folder/
  multi_tool_agent/
    __init__.py
    agent.py
  .env
  .env.example
  .gitignore
  README.md
```

## エージェントの実装

### 1. `multi_tool_agent/__init__.py`

```python
from . import agent
```

### 2. `multi_tool_agent/agent.py`

```python
import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """指定された都市の天気情報を取得します。

    Args:
        city (str): 天気情報を取得する都市名

    Returns:
        dict: ステータスと結果またはエラーメッセージ
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    elif city.lower() in ["tokyo", "東京"]:
        return {
            "status": "success",
            "report": (
                "Tokyo is cloudy with a temperature of 18 degrees Celsius."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }

def get_current_time(city: str) -> dict:
    """指定された都市の現在時刻を返します。

    Args:
        city (str): 現在時刻を取得する都市名

    Returns:
        dict: ステータスと結果またはエラーメッセージ
    """
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    elif city.lower() in ["tokyo", "東京"]:
        tz_identifier = "Asia/Tokyo"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
```

### 3. `.env.example`

```
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

### 4. `.gitignore`

```
.env
.venv
__pycache__
*.db
.adk/
```

## 環境変数の設定

1. `.env.example` をコピーして `.env` を作成：

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

2. `.env` ファイルを開き、`GOOGLE_API_KEY` に取得したGemini APIキーを設定します。

## エージェントの実行

### Web UIで実行

```bash
adk web
```

ブラウザが自動的に開き、チャット形式でエージェントと対話できます。

### ターミナルで実行

```bash
adk run multi_tool_agent
```

## 試してみよう

以下のようなプロンプトを試してみてください：

- "What is the weather in New York?"
- "What is the time in Tokyo?"
- "東京の天気は？"
- "ニューヨークの時間は？"

## ポイント解説

### 1. ツール関数の定義

ADKでは、Pythonの通常の関数をツールとして定義できます。関数のdocstringが自動的にツールの説明として使用されます。

```python
def get_weather(city: str) -> dict:
    """指定された都市の天気情報を取得します。
    
    Args:
        city (str): 天気情報を取得する都市名
    
    Returns:
        dict: ステータスと結果またはエラーメッセージ
    """
    # 実装...
```

### 2. エージェントの作成

`Agent` クラスを使用してエージェントを作成します：

```python
root_agent = Agent(
    name="weather_time_agent",           # エージェントの名前
    model="gemini-2.0-flash",            # 使用するGeminiモデル
    description="...",                    # エージェントの説明
    instruction="...",                    # エージェントへの指示
    tools=[get_weather, get_current_time], # 使用可能なツール関数
)
```

### 3. 多言語対応

`city.lower() in ["tokyo", "東京"]` のように、英語と日本語の両方に対応させることができます。

### 4. ADK CLIの便利さ

ADKは専用のCLIツールを提供しており、`adk web` コマンド一つでWebインターフェースが起動します。開発中のエージェントをすぐに試せるのが便利です。

## カスタマイズのアイデア

このベースを元に、以下のような拡張が可能です：

1. **実際のAPIと連携**
   - OpenWeatherMap APIなどを使って実際の天気情報を取得
   - 世界中の都市に対応

2. **ツールの追加**
   - ニュース取得
   - 為替レート取得
   - カレンダー機能

3. **データベース連携**
   - ユーザーの好みの都市を記憶
   - 過去の問い合わせ履歴を保存

## まとめ

Google ADKを使用することで、簡単にマルチツールエージェントを作成できました。このエージェントは：

- ✅ 複数の都市（New York、Tokyo）の天気情報を提供
- ✅ 複数の都市の現在時刻を提供
- ✅ 英語と日本語の両方に対応
- ✅ Web UIとCLIの両方で実行可能

ADKの強みは、ツール（関数）を定義するだけで、Geminiが自動的に適切なツールを選択して実行してくれる点です。複雑な分岐処理を書く必要がなく、宣言的にエージェントを構築できます。

## 参考資料

### ADK関連
- [Google ADK公式ドキュメント](https://google.github.io/adk-docs/)
- [ADK Quickstart](https://google.github.io/adk-docs/get-started/quickstart/)
- [ADK GitHub](https://github.com/google/adk)

### Gemini API関連
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)

### プロジェクトリポジトリ
- [GitHub - AgentTutorial](https://github.com/fujihira13/AgentTutorial)

---

次回は、より実践的なエージェントとして、実際のAPIと連携したり、複数のエージェントを組み合わせたマルチエージェントシステムを構築してみたいと思います！
