import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

def main():
    if not API_KEY:
        print("OPENROUTER_API_KEY が設定されていません")
        return

    url = "https://openrouter.ai/api/v1/chat/completions"

    payload = {
        "model": "openrouter/free",  # ← ★ ここを追加！
        "messages": [
            {
                "role": "user",
                "content": "これはOpenRouterのテストです。短く一言で返してください。"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        # 下2つは任意（あればベター）
        "HTTP-Referer": "https://example.com",  # 自分のサイトがあればURLに変えてOK
        "X-Title": "refind-dev-test",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print("status:", resp.status_code)

    try:
        data = resp.json()
    except Exception:
        print("レスポンスをJSONとして読めません:")
        print(resp.text)
        return

    # エラー時は内容だけ表示して終わる
    if resp.status_code != 200:
        print("エラー内容:", data)
        return

    # 成功時だけ choices を読む
    print("raw data:", data)
    print("result:", data["choices"][0]["message"]["content"])

if __name__ == "__main__":
    main()