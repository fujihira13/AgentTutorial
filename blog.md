---
title: "ADKを使って4コマ漫画を自動生成するAIエージェントを作ってみた"
emoji: "🎨"
type: "tech"
topics: ["adk", "gemini", "python", "agent", "AI"]
published: false
---

# 概要

GoogleのAIエージェントフレームワーク「ADK（Agent Development Kit）」を使って、**テーマを与えるだけで4コマ漫画を自動生成してくれるAIエージェント**を作ってみました。

このエージェントは、ストーリー生成から画像作成、音声合成、HTMLビューア生成まで、すべて自動で行います。
ADKの学習も兼ねて、シンプルながら実用的なツールを目指しました。

実際に作成したコードはこちらに置いています：
https://github.com/[your-repository]/comic-agent

---

## 実際に生成された4コマ漫画

エージェントに「猫のいたずら」というテーマを与えた結果、以下のような4コマ漫画が生成されました：

- **起**：猫が何かを狙っている様子
- **承**：飼い主の大切な花瓶に近づく
- **転**：花瓶を倒してしまう
- **結**：知らんぷりして寝ているオチ

音声も自動生成されるので、セリフ付きで楽しめます！
実際の出力例は `output/` フォルダに保存されています。

---

## ADKについて

ADK（Agent Development Kit）はGoogleが開発しているAIエージェントフレームワークです。
他のフレームワーク（LangChainなど）と比較して、以下の特徴があります：

### ADKの嬉しいポイント

1. **試すUIが標準装備**
   - `adk web` コマンドで、すぐにチャット形式のUIが起動
   - 各ツールの実行状況や引数、生成物を簡単に確認できる
   - デバッグがとてもやりやすい

2. **シンプルな記述**
   - ツールの連携がわかりやすく書ける
   - LangChainよりもコード量が少なくて済む

3. **Googleエコシステムとの相性**
   - Gemini、Imagen、TTSなどのGoogle AIサービスとシームレスに連携

今後、TypeScript製のMastraなど、AIエージェント開発ツールの選択肢がさらに増えていくと嬉しいですね。

---

## システムの全体構成

今回作成したエージェントは、以下の4つのツールを順番に実行します：

```text
ユーザー入力（テーマ）
  ↓
① develop_story
   （Geminiで4コマのストーリーをJSON形式で生成）
  ↓
② generate_panels
   （Geminiで4コマ漫画の画像を1枚に生成）
  ↓
③ narrate_comic
   （各コマのセリフを音声合成）
  ↓
④ publish_comic
   （HTMLビューアを生成）
  ↓
output/index.html を開いて完成！
```

### ファイル構成

```
comic_agent/
├── __init__.py
├── agent.py          # ADKのAgent定義
├── tools.py          # 4つのツール実装
├── schemas.py        # データ構造の定義（Pydantic）
└── templates/
    └── viewer.html   # HTMLビューアのテンプレート
```

---

## AIエージェントへの指示（プロンプト）

エージェントには、以下のような指示を与えています：

```
あなたは優秀な4コマ漫画制作者です。
ユーザから与えられるテーマに合わせて、次の手順に沿って4コマ漫画を作成してください。

1. テーマに沿った4コマ漫画のストーリーを考える
   - 起承転結の構成で作成
   - 最後のコマで意外なオチをつける
   
2. ストーリーの各コマの詳細を決める
   - 各コマの説明文
   - セリフ（あれば）
   - キャラクターの動作や表情

3. 画像を生成する
   - 4コマ漫画を1枚の画像として生成
   - 2x2のグリッドレイアウト

4. セリフを音声合成する
   - 各コマのセリフを音声ファイル化

5. HTMLビューアを生成する
   - 画像と音声を組み合わせて表示
```

### ストーリー生成のフォーマット

ツールに渡すJSONフォーマットは以下のようになっています：

```json
{
  "title": "漫画のタイトル",
  "theme": "ユーザーが指定したテーマ",
  "character_design": {
    "name": "主人公の名前",
    "appearance": "外見の説明",
    "personality": "性格の説明"
  },
  "panels": [
    {
      "order": 1,
      "role": "起",
      "scene_description": "シーンの説明",
      "dialogue": "セリフ（あれば）",
      "action": "キャラクターの動作"
    },
    // ... 4コマ分
  ]
}
```

---

## 作成したツール詳細

### ① develop_story - ストーリー生成

**役割**: Geminiを使って4コマ漫画のストーリーをJSON形式で生成

**工夫したポイント**:
- 4コマの数がズレないように厳密にチェック
- 日本語のみで生成するように指示（英語が混ざると雰囲気が壊れる）
- 失敗時は最大3回までリトライ
- それでも失敗した場合はテンプレートでフォールバック

```python
# 主要な検証ロジック
def validate_story(story):
    """生成されたストーリーが4コマかどうかチェック"""
    if len(story["panels"]) != 4:
        return False
    
    # 各パネルが必要な情報を持っているかチェック
    for panel in story["panels"]:
        if not panel.get("scene_description"):
            return False
    
    return True
```

### ② generate_panels - 画像生成

**役割**: Gemini Imagenで4コマ漫画を1枚の画像として生成

**工夫したポイント**:
- **1枚の画像に4コマすべて**を描画（UIがシンプルになる）
- 2x2のグリッドレイアウトを指定
- 画像生成失敗時はPillowで簡易モック画像を生成
- コマの読み順（右上→左上→右下→左下）を配列で調整

```python
# 画像生成プロンプトの例
prompt = f"""
4-panel manga layout in 2x2 grid.
Theme: {theme}

Panel 1 (top-left): {panel1_description}
Panel 2 (top-right): {panel2_description}
Panel 3 (bottom-left): {panel3_description}
Panel 4 (bottom-right): {panel4_description}

Style: Simple manga art, black and white, clear panel borders.
"""
```

### ③ narrate_comic - 音声合成

**役割**: 各コマのセリフをGemini TTSで音声ファイル化

**工夫したポイント**:
- セリフが空のコマはスキップ
- Gemini TTSのRAW PCM形式に**WAVヘッダーを追加**して保存
- 失敗時は無音のモックファイルを生成

```python
def add_wav_header(pcm_data, sample_rate=24000, channels=1):
    """RAW PCMデータにWAVヘッダーを追加"""
    import wave
    import io
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    
    return wav_buffer.getvalue()
```

### ④ publish_comic - HTMLビューア生成

**役割**: Jinja2を使って、画像と音声を表示するHTMLファイルを生成

**工夫したポイント**:
- 生成した画像と音声ファイルを埋め込み
- シンプルで見やすいレイアウト
- 各コマの音声を再生できるボタン付き

---

## セットアップ方法（初心者向け）

### 1. 必要なものを準備

```bash
# 仮想環境を作成（プロジェクト専用の環境）
python -m venv .venv

# 仮想環境を有効化
.venv\Scripts\activate  # Windowsの場合
# source .venv/bin/activate  # macOS/Linuxの場合

# 必要なパッケージをインストール
pip install -r requirements.txt
```

**用語解説**:
- **仮想環境**: プロジェクトごとに独立したPython環境を作る仕組み。他のプロジェクトと干渉しません。
- **requirements.txt**: 必要なパッケージの一覧が書かれたファイル

### 2. 環境変数の設定

`.env` ファイルを作成して、Google APIキーを設定します：

```ini
# Google APIキー（必須）
GOOGLE_API_KEY=your_google_api_key_here

# 本物のAIを使うかどうか（開発中はfalseでOK）
USE_REAL_STORY_GEN=true
USE_REAL_IMAGE_GEN=false  # 画像生成は無料枠が少ないので注意
USE_REAL_TTS=false        # 音声合成も無料枠が少ないので注意
```

**初心者向けアドバイス**:
- Google APIキーは[Google AI Studio](https://makersuite.google.com/app/apikey)で無料で取得できます
- 開発中は `USE_REAL_*` を `false` にしておくと、モックデータで動作確認できます
- 本番で試すときだけ `true` に変更しましょう

---

## 実行方法

### Webインターフェースで実行（おすすめ）

```bash
adk web comic_agent
```

実行すると、ブラウザが開いてチャット形式のUIが表示されます。
「猫のいたずら」などのテーマを入力すると、エージェントが自動で4コマ漫画を生成します。

**良いところ**:
- 生成途中の状態が見える
- 各ツールの実行結果を確認できる
- デバッグしやすい

### コマンドラインで実行

```bash
adk run comic_agent
```

対話形式でテーマを入力できます。

---

## 生成される成果物

実行が完了すると、`output/` フォルダに以下のファイルが生成されます：

```
output/
├── comic.json          # 生成されたストーリーのJSON
├── comic.png           # 4コマ漫画の画像
├── panel_1.wav         # 1コマ目の音声
├── panel_2.wav         # 2コマ目の音声
├── panel_3.wav         # 3コマ目の音声
├── panel_4.wav         # 4コマ目の音声
└── index.html          # ビューア（ブラウザで開く）
```

`index.html` をブラウザで開くと、画像と音声を一緒に楽しめます！

---

## 作ってみて学んだこと

### ADKの良かった点

1. **デバッグが楽**
   - WebUIで各ツールの実行状況が見える
   - エラーが出てもどこで失敗したかすぐわかる

2. **コードがシンプル**
   - LangChainと比べて、ツールの定義や連携がシンプルに書ける
   - 学習コストが低い

3. **Googleとの相性**
   - Gemini、Imagen、TTSなどがすぐ使える
   - APIキー1つで全部動く

### 苦労した点・工夫した点

1. **4コマの数が絶対にズレない仕組み**
   - LLMは時々指示を守らないので、厳密なバリデーションが必要
   - リトライロジックを入れて安定性を向上

2. **日本語の品質**
   - 英語が混ざるとユーザー体験が悪くなる
   - プロンプトに「必ず日本語で」と何度も念押し

3. **画像レイアウト**
   - 最初は4枚別々に生成していたが、1枚にまとめた方がUI的にシンプル
   - ただし、グリッドのレイアウト崩れは今後の改善点

4. **音声ファイル形式**
   - Gemini TTSはRAW PCMで返すので、WAVヘッダーの追加が必要
   - 最初は音が出なくて焦った...

---

## 今後の改善予定

- **画像品質の向上**: 4コマのレイアウトをもっと安定させたい
- **吹き出しの自動配置**: セリフを画像上に直接描画
- **キャラクター一貫性**: 各コマでキャラクターデザインを統一
- **アニメーション**: 簡単な動きを付けられたら面白そう

---

## まとめ

ADKを使って4コマ漫画生成エージェントを作ってみました。
ワークフロー的な処理でしたが、**エージェント形式で実装することでコードがシンプルになり、試行錯誤もしやすかった**です。

GoogleのAIサービス（Gemini、Imagen、TTS）はどれも品質が高く、インフラも含めて**AI開発がとてもやりやすい環境**だと感じました。

LangChainよりもツールの連携がシンプルなので、これからのAIエージェント開発にはADKを積極的に使っていきたいと思います。

**初心者の方へ**:
このプロジェクトは、ADKの学習に最適な題材だと思います。
ぜひコードを読んで、自分なりにカスタマイズしてみてください！

---

## 参考情報

- [ADK公式ドキュメント](https://github.com/google/agent-development-kit)
- [Gemini API](https://ai.google.dev/)
- [マルチモーダル処理の参考記事](https://zenn.dev/soundtricker/articles/fba90dc901ab46)
- [ADK実践例](https://zenn.dev/google_cloud_jp/articles/97002c462e9025)

---

**何か質問や改善点があれば、お気軽にコメントください！** 🎨✨

