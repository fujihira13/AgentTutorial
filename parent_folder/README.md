# Multi-tool Agent

このプロジェクトは、Google ADKを使用して構築されたマルチツールエージェントです。[クイックスタートガイド](https://google.github.io/adk-docs/get-started/quickstart/)に従って作成されています。

## セットアップ (Setup)

1.  仮想環境を作成します:
    ```bash
    python -m venv .venv
    ```

2.  仮想環境を有効化（アクティベート）します:
    - Windows: `.venv\Scripts\activate`
    - Mac/Linux: `source .venv/bin/activate`

3.  依存ライブラリをインストールします:
    ```bash
    pip install google-adk
    ```

4.  環境変数を設定します:
    - `.env.example` をコピーして `.env` を作成します:
        - Windows: `copy .env.example .env`
        - Mac/Linux: `cp .env.example .env`
    - `.env` ファイルを開き、`GOOGLE_API_KEY` にあなたの Gemini API キーを入力してください。

## エージェントの実行 (Running the Agent)

ADK CLIを使用してエージェントを実行できます。

Web UIを起動する場合:
```bash
adk web
# またはパスを指定する場合
adk web multi_tool_agent
```

ターミナルで実行する場合:
```bash
adk run multi_tool_agent
```

## プロンプト例 (Example Prompts)

- What is the weather in New York? (ニューヨークの天気は？)
- What is the time in New York? (ニューヨークの時間は？)
- What is the weather in Paris? (注: このエージェントはモック実装のため、ニューヨークの情報しか持っていません)

## 4コマ漫画エージェント (Comic Generator Agent)

4コマ漫画を生成するエージェントです。

### セットアップ (Setup for Comic Agent)

追加の依存ライブラリをインストールしてください:
```bash
pip install -r requirements.txt
```

`.env` ファイルに `USE_REAL_IMAGE_GEN` や `USE_REAL_TTS` の設定を追加できます（`.env.example`参照）。

### 実行方法 (Usage)

Web UIで実行:
```bash
adk web comic_agent
```

ターミナルで実行:
```bash
adk run comic_agent
```

### テスト入力例 (Test Prompts)

- "Create a comic about a cat who becomes a lawyer."
- "Theme: Coffee Shop, Characters: Robot and Barista, Tone: Funny"

