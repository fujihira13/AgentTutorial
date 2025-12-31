# 4コマ漫画エージェント

このプロジェクトは、Google ADKを使用して構築された4コマ漫画生成エージェントです。

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
    pip install -r requirements.txt
    ```

4.  環境変数を設定します:
    - `.env.example` をコピーして `.env` を作成します:
        - Windows: `copy .env.example .env`
        - Mac/Linux: `cp .env.example .env`
    - `.env` ファイルを開き、`GOOGLE_API_KEY` にあなたの Gemini API キーを入力してください。

## 4コマ漫画エージェント (Comic Generator Agent)

4コマ漫画を生成するエージェントです。

### 設定 (Settings)

`.env` ファイルに `USE_REAL_IMAGE_GEN` や `USE_REAL_TTS` の設定を追加・変更してください（`.env.example`参照）。

**使用モデル:**
- **画像生成**: `models/nano-banana-pro-preview` (Gemini 3 Pro Image)
- **音声読み上げ**: `gemini-2.5-pro-preview-tts` (Gemini 2.5 Pro)

**設定例 (.env):**
```ini
# 画像生成AIを使用する場合
USE_REAL_IMAGE_GEN=true

# 音声読み上げを使用する場合（Gemini 2.5 Pro Preview）
USE_REAL_TTS=true
```

### 実行方法 (Usage)

Web UIで実行:
```bash
adk web comic_agent
```

ターミナルで実行:
```bash
adk run comic_agent
```

### 4コマ漫画の入力例 (Example Inputs)

エージェントを起動すると、どのような漫画にしたいか詳しく聞かれます。例えば以下のように入力してください：

- 「猫がいきなり弁護士になる話を作って」
- 「テーマ：コーヒーショップ、登場人物：ロボットと店員、雰囲気：コメディ」
- 「宇宙旅行でトラブルが起きるけど、最後はほっこりする話」


### 生成物について (Outputs)

漫画生成が完了すると、`output/` フォルダに以下のファイルが出力されます。

- `index.html`: ブラウザで閲覧するためのビューア
- `comic.json`: 生成されたストーリーデータ
- `comic.png`: 4コマを1枚にまとめた画像
- `panel_*.wav`: 各コマの音声

**注意**: これらのファイルは、エージェントを実行するたびに**新しい内容で上書きされます**。以前の生成結果を残しておきたい場合は、実行前に `output/` フォルダの名前を変更するか、別の場所にコピーしてください。
