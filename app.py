# ============================================
# Re:find - LINE Bot Webhook サーバー
# ============================================
# LINEに送ったメッセージをFlaskで受け取り、
# オウム返しで返信するテスト用コード

import os  # 環境変数を読み込むためのライブラリ
from flask import Flask, request, abort  # Webサーバーの基本機能

# --- LINE Bot SDK の必要なパーツを読み込む ---
from linebot.v3 import WebhookHandler  # LINEからの通知を処理する
from linebot.v3.messaging import (
    Configuration,          # LINE APIの設定情報を管理
    ApiClient,              # LINE APIと通信するためのクライアント
    MessagingApi,           # メッセージ送受信の機能
    ReplyMessageRequest,    # 返信メッセージのリクエスト
    TextMessage             # テキストメッセージ
)
from linebot.v3.webhooks import (
    MessageEvent,           # 「メッセージが届いた」というイベント
    TextMessageContent      # テキストメッセージの中身
)

# ============================================
# Flaskアプリの初期化
# ============================================
app = Flask(__name__)

# ============================================
# LINE Bot の設定
# ============================================
# Renderの環境変数から秘密情報を読み込む
# （コードに直接書かないのがセキュリティのポイント！）
configuration = Configuration(
    access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# ============================================
# ルート（URL）の設定
# ============================================

@app.route("/")
def index():
    """
    トップページ（動作確認用）
    ブラウザで https://re-find.onrender.com/ にアクセスすると表示される
    """
    return "Re:find is running."


@app.route("/callback", methods=["POST"])
def callback():
    """
    LINEからのWebhook（通知）を受け取る入口
    - LINEでメッセージを送ると、LINEサーバーがこのURLにデータを送ってくる
    - 正しいリクエストかどうかを signature（署名）で検証する
    """
    # ① リクエストヘッダーから署名を取得（本物のLINEからか確認するため）
    signature = request.headers["X-Line-Signature"]

    # ② リクエストの本文（メッセージデータ）を取得
    body = request.get_data(as_text=True)
    print("受信:", body)  # Renderのログに表示される（デバッグ用）

    # ③ 署名を検証して、メッセージを処理する
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("エラー:", e)  # エラーが起きたらログに表示
        abort(400)  # 400エラー（不正なリクエスト）を返す

    return "OK"

# ============================================
# メッセージ受信時の処理
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    テキストメッセージを受信したときに実行される関数
    - event: LINEから届いたイベント情報が入っている
    - event.message.text: 送られてきたメッセージの内容
    - event.source.user_id: 送ってきたユーザーのID
    """
    # 受信したメッセージとユーザーIDを取り出す
    user_message = event.message.text
    user_id = event.source.user_id
    print(f"ユーザー {user_id} から: {user_message}")  # ログに記録

    # --- オウム返しで返信する（テスト用） ---
    # 後でここをAI分類やデータベース保存に置き換える
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,  # 返信に必要なトークン
                messages=[TextMessage(text=f"受信しました: {user_message}")]
            )
        )

# ============================================
# サーバー起動（ローカル実行用）
# ============================================
if __name__ == "__main__":
    # ローカルで python app.py を実行したときだけ動く
    # Renderでは gunicorn が起動するのでここは通らない
    app.run(debug=True)