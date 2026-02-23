# ai_classifier.py
# Re:find 用の「テキスト・画像分類」共通関数
# ※ OpenRouter → Azure OpenAI (gpt-5-mini) に変更

import os
import base64
import json
from openai import AzureOpenAI  # Azure OpenAI 専用クライアント
from dotenv import load_dotenv

# ローカル開発時は .env を読み込む
load_dotenv()

# ===================================================
# Azure OpenAI の接続情報（環境変数から取得）
# Renderの環境変数 or .env に以下を設定してください:
#   AZURE_OPENAI_API_KEY  : AzureポータルでコピーしたAPIキー
#   AZURE_OPENAI_ENDPOINT : https://refind-openai.openai.azure.com/ のようなURL
# ===================================================
AZURE_API_KEY      = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT     = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION  = "2024-12-01-preview"  # Azureが指定するAPIバージョン
AZURE_DEPLOY_NAME  = "gpt-5-mini"          # Foundryでデプロイした名前

# Azure OpenAI クライアントを初期化
# ※ このクライアントを通じてAPIを呼び出す
client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
)


# === 分類用プロンプト（変更なし） ===
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
    if existing_categories:
        cats_str = "、".join(existing_categories)
    else:
        cats_str = "なし"
    return BASE_PROMPT.format(categories=cats_str, text=text)


def parse_ai_response(content: str, fallback_title: str) -> dict:
    """
    AIの返答文字列をJSONとしてパースする共通処理。
    ``` json ``` 形式で返ってきた場合にも対応。
    """
    # ```json ... ``` 形式の場合にコードブロックを取り除く
    if "```" in content:
        part = content.split("```")
        content = max(part, key=len)  # 一番長い部分をJSON候補とする
        if content.strip().startswith("json"):
            content = content.strip()[4:]

    parsed = json.loads(content.strip())
    return {
        "title": parsed.get("title") or fallback_title,
        "category": parsed.get("category") or "未分類",
    }


def classify_text(text: str, existing_categories: list[str] | None = None) -> dict:
    """
    テキストをAIに渡して {"title": ..., "category": ...} を返す関数。
    （URLのOGPテキストや手入力テキストに使用）
    """
    if existing_categories is None:
        existing_categories = []

    # 環境変数が設定されているか確認
    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY または AZURE_OPENAI_ENDPOINT が設定されていません"
        )

    prompt = build_prompt(text, existing_categories)

    try:
        # Azure OpenAI にテキストを送って分類してもらう
        response = client.chat.completions.create(
            model=AZURE_DEPLOY_NAME,       # Foundryでデプロイしたモデル名
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=30,
        )

        # AIの返答テキストを取り出す
        content = response.choices[0].message.content

        return parse_ai_response(content, fallback_title=text[:30])

    except Exception as e:
        # エラーが起きても最低限動くようにフォールバック
        print("AI分類エラー:", e)
        return {
            "title": text[:30],
            "category": "未分類",
        }


def classify_image(image_bytes: bytes, existing_categories: list) -> dict:
    """
    画像（スクショ）をAIに渡して {"title": ..., "category": ...} を返す関数。
    GPT-5 miniはマルチモーダル対応なので画像を直接理解できる。
    """

    # ===============================
    # 画像をBase64に変換（API送信用）
    # バイナリデータ → テキスト形式に変換してAPIに送る
    # ===============================
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # 既存カテゴリ一覧を文字列に変換
    categories_str = "、".join(existing_categories) if existing_categories else "なし"

    # ===============================
    # AIへの指示文（プロンプト）
    # ===============================
    prompt = f"""
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
        # Azure OpenAI にテキスト＋画像を送って分類してもらう
        # content を「テキスト」と「画像」のリスト形式で渡すのがマルチモーダルの書き方
        response = client.chat.completions.create(
            model=AZURE_DEPLOY_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        # テキストの指示
                        {"type": "text", "text": prompt},
                        # 画像データ（Base64エンコード済み）
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            timeout=60,  # 画像処理は時間がかかるので長めに設定
        )

        # AIの返答テキストを取り出す
        content = response.choices[0].message.content

        return parse_ai_response(content, fallback_title="画像メモ")

    except Exception as e:
        print("AI画像解析エラー:", e)
        return {"title": "画像メモ", "category": "未分類"}


# 単体テスト用（python ai_classifier.py で実行できる）
if __name__ == "__main__":
    examples = [
        "駅前のピアノ教室。月曜16時に体験レッスンあり、小学生向け。",
        "楽天スーパーセールでスニーカー半額。23日まで。",
        "鶏むね肉と醤油・みりんで作る簡単照り焼きレシピ。",
    ]
    for ex in examples:
        print("====")
        print("入力:", ex)
        res = classify_text(ex, ["レシピ", "買い物候補"])
        print("結果:", res)
