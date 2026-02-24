# ai_classifier.py
# Re:find 用の「テキスト・画像分類」共通関数
# ※ GPT-5 mini は新しい Responses API を使うため、chat.completions ではなく responses を使用

import os
import re
import base64
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# ローカル開発時は .env を読み込む
load_dotenv()

# ===================================================
# Azure OpenAI の接続情報（環境変数から取得）
#   AZURE_OPENAI_API_KEY  : AzureポータルでコピーしたAPIキー
#   AZURE_OPENAI_ENDPOINT : https://refind-openai.openai.azure.com/ のようなURL
# ===================================================
AZURE_API_KEY      = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT     = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION  = "2025-03-01-preview"  # GPT-5 mini に必要なバージョン
AZURE_DEPLOY_NAME  = "gpt-5-mini"          # Foundryでデプロイした名前

# Azure OpenAI クライアントを初期化
client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
)


# === 分類用プロンプト（テキスト・画像で共通使用）===
BASE_PROMPT = """あなたはRe:findの分類アシスタントです。
Re:findは「後でやろうと思って保存した情報を埋もれさせない」サービスです。

以下のJSONのみを返してください。説明文・改行・コードブロック記号は一切不要です。
{{"title": "タイトル", "category": "カテゴリ名"}}

【titleのルール】
- 20文字以内の日本語
- ユーザーが後から見て内容をすぐ思い出せる具体的な表現にする
- 例: 「ピアノ教室の体験レッスン情報」「楽天クーポンの使い方」

【categoryのルール】
- 8文字以内の日本語（ひらがな・カタカナ・漢字）
- 「何をしたい情報か」が一言でわかる名前
- 既存カテゴリに合うものがあれば必ずそのまま使う
- なければ新しく作る（例: 習い事・買い物候補・レシピ・旅行・健康・家計・読みたい）
- 迷ったら「後でどう行動するか」の軸で判断する（買う・申し込む・読む・相談する）
- 分類が難しければ「記事」でまとめる

【既存カテゴリ一覧】
{categories}

【分類するテキスト】
{text}"""


def _check_env() -> None:
    """環境変数が設定されているか確認する。未設定の場合は RuntimeError を送出する。"""
    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY または AZURE_OPENAI_ENDPOINT が設定されていません"
        )


def build_prompt(text: str, existing_categories: list[str]) -> str:
    """既存カテゴリ＋テキストから、実際に投げるプロンプト文字列を組み立てる"""
    # カテゴリが空のときは明示的に「なし」と伝える
    cats_str = "、".join(existing_categories) if existing_categories else "（まだカテゴリはありません。新しく作成してください）"
    return BASE_PROMPT.format(categories=cats_str, text=text)


def parse_ai_response(content: str, fallback_title: str) -> dict:
    """
    AIの返答文字列をJSONとしてパースする共通処理。
    ``` json ``` 形式で返ってきた場合や、前後に余計なテキストがある場合にも対応。
    パース失敗時はフォールバック値を返す（例外を握りつぶさずに済む）。
    """
    # ``` json ``` や ``` ``` のコードブロック記号を除去
    content = re.sub(r"```[a-z]*\n?", "", content).strip()

    # JSON部分だけ正規表現で抽出（前後に余計なテキストが混入しても対応できる）
    match = re.search(r'\{.*?\}', content, re.DOTALL)
    if not match:
        # JSONが見つからなければフォールバック
        return {"title": fallback_title, "category": "未分類"}

    try:
        parsed = json.loads(match.group())
        return {
            "title": parsed.get("title") or fallback_title,
            "category": parsed.get("category") or "未分類",
        }
    except json.JSONDecodeError:
        # パース失敗時もフォールバック（本番でクラッシュしないようにする）
        return {"title": fallback_title, "category": "未分類"}


def detect_mime_type(image_bytes: bytes) -> str:
    """
    画像のバイナリデータを見てMIMEタイプを自動判定する関数。
    JPEGは先頭2バイトが FF D8、PNGは 89 50 4E 47 で始まる。
    """
    if image_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"   # JPEG / JPG
    elif image_bytes[:4] == b'\x89PNG':
        return "image/png"    # PNG
    else:
        return "image/png"    # その他はPNGとして扱う


def classify_text(text: str, existing_categories: list[str] | None = None) -> dict:
    """
    テキストをAIに渡して {"title": ..., "category": ...} を返す関数。
    GPT-5 mini は Responses API を使うため client.responses.create() を使用。
    """
    _check_env()  # 環境変数チェック（未設定なら即エラー）

    if existing_categories is None:
        existing_categories = []

    prompt = build_prompt(text, existing_categories)

    try:
        # GPT-5 mini は新しい Responses API を使う
        # chat.completions.create() ではなく responses.create() を使う点に注意
        response = client.responses.create(
            model=AZURE_DEPLOY_NAME,
            input=prompt,        # "messages" ではなく "input" を使う
        )

        # 返答テキストを取り出す（Responses API の形式）
        content = response.output_text

        return parse_ai_response(content, fallback_title=text[:30])

    except Exception as e:
        print("AI分類エラー:", e)
        return {"title": text[:30], "category": "未分類"}


def classify_image(image_bytes: bytes, existing_categories: list[str] | None = None) -> dict:
    """
    画像（スクショ）をAIに渡して {"title": ..., "category": ...} を返す関数。
    GPT-5 miniはマルチモーダル対応。JPEG・PNG どちらも自動判定して対応する。
    テキスト分類と同じ BASE_PROMPT を使うことで、分類ルールを統一している。
    """
    _check_env()  # 環境変数チェック（未設定なら即エラー）

    if existing_categories is None:
        existing_categories = []

    # 画像をBase64に変換（API送信用）
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # 画像の種類（JPEG or PNG）を自動判定
    mime_type = detect_mime_type(image_bytes)
    print(f"画像のMIMEタイプ: {mime_type}")

    # テキスト・画像で同じルールを適用するため BASE_PROMPT を共用する
    # 「テキスト」の部分には画像を読み取るよう指示を入れておく
    prompt_text = build_prompt(
        text="（以下の画像の内容を読み取って分類してください）",
        existing_categories=existing_categories,
    )

    try:
        # Responses API でマルチモーダル（テキスト＋画像）を送る形式
        response = client.responses.create(
            model=AZURE_DEPLOY_NAME,
            input=[
                {
                    "role": "user",
                    "content": [
                        # テキストの指示（BASE_PROMPTと同じルール）
                        {"type": "input_text", "text": prompt_text},
                        # 画像データ（Base64エンコード済み、MIMEタイプ自動判定）
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{base64_image}"
                        }
                    ]
                }
            ],
        )

        # 返答テキストを取り出す
        content = response.output_text
        print("画像AI返答:", content)

        return parse_ai_response(content, fallback_title="画像メモ")

    except Exception as e:
        print(f"AI画像解析エラー: {type(e).__name__}: {e}")
        return {"title": "画像メモ", "category": "未分類"}


# 単体テスト用（python ai_classifier.py で実行できる）
if __name__ == "__main__":
    import sys

    # --- テキスト分類テスト ---
    print("===== テキスト分類テスト =====")
    examples = [
        "駅前のピアノ教室。月曜16時に体験レッスンあり、小学生向け。",
        "楽天スーパーセールでスニーカー半額。23日まで。",
        "鶏むね肉と醤油・みりんで作る簡単照り焼きレシピ。",
    ]
    for ex in examples:
        print("----")
        print("入力:", ex)
        res = classify_text(ex, ["レシピ", "買い物候補"])
        print("結果:", res)

    # --- 画像分類テスト ---
    # 使い方: python ai_classifier.py 画像ファイル名.jpg
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n===== 画像分類テスト: {image_path} =====")
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        result = classify_image(image_bytes, ["季節行事", "買い物候補"])
        print("画像分類結果:", result)