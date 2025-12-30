.PHONY: help setup run

# デフォルトターゲット: 手順を表示
help:
	@echo -------------------------------------------------------------
	@echo  [実行手順]
	@echo.
	@echo  1. セットアップ
	@echo     python -m venv .venv
	@echo     .venv\Scripts\activate
	@echo     pip install -r requirements.txt
	@echo     cp .env.example .env
	@echo.
	@echo  2. ADKでの実行
	@echo     adk run comic_agent
	@echo     # プロンプト例: "Create a comic about a creative AI."
	@echo.
	@echo  3. ビューアの確認
	@echo     ブラウザで output/index.html を開くと、
	@echo     生成された4コマ漫画（画像・音声付き）を確認できます。
	@echo.
	@echo  [その他]
	@echo  - 画像/音声はデフォルトでMock(ダミー)です。
	@echo  - 実APIを使う場合は .env ファイルを編集してください。
	@echo  - 画像が表示されない場合は adk run を再実行してください(パス修正済み)。
	@echo -------------------------------------------------------------
	@echo.
	@echo  [コマンドショートカット]
	@echo  make setup  : セットアップを一括実行します
	@echo  make run    : エージェントを実行します

# セットアップ実行
setup:
	python -m venv .venv
	.venv\Scripts\pip install -r requirements.txt
	@if not exist .env copy .env.example .env
	@echo.
	@echo [Setup Complete]
	@echo 次に '.venv\Scripts\activate' を実行して仮想環境に入ってください。

# エージェント実行
run:
	.venv\Scripts\adk run comic_agent
