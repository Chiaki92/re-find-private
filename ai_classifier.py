# ai_classifier.py
# Re:find 用の「テキスト・画像分類」共通関数
# ※ GPT-5 mini は新しい Responses API を使うため、chat.completions ではなく responses を使用

import os
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


# === 分類用プロンプト ===
BASE_PROMPT = """あなたは「Re:find」という、後で見返したい情報を整理するサービスの分類アシスタントです。

ユーザーが保存したテキストを渡すので、
以下のJSON形式で「タイトル」と「カテゴリ」を決めてください。

返すJSONの形式（必ずこの通りにしてください）:
{{"title": "20文字以内の簡潔なタイトル", "category": "カテゴリ名"}}

【ルール】
- 出力はJSONのみとし、日本語の説明文やコードブロック記号（```）は一切書かないこと。
- title は、ユーザーが後から見たときに内容を思い出せる短い日本語にすること。
  - 例: 「ピアノ教室の体験レッスン情報」「楽天スーパーセールのクーポン」など。
- category は、「何のための情報か」が一言で分かる名前にすること。
  - 例: 「習い事」「買い物候補」「レシピ」「仕事の連絡」「旅行」「健康」「家計」など。
- すでに存在するカテゴリ一覧が与えられるので、合うものがあればその名前をそのまま使うこと。
- 合うカテゴリがなければ、新しいカテゴリ名を作ってよい。
- カテゴリ名は8文字以内の日本語（ひらがな・カタカナ・漢字）にすること。
- 曖昧な場合は、ユーザーが「後で行動したい軸」に近いカテゴリを選ぶこと（例: 買う・申し込む・読む・相談する など）。

【既存カテゴリ一覧】
{categories}

【分類したいテキスト】
{text}
"""


def build_prompt(text: str, existing_categories: list[str]) -> str:
    """既存カテゴリ＋テキストから、実際に投げるプロンプト文字列を組み立てる"""
    cats_str = "、".join(existing_categories) if existing_categories else "なし"
    return BASE_PROMPT.format(categories=cats_str, text=text)


def parse_ai_response(content: str, fallback_title: str) -> dict:
    """
    AIの返答文字列をJSONとしてパースする共通処理。
    ``` json ``` 形式で返ってきた場合にも対応。
    """
    if "```" in content:
        part = content.split("```")
        content = max(part, key=len)
        if content.strip().startswith("json"):
            content = content.strip()[4:]

    parsed = json.loads(content.strip())
    return {
        "title": parsed.get("title") or fallback_title,
        "category": parsed.get("category") or "未分類",
    }


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
    if existing_categories is None:
        existing_categories = []

    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY または AZURE_OPENAI_ENDPOINT が設定されていません"
        )

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


def classify_image(image_bytes: bytes, existing_categories: list) -> dict:
    """
    画像（スクショ）をAIに渡して {"title": ..., "category": ...} を返す関数。
    GPT-5 miniはマルチモーダル対応。JPEG・PNG どちらも自動判定して対応する。
    """

    # 画像をBase64に変換（API送信用）
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # 画像の種類（JPEG or PNG）を自動判定
    mime_type = detect_mime_type(image_bytes)
    print(f"画像のMIMEタイプ: {mime_type}")

    # 既存カテゴリ一覧を文字列に変換
    categories_str = "、".join(existing_categories) if existing_categories else "なし"

    prompt_text = f"""
この画像を見て、
・20文字以内のタイトル
・8文字以内のカテゴリ
をJSON形式で出力してください。

既存カテゴリ:
{categories_str}

必ず以下の形式のみで出力（説明文不要）:
{{"title":"〇〇","category":"〇〇"}}
"""

    try:
        # Responses API でマルチモーダル（テキスト＋画像）を送る形式
        response = client.responses.create(
            model=AZURE_DEPLOY_NAME,
            input=[
                {
                    "role": "user",
                    "content": [
                        # テキストの指示
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
