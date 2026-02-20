# ============================================
# Re:find - LINE Bot Webhook サーバー
# ============================================
# LINEに送ったメッセージをFlaskで受け取り、
# AIで分類した結果を返信するコード

import os  # 環境変数を読み込むためのライブラリ
from dotenv import load_dotenv  # .env を読むため
from flask import Flask, request, abort  # Webサーバーの基本機能

# --- LINE Bot SDK の必要なパーツを読み込む ---
from linebot.v3 import WebhookHandler  # LINEからの通知を処理する
from linebot.v3.messaging import (
    Configuration,          # LINE APIの設定情報を管理
    ApiClient,              # LINE APIと通信するためのクライアント
    MessagingApi,           # メッセージ送受信の機能
    ReplyMessageRequest,    # 返信メッセージのリクエスト
    TextMessage,            # テキストメッセージ
)
from linebot.v3.webhooks import (
    MessageEvent,           # 「メッセージが届いた」というイベント
    TextMessageContent,     # テキストメッセージの中身
)
from linebot.v3.exceptions import InvalidSignatureError  # 署名エラー用

from ai_classifier import classify_text  # ← さっき作った共通関数

# ============================================
# .env 読み込み（ローカル開発用）
# ============================================
load_dotenv()

# ============================================
# Flaskアプリの初期化
# ============================================
app = Flask(__name__)

# ============================================
# LINE Bot の設定
# ============================================
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise RuntimeError(
        "LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN が設定されていません"
    )

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# ============================================
# ルート（URL）の設定
# ============================================

@app.route("/")
def index():
    """
    トップページ（動作確認用）
    """
    return "Re:find is running."


@app.route("/callback", methods=["POST"])
def callback():
    """
    LINEからのWebhook（通知）を受け取る入口
    """
    # ① リクエストヘッダーから署名を取得
    signature = request.headers.get("X-Line-Signature", "")

    # ② リクエストの本文（メッセージデータ）を取得
    body = request.get_data(as_text=True)
    print("受信:", body)  # ログに表示（デバッグ用）

    # ③ 署名を検証して、メッセージを処理する
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("署名エラー: 不正なリクエスト")
        abort(400)
    except Exception as e:
        print("その他エラー:", e)
        abort(500)

    return "OK"


# ============================================
# メッセージ受信時の処理（ここでAI分類）
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    テキストメッセージを受信したときに実行される関数
    """
    user_message = event.message.text
    user_id = event.source.user_id
    print(f"ユーザー {user_id} から: {user_message}")  # ログに記録

    # いまはDB未接続なので既存カテゴリは空でOK
    existing_categories: list[str] = []

    # --- AIでタイトル & カテゴリを推定 ---
    result = classify_text(user_message, existing_categories)
    title = result["title"]
    category = result["category"]

    reply_text = f"📌 分類結果\nタイトル: {title}\nカテゴリ: {category}"

    # LINEに返信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


# ============================================
# サーバー起動（ローカル実行用）
# ============================================
if __name__ == "__main__":
    # ローカルで python app.py を実行したときだけ動く
    app.run(debug=True)