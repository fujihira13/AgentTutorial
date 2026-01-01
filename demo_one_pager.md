# 4コマ漫画エージェント（ADK + Gemini）
生成フローを一気通貫で実行し、ストーリー→画像→音声→HTMLを自動出力

## 目的
- ADKのエージェント設計とツール連携を実践
- 4コマ生成の一連フローを短時間で再現

## デモ（1分の見せ方）
- 起動: `adk web comic_agent`
- 入力: 「テーマ/登場人物/雰囲気」を指定
- 出力: `output/` の `comic.json` / `comic.png` / `index.html`
- 仕上げ: HTMLビューアで閲覧と音声再生

## パイプライン
ユーザー入力 → develop_story → generate_panels → narrate_comic → publish_comic

## 主な工夫
- 4コマJSONの長さ検証とリトライで安定化
- 日本語チェックを厳格化し英語混入を抑制
- 画像は2x2の1枚に統合してUIを単純化
- 失敗時はテンプレ/モックにフォールバック

## 技術スタック
Python / Google ADK / Gemini (story, image, TTS) / Pydantic / Jinja2 / Pillow

## 出力物
- `comic.json`（4コマ構成）
- `comic.png`（2x2の1枚画像）
- `panel_*.wav`（セリフ音声）
- `index.html`（ビューア）

## 制約と次の改善
- 吹き出し配置など演出は未対応
- レイアウト固定と品質評価の自動化を追加予定
