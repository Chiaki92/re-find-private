# ai_classifier.py
# Re:find 用の「テキスト分類」共通関数

import os
import json
import requests
from dotenv import load_dotenv

# ローカル開発時は .env を読み込む
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# === 分類用プロンプト（B-2-2で決めたやつ） ===
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


def classify_text(text: str, existing_categories: list[str] | None = None) -> dict:
    """
    任意のテキストをAIに渡して、
    {"title": ..., "category": ...} 形式の辞書を返す共通関数。
    """
    if existing_categories is None:
        existing_categories = []

    if not OPENROUTER_API_KEY:
        # 開発中に気づきやすいように例外にしておく
        raise RuntimeError("OPENROUTER_API_KEY が設定されていません")

    prompt = build_prompt(text, existing_categories)

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://example.com",  # 本番で自分たちのURLに変える
                "X-Title": "refind-ai-classifier",
            },
            json={
                "model": "openrouter/free",  # まずは無料ルーターでOK
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            },
            timeout=30,
        )
        data = resp.json()

        if resp.status_code != 200:
            # エラー時はログだけ出してフォールバック
            print("AI API エラー:", resp.status_code, data)
            return {
                "title": text[:30],
                "category": "未分類",
            }

        content = data["choices"][0]["message"]["content"]

        # もし ```json ... ``` 形式で返ってきた場合のガード
        if "```" in content:
            part = content.split("```")
            # 一番長そうな部分を JSON 候補として扱う
            content = max(part, key=len)
            if content.strip().startswith("json"):
                content = content.strip()[4:]

        parsed = json.loads(content.strip())

        return {
            "title": parsed.get("title") or text[:30],
            "category": parsed.get("category") or "未分類",
        }

    except Exception as e:
        print("AI分類エラー:", e)
        # 何かあっても最低限動くようにフォールバック
        return {
            "title": text[:30],
            "category": "未分類",
        }


# 単体テスト用
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