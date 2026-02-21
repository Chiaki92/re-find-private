# Re:find — タスク詳細ガイド（TODO リスト対応版）

> **このドキュメントの使い方**
> TODOリスト（Excel）の各タスクIDに対応した「具体的に何をするか」をまとめています。
> 作業中にTODOリストと並べて開き、「今やるタスクID」を探して読んでください。
> 各タスクには **完了チェック**（何ができていればOKか）を書いています。

---

## 2/19（木）：企画仕上げ

### ✅ この日のゴール
チーム全員が「明日から何を作るか」を理解していること。

---

### No.1 | A-4-1：DB設計ドキュメントをチームで読み合わせ（30分）

**何をするか：** `Re_find_データベース設計.md` を全員で一緒に読む。

**具体的な進め方：**
1. 画面共有（Zoom等）でドキュメントを映す
2. 以下の7つのテーブルを順番に確認する
   - **users** — LINEのIDとSupabase認証IDの橋渡し
   - **categories** — ユーザーごとのカテゴリ（「レシピ」「習い事」など）
   - **items** — 保存した情報の本体（メインテーブル）
   - **shared_links** — 共有リンクのURL管理
   - **user_activity_logs** — 行動ログ（将来の分析用）
   - **user_settings** — 通知時間などの設定
   - **notification_rules** — 通知のタイミングルール
3. 各テーブルについて「このテーブルは何のためにあるの？」を確認
4. わからない用語があればその場で質問する

**完了チェック：**
- [ ] 全員が「items テーブルが一番大事で、ここにユーザーが保存した情報が入る」と説明できる
- [ ] 「ソフトデリート」が何かを全員が理解している（物理削除しない方式）
- [ ] 「RLS」が何かを全員が理解している（自分のデータだけ見える仕組み）

---

### No.2 | A-4-2：技術スタックの未決事項をチームで決定（30分）

**何をするか：** まだ決まっていない3つの項目をチームで議論して決める。

**議論する3項目：**

**① CSSフレームワーク**
- **Bootstrap**（おすすめ）：HTMLにクラス名を書くだけで見た目が整う。学習コストが一番低い
- **Tailwind CSS**：自由度が高いが慣れが必要。後から入れると全部書き直し
- **素のCSS**：全部自分で書く。時間がかかる

→ 初心者チームには **Bootstrap** がおすすめ。CDNリンク1行で導入できる

**② PDF対応をPhase 1に入れるか**
- 入れる場合：PyPDF2 というライブラリでPDFのテキストを取り出せる
- 入れない場合：「現在はPDFに非対応です」とLINEで返す

→ 2週間のスケジュールを考えると **入れない（見送り）** が安全

**③ 共有リンクのRLS方式**
- **方法A（Flask側で処理）**：推奨。Flaskに慣れているチーム向き
- **方法B（SupabaseのRLSルール変更）**：RLSの設定が複雑になる

→ **方法Aで確定** がおすすめ

**完了チェック：**
- [ ] 3項目すべてについてチームで決定した
- [ ] 決定内容をメモに残した

---

### No.3 | A-4-3：決定事項をドキュメントに反映（15分）

**何をするか：** A-4-2 で決めた内容を `技術スタック検討まとめ_改訂版.md` に書き込む。

**具体的にやること：**
1. ドキュメント内の「チーム議論項目」のセクションを見つける
2. 各項目に決定結果を書き加える（例：「CSSフレームワーク → Bootstrap に決定」）
3. チーム全員に共有する

**完了チェック：**
- [ ] ドキュメントが最終版になっている

---

### No.4 | A-5-1：タスク分解ドキュメントをチームで確認・担当決め（30分）

**何をするか：** このTODOリスト（Excel）を見ながら、各タスクの担当者を決める。

**具体的な進め方：**
1. TODOリスト（Excel）を開く
2. 日付ごとに「誰がどのタスクをやるか」を決める
3. **並行作業**（🔀マーク）に注目。同時に進められるタスクは別の人に振る

**担当の振り方の例：**

| 日付 | 担当A | 担当B | 担当C |
|------|-------|-------|-------|
| 2/20 | Flask + GitHub + Render（A-6-1〜3） | Supabase設定（B-1-1〜10） | LINE Developers設定（A-6-4, A-6-5） |
| 2/21 | AI分類（B-2） | 画像解析 + Storage（B-3） | プロンプト調整・テスト |
| 2/22 | OGP取得（B-4） | エラーハンドリング | ログ記録 + レビュー① |

4. 担当列（F列）に名前を記入する

**完了チェック：**
- [ ] すべてのタスクに担当者が入っている
- [ ] スケジュールシートにも反映した

---

### No.5 | A-5-2：各自のアカウント準備を確認（15分）

**何をするか：** 開発に必要な4つのサービスのアカウントを全員が持っているか確認する。

**必要なアカウント一覧：**

| サービス | URL | 用途 |
|---------|-----|------|
| GitHub | https://github.com | コードの共有・管理 |
| Render | https://render.com | アプリの公開（デプロイ） |
| Supabase | https://supabase.com | データベース + 認証 |
| LINE Developers | https://developers.line.biz | LINE Bot作成 |

**確認方法：** 各サービスにログインできるかを各自確認。できない人は今日中に作成。

**完了チェック：**
- [ ] 全員が4つのアカウントにログインできる状態

---
---

## 2/20（金）：バックエンド① — 開発基盤を作る

### ✅ この日のゴール
LINEでテキストを送ったらサーバーのログに表示される ＋ PythonからSupabaseにデータ読み書きできる。

---

### No.6 | A-6-1：GitHubリポジトリを作成する（15分）

**何をするか：** チーム共有のコード置き場を作る。

**手順：**
1. GitHub（https://github.com）にログイン
2. 右上の「+」→「New repository」をクリック
3. 設定する項目：
   - **Repository name**：`re-find`
   - **Description**：「情報再発見サービス Re:find」（任意）
   - **Public / Private**：**Private**（外部に公開しない）
   - **Add a README file**：✅ チェックを入れる
   - **Add .gitignore**：「Python」を選択
4. 「Create repository」をクリック
5. チームメンバーを招待：
   - リポジトリページ → Settings → Collaborators → 「Add people」
   - せとさん・木村さんのGitHubユーザー名を入力して招待

**完了チェック：**
- [✅] `re-find` リポジトリが作成されている
- [ ] チームメンバー全員が招待されている

---

### No.7 | A-6-2：Flaskプロジェクトの雛形を作成する（30分）

**何をするか：** Webアプリの土台となるファイル群を作る。

**手順：**

1. GitHubリポジトリをPCにクローン（コピー）する
```bash
git clone https://github.com/あなたのユーザー名/re-find.git
cd re-find
```

2. 以下のファイルを作成する：

**① app.py**（Flaskのメインファイル）
```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello! Re:find is running."

if __name__ == "__main__":
    app.run(debug=True)
```

**② requirements.txt**（必要なライブラリ一覧）
```
flask
gunicorn
line-bot-sdk
supabase
requests
beautifulsoup4
python-dotenv
```

**③ .env.example**（環境変数のサンプル。中身は空でOK）
```
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENROUTER_API_KEY=
```

**④ templates/index.html**（仮のトップページ）
```html
<!DOCTYPE html>
<html>
<head><title>Re:find</title></head>
<body><h1>Re:find</h1><p>Hello!</p></body>
</html>
```

3. ローカルで動作確認
```bash
pip install flask
python app.py
```
→ ブラウザで `http://127.0.0.1:5000` を開いて「Hello! Re:find is running.」が表示されればOK

4. GitHubにプッシュ
```bash
git add .
git commit -m "Flaskプロジェクト初期構築"
git push
```

**完了チェック：**
- [✅] ローカルで Flask が起動して画面が表示される
- [✅] GitHub に全ファイルがプッシュされている

---

### No.8 | A-6-3：Renderにデプロイする（30分）

**何をするか：** 作ったアプリをインターネット上に公開する。

**手順：**
1. Render（https://render.com）にログイン
2. 「New +」→「Web Service」をクリック
3. 「Connect a repository」→ GitHubアカウントを連携
4. `re-find` リポジトリを選択
5. 設定する項目：
   - **Name**：`re-find`（URLが `re-find.onrender.com` になる）
   - **Region**：Singapore（日本に近い）
   - **Runtime**：Python 3
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`gunicorn app:app`
   - **Instance Type**：**Free**（無料）
6. 「Deploy Web Service」をクリック
7. デプロイ完了まで数分待つ（ログが流れるのを見守る）
8. `https://re-find.onrender.com` にアクセスして確認

**⚠️ よくあるトラブル：**
- 「Build failed」→ requirements.txt のスペルミスがないか確認
- 画面が出ない → 数分待ってからアクセスし直す（初回は起動が遅い）

**完了チェック：**
- [✅] `https://re-find.onrender.com` で「Hello! Re:find is running.」が表示される

---

### No.9 | A-6-4：LINE Developersでチャネルを作成する（30分）

**何をするか：** LINE Botの管理画面でBot用のチャネル（箱）を作る。

**手順：**
1. LINE Developers（https://developers.line.biz）にログイン
2. 「プロバイダー」→「新規プロバイダー作成」→ 名前を入力（例：「Re:find」）
3. 作成したプロバイダーの中に「Messaging API」チャネルを作成
   - **チャネルの種類**：Messaging API
   - **チャネル名**：Re:find
   - **チャネル説明**：情報再発見サービス
   - **大業種**：個人
   - **小業種**：個人（その他）
4. 作成後、以下の2つをメモする（後で使う）：
   - **Channel Secret**：「チャネル基本設定」タブの下の方にある
   - **Channel Access Token**：「Messaging API設定」タブ → 「チャネルアクセストークン（長期）」の「発行」を押す
5. **応答設定の変更**（重要！）：
   - 「Messaging API設定」タブ → 「LINE Official Account features」→「応答メッセージ」→「編集」をクリック
   - LINE Official Account Managerが開く
   - 「応答メッセージ」→ **オフ** にする
   - 「Webhook」→ **オン** にする

**⚠️ なぜ応答メッセージをオフにするか：**
オンのままだと、ユーザーが送ったメッセージにLINEの自動応答が返ってしまい、自分で作ったBotの返信とかぶる。

**完了チェック：**
- [✅] Channel Secret をメモした
- [✅] Channel Access Token を発行してメモした
- [✅] 応答メッセージがオフ・Webhookがオンになっている

---

### No.10 | A-6-5：LINE Bot の Webhook を Flask に接続する（45分）

**何をするか：** LINEに送ったメッセージがFlaskに届くようにする。

**前提：** A-6-3（Renderデプロイ）と A-6-4（LINE設定）が完了していること。

**手順：**

1. Render の環境変数を設定する
   - Renderのダッシュボード → `re-find` サービス → 「Environment」タブ
   - 以下を追加：
     - `LINE_CHANNEL_SECRET` = （メモした Channel Secret）
     - `LINE_CHANNEL_ACCESS_TOKEN` = （メモした Channel Access Token）

2. `app.py` を修正してWebhookを受け取れるようにする
```python
import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# LINE Bot の設定
configuration = Configuration(
    access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    return "Re:find is running."

@app.route("/callback", methods=["POST"])
def callback():
    # LINEからのリクエストを検証する
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("受信:", body)  # ログに表示（デバッグ用）
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("エラー:", e)
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    # テキストメッセージを受信したとき
    user_message = event.message.text
    user_id = event.source.user_id
    print(f"ユーザー {user_id} から: {user_message}")

    # オウム返し（テスト用）
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"受信しました: {user_message}")]
            )
        )

if __name__ == "__main__":
    app.run(debug=True)
```

3. GitHubにプッシュ → Render が自動デプロイする
```bash
git add .
git commit -m "LINE Webhook接続"
git push
```

4. LINE Developers で Webhook URL を設定
   - 「Messaging API設定」タブ → 「Webhook URL」
   - `https://re-find.onrender.com/callback` を入力
   - 「検証」ボタンをクリック → 「成功」が出ればOK
   - 「Webhookの利用」→ **オン**

5. QRコードでBotを友達追加して、テキストを送ってみる
   - Messaging API設定のQRコードをスマホで読み取り、友達追加
   - 「テスト」と送る → 「受信しました: テスト」が返ってくればOK

**⚠️ よくあるトラブル：**
- 「検証」で失敗 → Renderがスリープ中の可能性。先にブラウザで `re-find.onrender.com` にアクセスして起こしてから再度検証
- Botから返信が来ない → Renderのログ（「Logs」タブ）でエラーを確認

**完了チェック：**
- [✅] LINEでテキストを送ると、オウム返しの返信が来る
- [✅] Render のログに「ユーザー UXXXX から: テスト」のようなログが出ている

---

### No.11 | B-1-1：Supabaseプロジェクトを作成する（15分）

**何をするか：** データベースの「場所」を作る。

**手順：**
1. Supabase（https://supabase.com）にログイン
2. 「New Project」をクリック
3. 設定する項目：
   - **Organization**：デフォルトのもの（なければ作成）
   - **Name**：`re-find`
   - **Database Password**：強いパスワードを設定して**メモ**（後で使う可能性あり）
   - **Region**：**Northeast Asia (Tokyo)**
   - **Pricing Plan**：Free（無料）
4. 「Create new project」をクリック → 数分待つ
5. プロジェクトができたら、以下の3つをメモ：
   - **Project URL** → Settings → API → Project URL
   - **anon key**（公開キー）→ Settings → API → `anon` `public`
   - **service_role key**（管理者キー）→ Settings → API → `service_role` `secret`

**⚠️ 重要：** service_role key は「管理者用」のキー。共有リンク機能で使うが、**絶対にフロントエンドのJavaScriptには書かない**。Flaskのサーバー側コードだけで使う。

**完了チェック：**
- [✅] Supabaseプロジェクトが作成された
- [✅] 3つのキー（URL, anon key, service_role key）をメモした

---

### No.12 | B-1-2：テーブル作成 — users（10分）

**何をするか：** ユーザー情報を保存するテーブルを作る。

**手順：**
1. Supabase管理画面 → 左メニュー「SQL Editor」をクリック
2. 「New query」をクリック
3. 以下のSQLをコピー＆ペーストして「Run」を押す：

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    line_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

4. 「Success」と表示されればOK
5. 左メニュー「Table Editor」で `users` テーブルが表示されることを確認

**このテーブルの役割：** LINE Bot で使う ID（U1234...）と、Webアプリのログインで使う ID（UUID形式）を紐づける。同じ人なのにIDが違う問題を解決するための橋渡しテーブル。

**完了チェック：**
- [✅] Table Editor に `users` テーブルが表示される

---

### No.13 | B-1-3：テーブル作成 — categories（10分）

**何をするか：** カテゴリ情報を保存するテーブルを作る。

**手順：** SQL Editor で以下を実行：

```sql
CREATE TABLE categories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (line_user_id, name)
);
```

**ユニーク制約の確認テスト：**
```sql
-- テストデータを入れてみる
INSERT INTO categories (line_user_id, name) VALUES ('test_user', 'レシピ');
-- 同じデータをもう一回入れる → エラーになればOK
INSERT INTO categories (line_user_id, name) VALUES ('test_user', 'レシピ');
-- ↑ "duplicate key value violates unique constraint" が出る
-- テストデータを消す
DELETE FROM categories WHERE line_user_id = 'test_user';
```

**完了チェック：**
- [✅] Table Editor に `categories` テーブルが表示される
- [✅] 同じデータを2回INSERTしたらエラーが出る（ユニーク制約が効いている）

---

### No.14 | B-1-4：テーブル作成 — items（10分）

**何をするか：** ユーザーが保存した情報の本体テーブルを作る。**一番重要なテーブル。**

**手順：** SQL Editor で以下を実行：

```sql
CREATE TABLE items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('image', 'url', 'text')),
    original_url TEXT,
    image_url TEXT,
    title TEXT,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    memo TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'archived')),
    ogp_image TEXT,
    next_notify_at TIMESTAMPTZ,
    notify_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
```

**CHECK制約の確認テスト：**
```sql
-- type に 'video' を入れてみる → エラーになればOK
INSERT INTO items (line_user_id, type) VALUES ('test_user', 'video');
-- ↑ "new row violates check constraint" が出る
```

**完了チェック：**
- [✅] Table Editor に `items` テーブルが表示される
- [✅] type に 'video' を入れたらエラーが出る（CHECK制約が効いている）

---

### No.15 | B-1-5：テーブル作成 — shared_links, user_activity_logs（10分）

**手順：** SQL Editor で以下を実行（2つまとめて）：

```sql
-- 共有リンク
CREATE TABLE shared_links (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL,
    item_id UUID REFERENCES items(id) ON DELETE RESTRICT,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 行動ログ
CREATE TABLE user_activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    item_id UUID REFERENCES items(id) ON DELETE RESTRICT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 行動ログの検索を速くするインデックス
CREATE INDEX idx_activity_logs_user_time 
ON user_activity_logs (line_user_id, created_at);
```

**完了チェック：**
- [✅] Table Editor に `shared_links` と `user_activity_logs` の2テーブルが表示される

---

### No.16 | B-1-6：テーブル作成 — user_settings, notification_rules（10分）

**手順：** SQL Editor で以下を実行：

```sql
-- ユーザー設定
CREATE TABLE user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL UNIQUE,
    notify_time TIME NOT NULL DEFAULT '21:00',
    notify_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    timezone TEXT NOT NULL DEFAULT 'Asia/Tokyo',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 通知ルール
CREATE TABLE notification_rules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    line_user_id TEXT NOT NULL,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE RESTRICT,
    rule_type TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**完了チェック：**
- [✅] Table Editor に全7テーブルが表示される（users, categories, items, shared_links, user_activity_logs, user_settings, notification_rules）

---

### No.17 | B-1-7：トリガーを設定する（10分）

**何をするか：** items 等のテーブルで「データを更新したら updated_at が自動で今の時刻になる」仕組みを作る。

**手順：** SQL Editor で以下を実行：

```sql
-- トリガー関数の作成
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- items テーブルに設定
CREATE TRIGGER trigger_items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- user_settings テーブルに設定
CREATE TRIGGER trigger_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- notification_rules テーブルに設定
CREATE TRIGGER trigger_notification_rules_updated_at
    BEFORE UPDATE ON notification_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

**動作確認（任意）：**
```sql
-- テストデータを入れる
INSERT INTO user_settings (line_user_id) VALUES ('trigger_test');
-- updated_at を確認
SELECT updated_at FROM user_settings WHERE line_user_id = 'trigger_test';
-- 数秒待ってからデータを更新
UPDATE user_settings SET notify_time = '20:00' WHERE line_user_id = 'trigger_test';
-- updated_at が変わっていればOK
SELECT updated_at FROM user_settings WHERE line_user_id = 'trigger_test';
-- テストデータを消す
DELETE FROM user_settings WHERE line_user_id = 'trigger_test';
```

**完了チェック：**
- [✅] 3つのトリガーが作成された（エラーなく実行完了）

---

### No.18 | B-1-8：RLSを有効化してポリシーを設定する（20分）

**何をするか：** 「自分のデータだけ見える」仕組みをDB側で強制する。

**⚠️ 最重要注意：** RLS を ON にすると、ポリシーが正しくないとデータが一切読めなくなる。設定後に必ずテストすること。

**手順：** SQL Editor で以下を**1つずつ**実行する（まとめて実行してもOKだが、エラーの特定が難しくなる）：

```sql
-- ① users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分のユーザー情報だけ" ON users
FOR ALL USING (id = auth.uid());

-- ② categories
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分のカテゴリだけ" ON categories
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);

-- ③ items
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分のアイテムだけ" ON items
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);

-- ④ shared_links
ALTER TABLE shared_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分の共有リンクだけ" ON shared_links
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);

-- ⑤ user_activity_logs
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分のログだけ" ON user_activity_logs
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);

-- ⑥ user_settings
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分の設定だけ" ON user_settings
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);

-- ⑦ notification_rules
ALTER TABLE notification_rules ENABLE ROW LEVEL SECURITY;
CREATE POLICY "自分の通知ルールだけ" ON notification_rules
FOR ALL USING (
    line_user_id = (SELECT line_user_id FROM users WHERE id = auth.uid())
);
```

**完了チェック：**
- [✅] 7テーブル全てでRLSが「Enabled」になっている（Table Editor の各テーブルで確認可能）

---

### No.19 | B-1-9：Storageバケットを作成する（10分）

**何をするか：** スクショ画像の保存先を作る。

**手順：**
1. 左メニュー「Storage」をクリック
2. 「New bucket」をクリック
3. **Name**：`screenshots`
4. **Public bucket**：✅ チェックを入れる（画像を表示するために必要）
5. 「Create bucket」をクリック

**完了チェック：**
- [✅] Storage に `screenshots` バケットが表示される

---

### No.20 | B-1-10：PythonからSupabaseに接続テストする（30分）

**何をするか：** Flaskから実際にデータの読み書きができるか確認する。

**手順：**

1. Renderの環境変数に以下を追加：
   - `SUPABASE_URL` = （メモした Project URL）
   - `SUPABASE_KEY` = （メモした anon key）
   - `SUPABASE_SERVICE_ROLE_KEY` = （メモした service_role key）

2. `app.py` にテスト用のルートを**一時的に**追加：
```python
import os
from supabase import create_client

supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

@app.route("/test-db")
def test_db():
    try:
        # カテゴリを追加
        supabase_admin.table("categories").insert({
            "line_user_id": "test_user",
            "name": "テストカテゴリ"
        }).execute()

        # カテゴリを取得
        result = supabase_admin.table("categories") \
            .select("*") \
            .eq("line_user_id", "test_user") \
            .execute()

        # テストデータを削除
        supabase_admin.table("categories") \
            .delete() \
            .eq("line_user_id", "test_user") \
            .execute()

        return f"成功！取得データ: {result.data}"
    except Exception as e:
        return f"エラー: {e}"
```

3. GitHubにプッシュしてデプロイ
4. `https://re-find.onrender.com/test-db` にアクセス
5. 「成功！取得データ: [...]」が表示されればOK
6. **テスト後、テストコードを削除する**（本番には残さない）

**完了チェック：**
- [✅] `/test-db` で「成功」が表示される
- [✅] テストコードを削除してプッシュした

---
---

## 2/21（土）：バックエンド② — AI処理の実装

### ✅ この日のゴール
LINEで画像やテキストを送ると、AIが分類してDBに保存される。

---

### No.21 | B-2-1：OpenRouterアカウント作成と動作確認（20分）

**何をするか：** AI分類に使うサービスのアカウントを作って接続テストする。

**手順：**
1. OpenRouter（https://openrouter.ai）にアクセス
2. アカウント作成（GoogleアカウントでOK）
3. 「Keys」ページ → 「Create key」→ APIキーが発行される → **メモ**
4. Renderの環境変数に追加：`OPENROUTER_API_KEY` = （メモしたキー）

5. Pythonで接続テスト（ローカルまたはRender上）：
```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "qwen/qwen3-235b-a22b:free",
        "messages": [{"role": "user", "content": "こんにちは"}]
    }
)
print(response.json())
```
→ AIの返答が返ってくればOK

**完了チェック：**
- [✅] APIキーを取得してRenderの環境変数に設定した
- [✅] AIに「こんにちは」を送って返答が返ってくる

> **📝 実装変更メモ（B-2-1）**
> - **テキスト分類モデルを変更**：当初予定の `qwen/qwen3-235b-a22b:free` → **`openrouter/free`**（OpenRouter の無料ルーター）に変更。特定モデルに依存せず、利用可能な無料モデルを自動選択する方式にした。
> - **追加ヘッダー設定**：OpenRouter 推奨の `HTTP-Referer` と `X-Title` ヘッダーを追加。

---

### No.22 | B-2-2：AI分類のプロンプトを設計する（45分）

**何をするか：** AIに「どんな指示を出すか」の文面を考えて試す。

**プロンプトの例：**
```
あなたは情報分類アシスタントです。
ユーザーが保存した情報のテキストを受け取り、以下のJSON形式で返してください。

{
  "title": "20文字以内の簡潔なタイトル",
  "category": "カテゴリ名"
}

ルール:
- タイトルは内容を端的に表す日本語にすること
- 以下の既存カテゴリに合うものがあれば、そのカテゴリ名をそのまま使うこと:
  [既存カテゴリ一覧をここに入れる]
- 合うカテゴリがなければ、新しいカテゴリ名を作ること
- カテゴリ名は短く（8文字以内）、ひらがな・カタカナ・漢字で
- JSON以外の文字は出力しないこと
```

**テストケース（少なくとも5つは試す）：**
- 「駅前のピアノ教室、月曜16時から体験レッスンあり」→ 期待：習い事系
- 「楽天スーパーセール、ポイント10倍は22日まで」→ 期待：セール・買い物系
- 「鶏むね肉 500g、醤油大さじ2、みりん大さじ1」→ 期待：レシピ系
- 「Aさんにメール返信する。内容は来週の打ち合わせ日程」→ 期待：返信・連絡系
- 「https://example.com の記事が参考になった」→ 期待：記事・参考系

**完了チェック：**
- [✅] プロンプトのテンプレートが完成した
- [✅] 5つ以上のテストケースでそれなりの結果が出た

> **📝 実装変更メモ（B-2-2）**
> - **プロンプトを `BASE_PROMPT` テンプレートとして分離**：関数内にインラインで書くのではなく、モジュール先頭に `BASE_PROMPT` 変数として定義し、`build_prompt()` ヘルパー関数で組み立てる方式に変更。保守性が向上。
> - **プロンプト内容の充実**：ガイドの例よりも詳細なルールを追加。
>   - 「出力はJSONのみとし、コードブロック記号は一切書かないこと」を明記
>   - title の具体例（「ピアノ教室の体験レッスン情報」等）を追加
>   - category の具体例（「習い事」「買い物候補」等）を追加
>   - 「曖昧な場合はユーザーが後で行動したい軸に近いカテゴリを選ぶ」ルールを追加

---

### No.23 | B-2-3：AIを呼び出す共通関数を作成する（45分）

**何をするか：** `ai_classifier.py` というファイルを作り、AI分類を呼び出す関数を作る。

**作成するファイル：** `ai_classifier.py`

```python
import os
import json
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def classify_text(text, existing_categories):
    """
    テキストをAIに送ってタイトルとカテゴリを返してもらう。

    引数:
        text: 分類したいテキスト
        existing_categories: そのユーザーの既存カテゴリ名のリスト（例: ["レシピ", "習い事"]）
    戻り値:
        {"title": "...", "category": "..."} の辞書
    """
    categories_str = "、".join(existing_categories) if existing_categories else "なし"

    prompt = f"""あなたは情報分類アシスタントです。
以下のテキストの内容を分析し、JSONで返してください。

テキスト:
{text}

既存カテゴリ一覧: {categories_str}

以下のJSON形式で返してください（JSON以外は出力しないでください）:
{{"title": "20文字以内の簡潔なタイトル", "category": "カテゴリ名"}}

ルール:
- 既存カテゴリに合うものがあればそのまま使う
- なければ新しいカテゴリ名を作る（8文字以内）
- 日本語で返すこと"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3-235b-a22b:free",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # JSONをパース（AIが余計な文字を出すことがあるので対策）
        # ```json ... ``` で囲まれている場合に対応
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        parsed = json.loads(content.strip())
        return {
            "title": parsed.get("title", text[:30]),
            "category": parsed.get("category", "未分類")
        }

    except Exception as e:
        print(f"AI分類エラー: {e}")
        # エラー時はフォールバック
        return {
            "title": text[:30] if len(text) > 30 else text,
            "category": "未分類"
        }
```

**完了チェック：**
- [✅] `ai_classifier.py` が作成されている
- [✅] `classify_text("駅前のピアノ教室", ["レシピ"])` を呼んで結果が返る

> **📝 実装変更メモ（B-2-3）**
> - **`dotenv` 対応追加**：`from dotenv import load_dotenv` + `load_dotenv()` でローカル開発時に `.env` ファイルから環境変数を読み込めるようにした。
> - **API キー存在チェック追加**：`OPENROUTER_API_KEY` が未設定の場合、`RuntimeError` を発生させて開発中に即座に気づけるようにした。
> - **`openrouter/free` モデルに変更**：ガイドの `qwen/qwen3-235b-a22b:free` ではなく `openrouter/free` を使用。
> - **マークダウンコードブロック解析の改善**：`max(part, key=len)` でコードブロック内のJSON候補を特定する方式に変更（ガイドの `split("```")[1]` より堅牢）。
> - **戻り値のフォールバック改善**：`parsed.get("title") or text[:30]` のように `or` を使用（`None` と空文字両方に対応）。
> - **単体テスト用コード追加**：`if __name__ == "__main__":` で3つのテストケースを実行できるようにした。

---

### No.24 | B-2-4：LINE Bot テキスト受信→AI分類→DB保存フロー（60分）

**何をするか：** LINEでテキストを送ったら、AIが分類してデータベースに保存されるようにする。

**app.py のメッセージハンドラを修正：**

```python
from ai_classifier import classify_text
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # ① そのユーザーの既存カテゴリ一覧を取得
    cats = supabase_admin.table("categories") \
        .select("id, name") \
        .eq("line_user_id", user_id) \
        .execute()
    existing = {c["name"]: c["id"] for c in cats.data}
    category_names = list(existing.keys())

    # ② AI分類
    result = classify_text(text, category_names)
    title = result["title"]
    category_name = result["category"]

    # ③ カテゴリがなければ新規作成
    if category_name in existing:
        category_id = existing[category_name]
    else:
        new_cat = supabase_admin.table("categories") \
            .insert({"line_user_id": user_id, "name": category_name}) \
            .execute()
        category_id = new_cat.data[0]["id"]

    # ④ items テーブルに保存
    tomorrow_9pm = (datetime.now(JST) + timedelta(days=1)).replace(
        hour=21, minute=0, second=0, microsecond=0
    )
    supabase_admin.table("items").insert({
        "line_user_id": user_id,
        "type": "text",
        "title": title,
        "description": text,
        "category_id": category_id,
        "status": "pending",
        "next_notify_at": tomorrow_9pm.isoformat(),
        "notify_count": 0
    }).execute()

    # ⑤ LINEに返信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"📝 {category_name} に保存しました！")]
            )
        )
```

**テスト手順：**
1. GitHubにプッシュ → Renderがデプロイ
2. LINEで「駅前のピアノ教室、月曜16時から体験レッスンあり」を送る
3. Botから「📝 〇〇 に保存しました！」が返ってくる
4. Supabase Table Editor → items テーブルにデータが入っていることを確認

**完了チェック：**
- [✅] テキストを送るとAI分類されてDBに保存される
- [✅] カテゴリも自動で作成される

> **📝 実装変更メモ（B-2-4）**
> - **エラーハンドリング強化**：ガイドでは B-4-4 で一括対応する予定だったが、B-2-4 の時点で try-except を組み込み済み。AI/DB失敗時はデフォルトの「メッセージを受信しました」返信にフォールバック。LINE返信部分も別の try-except で囲み、返信失敗でもアプリが落ちないようにした。
> - **Supabase エラーチェック追加**：`getattr(res, "error", None)` で Supabase の応答エラーを明示的にチェック。ガイドにはない実装。
> - **返信メッセージの詳細化**：`📝 {category_name} に保存しました！` → `📝 「{category_name}」に保存しました！\nタイトル: {title}` にタイトルも表示するよう変更。
> - **ロギング追加**：`app.logger.info` / `app.logger.error` で処理の各段階を詳細にログ出力。
> - **`notify_count` 省略**：ガイドでは明示的に `"notify_count": 0` を指定していたが、DB側のデフォルト値（`DEFAULT 0`）に任せる形に変更。
> - **`category_id` の条件付きセット**：カテゴリ作成に失敗した場合 `category_id = None` とし、`item_data` に含めない安全策を追加。

---

### No.25 | B-3-1：LINE Botで画像を受信して取得する処理（30分）

**何をするか：** LINEで送られた画像のデータをダウンロードする処理を作る。

**app.py に画像受信ハンドラを追加：**
```python
from linebot.v3.webhooks import ImageMessageContent

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # LINE APIから画像データをダウンロード
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        # 画像のバイナリデータを取得
        content = line_bot_api.get_message_content(message_id)
        image_data = content  # バイナリデータ

    # TODO: この後 Storage に保存 → AI解析 → DB保存
    print(f"画像受信: ユーザー={user_id}, サイズ={len(image_data)}bytes")
```

**⚠️ 注意：** LINEの画像データは一定時間で期限切れになるので、受信したらすぐにダウンロードして保存すること。

**完了チェック：**
- [✅] LINEで画像を送ったらRenderのログに画像サイズが表示される

> **📝 実装変更メモ（B-3-1）**
> - ガイドのサンプルコードでは `MessagingApi` で `get_message_content` していたが、実装では **`MessagingApiBlob`** を使用（SDK v3 の正しい方式）。ガイドの B-3-4 完成版コードが最初から適用された。

---

### No.26 | B-3-2：画像をSupabase Storageにアップロード（30分）

**何をするか：** 受信した画像をクラウドに保存する処理を作る。

**作成するファイル：** `storage_handler.py`

```python
import os
from supabase import create_client

supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

def upload_image(line_user_id, item_id, image_data):
    """
    画像をSupabase Storageにアップロードして、公開URLを返す。
    """
    file_path = f"{line_user_id}/{item_id}.png"

    supabase_admin.storage.from_("screenshots").upload(
        path=file_path,
        file=image_data,
        file_options={"content-type": "image/png"}
    )

    # 公開URLを取得
    url = supabase_admin.storage.from_("screenshots").get_public_url(file_path)
    return url
```

**完了チェック：**
- [✅] テスト画像をアップロードしてURLが返ってくる

> **📝 実装変更メモ（B-3-2）**
> - **Render の SDK バージョン対応**（コミット `f210f4f`）：`storage3 2.28.0` の引数名に合わせ、`upload()` の引数を `path=` / `file=` に変更。
> - **`upsert` オプション追加**：`file_options` に `"upsert": "true"` を追加。同名ファイルが存在する場合に上書きするようにした。
> - **公開URL取得のバージョン差異対策**：`get_public_url()` の戻り値が `dict` 型の場合に `.get("publicUrl")` で取得するガード処理を追加。

---

### No.27 | B-3-3：マルチモーダルLLMで画像を解析する処理（60分）

**何をするか：** AIに画像を直接送って、内容を読み取ってもらう処理を作る。

**ai_classifier.py に関数を追加：**

```python
import base64

def classify_image(image_data, existing_categories):
    """
    画像をAIに送ってタイトルとカテゴリを返してもらう。
    """
    categories_str = "、".join(existing_categories) if existing_categories else "なし"
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    prompt = f"""この画像の内容を読み取り、以下のJSON形式で返してください。
JSON以外は出力しないでください。

{{"title": "20文字以内の簡潔なタイトル", "category": "カテゴリ名"}}

既存カテゴリ: {categories_str}
既存カテゴリに合うものがあればそのまま使い、なければ新規作成してください。"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen-2.5-vl-72b-instruct:free",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }},
                        {"type": "text", "text": prompt}
                    ]
                }]
            },
            timeout=60
        )
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        parsed = json.loads(content.strip())
        return {
            "title": parsed.get("title", "画像メモ"),
            "category": parsed.get("category", "未分類")
        }

    except Exception as e:
        print(f"画像解析エラー: {e}")
        return {"title": "画像メモ", "category": "未分類"}
```

**⚠️ 重要：** 無料モデルの日本語スクショ解析精度はここで実際に確認する。うまくいかない場合はモデル名を変えて試す。

**完了チェック：**
- [✅] スクショ画像を渡してタイトルとカテゴリが返ってくる
- [✅] 日本語のスクショでもそれなりに正しい結果が出る

> **📝 実装変更メモ（B-3-3）**
> - **画像分類モデルを変更**：当初予定の `qwen/qwen-2.5-vl-72b-instruct:free` → **`google/gemma-3-27b-it:free`**（Google Gemma 3）に変更。無料のマルチモーダルモデルとして精度・安定性を検証した結果。
> - **API リクエスト形式**：OpenAI 互換の `"type": "text"` + `"type": "image_url"` 形式を使用（ガイドのコードとほぼ同じだが、テキストを先・画像を後の順序に変更）。
> - **API ステータスコードチェック追加**：`response.status_code != 200` の場合にフォールバック値を返すガード処理を追加。
> - **マークダウンコードブロック解析の改善**：テキスト分類と同じ `max(part, key=len)` 方式に統一。ガイドの `split("```")[1]` より堅牢。
> - **`timeout=60` を明示指定**：画像解析は時間がかかるため、テキスト分類（30秒）より長い60秒タイムアウトを設定。

---

### No.28 | B-3-4：画像受信→Storage→AI解析→DB保存フロー結合（45分）

**何をするか：** No.25〜27で作った処理をすべてつなげる。

**app.py の画像ハンドラを完成版に修正：**

```python
import uuid
from ai_classifier import classify_text, classify_image
from storage_handler import upload_image

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # ① 画像をダウンロード
    with ApiClient(configuration) as api_client:
        blob_api = MessagingApiBlob(api_client)
        image_data = blob_api.get_message_content(message_id)

    # ② item_id を先に生成
    item_id = str(uuid.uuid4())

    # ③ Supabase Storage にアップロード
    image_url = upload_image(user_id, item_id, image_data)

    # ④ 既存カテゴリ取得
    cats = supabase_admin.table("categories") \
        .select("id, name").eq("line_user_id", user_id).execute()
    existing = {c["name"]: c["id"] for c in cats.data}

    # ⑤ AI画像解析
    result = classify_image(image_data, list(existing.keys()))

    # ⑥ カテゴリ処理（テキストと同じロジック）
    category_name = result["category"]
    if category_name in existing:
        category_id = existing[category_name]
    else:
        new_cat = supabase_admin.table("categories") \
            .insert({"line_user_id": user_id, "name": category_name}).execute()
        category_id = new_cat.data[0]["id"]

    # ⑦ DB保存
    tomorrow_9pm = (datetime.now(JST) + timedelta(days=1)).replace(
        hour=21, minute=0, second=0, microsecond=0
    )
    supabase_admin.table("items").insert({
        "id": item_id,
        "line_user_id": user_id,
        "type": "image",
        "image_url": image_url,
        "title": result["title"],
        "category_id": category_id,
        "status": "pending",
        "next_notify_at": tomorrow_9pm.isoformat(),
        "notify_count": 0
    }).execute()

    # ⑧ 返信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"📷 {category_name} に保存しました！")]
            )
        )
```

**完了チェック：**
- [✅] LINEでスクショを送ると「📷 〇〇 に保存しました！」が返ってくる
- [✅] Supabase の items にデータが入っている
- [✅] Supabase の Storage に画像がアップロードされている

> **📝 実装変更メモ（B-3-4）**
> - **エラーハンドリングの充実**：B-4-4 で予定していた try-except を画像ハンドラに組み込み済み。さらに、画像ダウンロード失敗時は専用メッセージ「画像を取得できませんでした」を返し、それ以外のエラー（Storage・AI・DB）は汎用エラーメッセージを返す2段構成に改善。
> - **デフォルト返信の方式変更**：ガイドではデフォルト返信を「画像を受信しました」としていたが、実装では「⚠️ 保存中にエラーが発生しました」をデフォルトにし、**全処理成功時のみ成功メッセージで上書き**する安全な方式に変更。
> - **返信メッセージの詳細化**：`📷 〇〇 に保存しました！` → `📷 「{category_name}」に保存しました！\nタイトル: {title}` にタイトルも表示。
> - **行動ログ記録の統合**（B-4-5）：画像保存成功後に `log_activity()` を呼び出すよう統合済み。

---
---

## 2/22（日）：バックエンド③ + ★レビュー①

### ✅ この日のゴール
全入力パターン（テキスト・画像・URL）が動く ＋ チームで確認済み。

---

### No.29 | B-4-1：OGP取得の共通関数を作成する（45分）

**何をするか：** URLを受け取ったときに、そのページのタイトル・説明・サムネイルを自動取得する。

**作成するファイル：** `ogp_fetcher.py`

```python
import requests
from bs4 import BeautifulSoup

def fetch_ogp(url):
    """
    URLからOGP情報（タイトル・説明・画像）を取得する。
    取得できない場合はフォールバック値を返す。
    """
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"  # Botブロック回避
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # OGPタグを探す
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")

        title = og_title["content"] if og_title else None
        description = og_desc["content"] if og_desc else None
        image = og_image["content"] if og_image else None

        # OGPがない場合は <title> タグから取得
        if not title:
            title_tag = soup.find("title")
            title = title_tag.string if title_tag else url

        return {
            "title": title or url,
            "description": description or "",
            "image": image
        }

    except Exception as e:
        print(f"OGP取得エラー ({url}): {e}")
        # 取得失敗時はURLのドメイン名をタイトルにする
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return {
            "title": domain or url,
            "description": "",
            "image": None
        }
```

**完了チェック：**
- [✅] 有名なサイト（Yahoo!ニュース等）のURLでOGP情報が取れる
- [✅] 存在しないURLでもエラーにならずフォールバック値が返る

> **📝 実装変更メモ（B-4-1）**
> - **User-Agent の詳細化**：ガイドの `"Mozilla/5.0"` → `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"` に変更。より本物のブラウザに近い文字列にして Bot ブロック回避を強化。
> - **`urlparse` のインポート位置**：ガイドでは `except` ブロック内で `from urllib.parse import urlparse` していたが、モジュール先頭でインポートするように変更（PEP 8 準拠）。
> - **詳細なコメント追加**：各ステップにドキュメント的なコメントを追加し、チームメンバーがコードを読みやすいようにした。

---

### No.30 | B-4-2：URL受信→OGP取得→AI分類→DB保存フロー（60分）

**何をするか：** LINEでURLを送ったときの処理を追加する。

**app.py のテキストハンドラにURL判定を追加：**

```python
import re
from ogp_fetcher import fetch_ogp

def is_url(text):
    """テキストにURLが含まれているか判定"""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group() if match else None

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text

    url = is_url(text)

    if url:
        # ===== URL処理 =====
        ogp = fetch_ogp(url)

        # 既存カテゴリ取得
        cats = supabase_admin.table("categories") \
            .select("id, name").eq("line_user_id", user_id).execute()
        existing = {c["name"]: c["id"] for c in cats.data}

        # OGPのタイトル+説明文でAI分類
        ai_input = f"{ogp['title']}。{ogp['description']}"
        result = classify_text(ai_input, list(existing.keys()))

        # カテゴリ処理
        category_name = result["category"]
        if category_name in existing:
            category_id = existing[category_name]
        else:
            new_cat = supabase_admin.table("categories") \
                .insert({"line_user_id": user_id, "name": category_name}).execute()
            category_id = new_cat.data[0]["id"]

        # DB保存
        tomorrow_9pm = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )
        supabase_admin.table("items").insert({
            "line_user_id": user_id,
            "type": "url",
            "original_url": url,
            "title": result["title"],
            "description": ogp["description"],
            "category_id": category_id,
            "ogp_image": ogp["image"],
            "status": "pending",
            "next_notify_at": tomorrow_9pm.isoformat(),
            "notify_count": 0
        }).execute()

        reply_text = f"🔗 {category_name} に保存しました！"

    else:
        # ===== テキスト処理（No.24 のコードと同じ）=====
        # （省略 — No.24で書いたテキスト処理をここに入れる）
        reply_text = f"📝 {category_name} に保存しました！"

    # 返信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
```

**完了チェック：**
- [✅] LINEでURLを送ると「🔗 〇〇 に保存しました！」が返ってくる
- [✅] items テーブルに original_url と ogp_image が保存されている

> **📝 実装変更メモ（B-4-2）**
> - **実装完了**。`app.py` に `is_url()` 関数と URL 分岐処理を統合済み。
> - **テキストハンドラへの統合方式**：ガイドでは URL 処理とテキスト処理を `if url:` / `else:` で分離する方式だったが、実装ではこれに加えて**カテゴリ取得を共通化**（URL/テキスト判定の前にカテゴリを取得）し、コード重複を削減。
> - **デフォルト返信の安全方式**：ガイドでは成功メッセージをデフォルトにしていたが、実装では「⚠️ 保存中にエラーが発生しました」をデフォルトにし、全処理成功時のみ `🔗` / `📝` メッセージで上書き。
> - **返信メッセージの改善**：`🔗 {category_name} に保存しました！` → `🔗 「{category_name}」に保存しました！\nタイトル: {title}` にタイトルも表示。
> - **行動ログの統合**（B-4-5）：URL保存時は `metadata={"message_type": "url"}` で記録。

---

### No.31 | B-4-3：メッセージ振り分けロジックを整理する（30分）

**何をするか：** テキスト・画像・URL・その他（スタンプ等）の全パターンを整理する。

**振り分けの全体像：**
```
メッセージ受信
├── テキスト
│   ├── URLが含まれている → URL処理（No.30）
│   └── URLがない → テキスト処理（No.24）
├── 画像 → 画像処理（No.28）
└── その他（動画・スタンプ・位置情報等）→ 非対応メッセージを返す
```

**「その他」の場合の処理を追加：**
```python
from linebot.v3.webhooks import (
    StickerMessageContent, VideoMessageContent,
    AudioMessageContent, LocationMessageContent,
    FileMessageContent
)

# 非対応メッセージの共通ハンドラ
for msg_type in [StickerMessageContent, VideoMessageContent,
                 AudioMessageContent, LocationMessageContent,
                 FileMessageContent]:
    @handler.add(MessageEvent, message=msg_type)
    def handle_unsupported(event):
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text="📌 現在は画像・URL・テキストに対応しています。\nスクショやURLを送ってみてください！"
                    )]
                )
            )
```

**完了チェック：**
- [✅] テキスト → AI分類 → 保存される
- [✅] URL → OGP取得 → AI分類 → 保存される
- [✅] 画像 → AI解析 → 保存される
- [✅] スタンプを送ると「現在は画像・URL・テキストに対応しています」が返る

> **📝 実装変更メモ（B-4-3）**
> - **実装完了**。ガイドのコードとほぼ同じ構成で実装。
> - **エラーハンドリング追加**：ガイドにはなかった try-except を非対応メッセージハンドラにも追加。返信失敗時も `app.logger.error` でログ出力してアプリが落ちないようにした。

---

### No.32 | B-4-4：エラーハンドリングを追加する（45分）

**何をするか：** 各処理でエラーが起きたときに、アプリが落ちずにユーザーに適切なメッセージを返すようにする。

**追加するエラーハンドリング：**

| エラーの種類 | 対処方法 |
|------------|---------|
| AI APIエラー | 「未分類」に保存して「分類に一時的な問題が…」と返信 |
| OGP取得失敗 | ドメイン名をタイトルにして保存（fetch_ogp内で対応済み） |
| 画像ダウンロード失敗 | 「画像を取得できませんでした」と返信 |
| DB保存失敗 | 「保存に失敗しました。もう一度お試しください」と返信 |

**実装方法：** 各ハンドラの全体を `try-except` で囲む
```python
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    try:
        # （既存の処理全体）
        pass
    except Exception as e:
        print(f"テキスト処理エラー: {e}")
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text="⚠️ 保存中にエラーが発生しました。\nもう一度お試しください。"
                    )]
                )
            )
```

**完了チェック：**
- [✅] 各ハンドラに try-except が入っている
- [✅] エラーが起きてもアプリ全体が落ちない

> **📝 実装変更メモ（B-4-4）**
> - **実装完了**。ガイドの方針に沿いつつ、より堅牢な実装に改善。
> - **「デフォルトエラー → 成功時に上書き」方式**：ガイドでは try 内で成功メッセージを組み立て → except でエラーメッセージに差し替える方式だったが、実装では逆に**デフォルトをエラーメッセージにし、全処理成功時のみ成功メッセージで上書き**する安全な方式に変更。
> - **画像ダウンロード失敗の専用対応**：ガイドの表にあった「画像を取得できませんでした」を、ネストされた内側の try-except で実装。外側の except では `"画像を取得できませんでした" not in reply_text` で判定し、専用メッセージを保持する工夫。
> - **署名検証エラーの明示対応**：`callback()` 関数で `InvalidSignatureError` を明示的にキャッチし、`400` を返す実装を追加。
> - **非対応メッセージハンドラにも try-except を追加**。

---

### No.33 | B-4-5：user_activity_logsへの記録処理を追加（30分）

**作成するファイル：** `activity_logger.py`

```python
import os
from supabase import create_client

supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

def log_activity(line_user_id, action_type, item_id=None, metadata=None):
    """行動ログを記録する"""
    try:
        data = {
            "line_user_id": line_user_id,
            "action_type": action_type,
        }
        if item_id:
            data["item_id"] = item_id
        if metadata:
            data["metadata"] = metadata

        supabase_admin.table("user_activity_logs").insert(data).execute()
    except Exception as e:
        print(f"ログ記録エラー: {e}")
        # ログ記録失敗はアプリ全体に影響させない
```

**app.py のハンドラ内で呼び出しを追加：**
```python
from activity_logger import log_activity

# テキスト/URL受信時
log_activity(user_id, "bot_message", metadata={"message_type": "text"})

# 画像受信時
log_activity(user_id, "bot_message", metadata={"message_type": "image"})
```

**完了チェック：**
- [✅] メッセージ送信後にuser_activity_logsにレコードが増えている

> **📝 実装変更メモ（B-4-5）**
> - **実装完了**。`activity_logger.py` にガイド通りの `log_activity()` 関数を実装し、`app.py` の各ハンドラから呼び出し済み。
> - **`dotenv` 対応追加**：`activity_logger.py` でも `load_dotenv()` を呼び出し、ローカル開発時に `.env` から環境変数を読み込めるようにした。
> - **呼び出しタイミングの明確化**：テキスト/URL 保存成功後に `metadata={"message_type": "text"}` or `"url"`、画像保存成功後に `metadata={"message_type": "image"}` で記録。try ブロック内の最後（成功時のみ）で呼び出す設計。
> - **詳細なドキュメントコメント追加**：ファイル先頭に役割・使い方・呼び出し元の説明コメントを追加。

---

### No.34〜36 | ★レビュー①（全員で60分）

**No.34 | R①-1：各メンバーが自分のLINEからテスト（30分）**
- 全員がBot友達追加済みであること
- テスト項目：
  - [ ] テキスト「今週末のセール情報メモ」→ 保存される？
  - [ ] スクショ画像 → 保存される？
  - [ ] URL → 保存される？
  - [ ] スタンプ → 「対応していません」メッセージが出る？

**No.35 | R①-2：AI分類の精度を評価する（15分）**
- Supabase Table Editor で items テーブルを確認
- 各アイテムのタイトルとカテゴリが適切かを見る
- 5段階評価（1=的外れ 〜 5=完璧）で記録

**No.36 | R①-3：問題リストを作成する（15分）**
- 見つかった問題を3段階に分類：
  - **致命的**（翌日修正）：データが保存されない、アプリが落ちる等
  - **改善希望**：カテゴリ名が変、タイトルが長すぎる等
  - **将来対応**：「こんな機能もあったら」等

---
---

## 2/23（月）：フロントエンド① — Webアプリの骨格

### ✅ この日のゴール
スマホでLINEログインして、保存済みアイテムがタイル表示される。

---

### 🔄 B-5 方法変更について（改訂版：方法A）

**変更理由：** SupabaseにはLINEプロバイダーが存在しないため、元のタスク（Supabase Auth経由）は実行不可。Flask側で直接LINE Login OAuthを処理する方式に変更する。

**変更の影響まとめ：**

| 項目 | 変更内容 |
|------|---------|
| B-5-1 | Supabase Auth設定 → **不要に**。LINE Loginチャネル作成 + Render環境変数のみ |
| B-5-2 | 変更なし（HTMLそのまま） |
| B-5-3 | Supabase Auth経由 → **Flask側で直接LINE OAuth処理** |
| B-5-4 | 変更なし（ログアウトそのまま） |
| RLSポリシー | 全テーブルのRLS → **不要に**（Flask + service_role_key で制御） |
| usersテーブル | id列が `auth.uid()` → **自動生成UUID**に変更 |
| C-1-3以降 | 変更なし（元から `supabase_admin`（service_role_key）を使う設計だった） |

---

### No.37 | B-5-1：LINE Loginチャネル作成 + 環境変数設定（30分）

**⚠️ LINE Login チャネルは Messaging API チャネルとは別物。新しく作る。**

> **📝 方法変更メモ（改訂版）：** SupabaseにはLINEプロバイダーが存在しないため、Supabase Auth経由の方式から Flask側で直接LINE Login OAuthを処理する方式（方法A）に変更。

**手順：**

**① LINE Loginチャネルを作成する**

1. LINE Developers（https://developers.line.biz）にログイン
2. 既存のプロバイダー「Re:find」を開く
3. 「新規チャネル作成」→ **LINE Login** を選ぶ
4. 設定項目：
   - チャネル名：`Re:find Login`
   - チャネルの説明：`Re:findのWebアプリケーションにLINEアカウントでログインするための認証機能です。`
   - アプリタイプ：**Web app** ✅ にチェック
   - その他：Messaging APIチャネルと同じ内容でOK
5. 作成後、以下をメモ：
   - **Channel ID**（チャネル基本設定に表示される数字）
   - **Channel Secret**（チャネル基本設定の下の方）

**② コールバックURLを設定する**

1. LINE Login チャネルの設定画面を開く
2. 「LINE Login設定」タブを開く
3. 「コールバックURL」に以下を入力：
   ```
   https://re-find.onrender.com/login/callback
   ```
   ※ あなたのRender URLに合わせて変更してください

**③ Renderに環境変数を追加する**

Render ダッシュボード → re-find サービス → Environment タブに以下を追加：

| 変数名 | 値 |
|--------|-----|
| `LINE_LOGIN_CHANNEL_ID` | LINE Login の Channel ID |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login の Channel Secret |
| `FLASK_SECRET_KEY` | ランダムな文字列（※下の説明参照） |

**FLASK_SECRET_KEY の作り方：**
Pythonで以下を実行して出てきた文字列をコピーする：
```python
import secrets
print(secrets.token_hex(32))
```
→ これはセッション（ログイン状態の記憶）を暗号化するための鍵。

**完了チェック：**
- [ ] LINE Login チャネルが作成されている
- [ ] Channel ID と Channel Secret をメモした
- [ ] コールバックURL `https://re-find.onrender.com/login/callback` が設定されている
- [ ] Render に `LINE_LOGIN_CHANNEL_ID` を追加した
- [ ] Render に `LINE_LOGIN_CHANNEL_SECRET` を追加した
- [ ] Render に `FLASK_SECRET_KEY` を追加した

---

### No.38 | B-5-2：ログイン画面のHTMLを作成する（30分）

**作成するファイル：** `templates/login.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Re:find - ログイン</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="text-center">
            <h1 class="mb-4">Re:find</h1>
            <p class="text-muted mb-4">保存した情報を、もう一度見つける</p>
            <a href="/login/line" class="btn btn-success btn-lg px-5 py-3">
                LINEでログイン
            </a>
        </div>
    </div>
</body>
</html>
```

**完了チェック：**
- [ ] ログイン画面がスマホで見やすいレイアウトになっている

---

### No.39 | B-5-3：Flaskにログイン処理を実装する（60分）

**⚠️ ここが一番の変更ポイント。元のタスクとはコードが違う。**
**⚠️ 認証まわりは躓きやすい。うまくいかなくても焦らない。**

**最悪の場合のプランB：** LINE user_id 直接入力で仮実装する（後述）。

**ログインの流れ（図解）：**

```
ユーザー                    Flask                     LINE
  │                         │                         │
  │ ① 「LINEでログイン」押す  │                         │
  │ ──────────────────────→ │                         │
  │                         │ ② LINE認証ページへ転送    │
  │                         │ ──────────────────────→ │
  │                         │                         │
  │ ③ LINEでログイン         │                         │
  │ ──────────────────────────────────────────────→  │
  │                         │                         │
  │                         │ ④ codeを持ってFlaskに戻る │
  │ ←────────────────────── │ ←────────────────────── │
  │                         │                         │
  │                         │ ⑤ codeでアクセストークン取得│
  │                         │ ──────────────────────→ │
  │                         │                         │
  │                         │ ⑥ トークンでプロフィール取得│
  │                         │ ──────────────────────→ │
  │                         │                         │
  │                         │ ⑦ DBに保存 + セッション作成│
  │                         │                         │
  │ ⑧ トップページ表示       │                         │
  │ ←────────────────────── │                         │
```

**実装コード（app.py に追加）：**

```python
import os
import secrets
import requests as http_requests  # Flask の request と名前が被るので別名にする
from flask import Flask, request, abort, session, redirect, url_for, render_template
from supabase import create_client

app = Flask(__name__)

# ============================================================
# セッション設定（ログイン状態をブラウザに覚えさせるための設定）
# ============================================================
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30日間

# ============================================================
# LINE Login の設定（Messaging API とは別のチャネル）
# ============================================================
LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")
LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")
LINE_LOGIN_REDIRECT_URI = os.environ.get(
    "LINE_LOGIN_REDIRECT_URI",
    "https://re-find.onrender.com/login/callback"
)

# ============================================================
# Supabase 管理者クライアント（service_role_key を使用）
# ============================================================
supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================================
# ログイン画面を表示する
# ============================================================
@app.route("/login")
def login_page():
    """ログイン画面を表示する"""
    # すでにログイン済みならトップページへ
    if session.get("line_user_id"):
        return redirect("/")
    return render_template("login.html")


# ============================================================
# 「LINEでログイン」ボタンを押したときの処理
# ============================================================
@app.route("/login/line")
def login_line():
    """LINEの認証ページにリダイレクトする"""

    # CSRF対策のランダム文字列（なりすまし防止）
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    # LINE の認証ページURL を組み立てる
    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={LINE_LOGIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=profile%20openid"  # プロフィール情報とIDを要求
    )

    # LINEの認証ページへ飛ばす
    return redirect(auth_url)


# ============================================================
# LINEで認証した後、戻ってくる先（コールバック）
# ============================================================
@app.route("/login/callback")
def login_callback():
    """LINEからのコールバックを処理する"""

    # --- エラーチェック ---

    # LINE側でエラーが発生した場合
    error = request.args.get("error")
    if error:
        print(f"LINE認証エラー: {error}")
        return redirect("/login")

    # CSRF対策チェック（送ったstateと返ってきたstateが一致するか）
    state = request.args.get("state")
    if state != session.get("oauth_state"):
        print("stateが一致しません（CSRF攻撃の可能性）")
        return redirect("/login")

    # 認証コードを取得
    code = request.args.get("code")
    if not code:
        print("認証コードがありません")
        return redirect("/login")

    # --- ⑤ 認証コードをアクセストークンに交換する ---

    token_response = http_requests.post(
        "https://api.line.me/oauth2/v2.1/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINE_LOGIN_REDIRECT_URI,
            "client_id": LINE_LOGIN_CHANNEL_ID,
            "client_secret": LINE_LOGIN_CHANNEL_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        print(f"トークン取得失敗: {token_response.text}")
        return redirect("/login")

    access_token = token_response.json().get("access_token")

    # --- ⑥ アクセストークンでユーザーのプロフィールを取得する ---

    profile_response = http_requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if profile_response.status_code != 200:
        print(f"プロフィール取得失敗: {profile_response.text}")
        return redirect("/login")

    profile = profile_response.json()
    line_user_id = profile.get("userId")       # 例："U1234abcdef..."
    display_name = profile.get("displayName")  # 例："ちあき"

    print(f"ログイン成功: {display_name} ({line_user_id})")

    # --- ⑦ DBに保存（UPSERT：あれば更新、なければ作成） ---

    try:
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        # 初回ログイン時のデフォルトデータ作成
        _create_default_data_if_needed(line_user_id)

    except Exception as e:
        print(f"DB保存エラー: {e}")
        # DB保存に失敗してもログインは続行する

    # --- セッションにログイン情報を保存 ---

    session.permanent = True  # 30日間有効にする
    session["line_user_id"] = line_user_id
    session["display_name"] = display_name

    # --- ⑧ トップページへリダイレクト ---
    return redirect("/")


def _create_default_data_if_needed(line_user_id):
    """初回ログイン時にデフォルトのカテゴリ・設定・通知ルールを作成する"""

    # 「未分類」カテゴリがなければ作成
    existing = supabase_admin.table("categories") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .eq("name", "未分類") \
        .execute()

    if not existing.data:
        supabase_admin.table("categories").insert({
            "line_user_id": line_user_id,
            "name": "未分類",
        }).execute()

    # user_settings がなければデフォルト作成
    existing_settings = supabase_admin.table("user_settings") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_settings.data:
        supabase_admin.table("user_settings").insert({
            "line_user_id": line_user_id,
            "notify_time": "21:00",
            "notify_enabled": True,
        }).execute()

    # notification_rules がなければデフォルト作成
    existing_rules = supabase_admin.table("notification_rules") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_rules.data:
        supabase_admin.table("notification_rules").insert({
            "line_user_id": line_user_id,
            "category_id": None,
            "item_id": None,
            "rule_type": "interval",
            "config": {"days": [1, 3, 7, 14, 30, 60]},
            "is_active": True,
            "priority": 10,
        }).execute()
```

**⚠️ /callback のURL衝突に注意！**

元の `app.py` には LINE Bot Webhook 用の `/callback` ルートがすでにある。
LINE Login のコールバックは `/login/callback` なので **衝突しない**。

```
/callback         ← LINE Bot（Messaging API）のWebhook受信用。そのまま残す
/login/callback   ← LINE Login のコールバック用。今回新しく追加
```

**完了チェック：**
- [ ] `/login` にアクセスするとログイン画面が表示される
- [ ] 「LINEでログイン」を押すとLINEの認証画面に飛ぶ
- [ ] LINEで認証後、トップページに戻ってくる
- [ ] Supabase の users テーブルにレコードが作成されている
- [ ] Supabase の categories テーブルに「未分類」が作成されている

---

### No.40 | B-5-4：ログアウト処理を実装する（15分）

```python
@app.route("/logout")
def logout():
    # セッションをクリア
    session.clear()
    return redirect("/login")
```

**完了チェック：**
- [ ] ログアウトボタンを押すとログイン画面に戻る
- [ ] ログアウト後にトップページにアクセスするとログイン画面にリダイレクトされる

---

### 追加変更①：usersテーブルの修正

> **📝 方法A対応：** Supabase Auth を使わないため、`id` を `auth.uid()` ではなく自動生成UUIDに変更。

**元の設計：**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,  -- ← Supabase Auth の auth.uid()
    line_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**方法A用に変更：**
```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,  -- ← 自動生成に変更
    line_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

変更点は1行だけ：`id` に `DEFAULT gen_random_uuid()` を追加。

**⚠️ すでにテーブルを作成済みの場合：**
Supabase管理画面 → SQL Editor で以下を実行：
```sql
ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid();
```

---

### 追加変更②：RLSポリシーについて

**方法Aでは、全テーブルのRLSポリシーは設定不要。**

元の設計では `auth.uid()` を使ってRLSで制御していたが、方法Aでは Supabase Auth を使わないため `auth.uid()` が存在しない。
代わりに、全てのDBアクセスを `service_role_key`（管理者権限）で行い、Flask側で `session["line_user_id"]` を使ってユーザーを判別する。

```
元の設計：
  ブラウザ → Supabase（RLSが自動でフィルタ）

方法A：
  ブラウザ → Flask（line_user_idでフィルタ）→ Supabase（管理者権限でアクセス）
```

**すでにRLSを有効化している場合：**
そのままでOK。`service_role_key` はRLSをバイパスするので影響なし。

---

### 追加変更③：ヘルパー関数（他のルートで使う）

B-5-3のコードと一緒に、以下のヘルパー関数も追加しておくと便利：

```python
def get_current_user_line_id():
    """現在ログイン中のユーザーの line_user_id を返す。未ログインなら None"""
    return session.get("line_user_id")

def login_required(f):
    """ログインしていないユーザーをログイン画面にリダイレクトするデコレータ"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("line_user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
```

使い方：
```python
@app.route("/")
@login_required
def index():
    line_user_id = get_current_user_line_id()
    # ... 一覧データ取得 ...
```

---

### 最悪のプランB：LINE user_id 直接入力で仮実装

もしLINE Login の設定がうまくいかない場合、開発を止めないために以下の仮実装を使う：

```python
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        # フォームから line_user_id を手入力して仮ログイン
        line_user_id = request.form.get("line_user_id")
        if line_user_id:
            session.permanent = True
            session["line_user_id"] = line_user_id
            session["display_name"] = "テストユーザー"
            return redirect("/")
    return render_template("login.html")
```

これで LINE Bot 側で表示される user_id をコピペして仮ログインできる。
**本番リリース前に必ずLINE Login に切り替えること。**

---

### No.41〜44 | C-1：Web一覧表示＋カテゴリフィルタ

**No.41 | C-1-1 + No.42 | C-1-2：一覧画面のHTML＋CSS（計90分）**

`templates/index.html` にタイル表示の一覧画面を作る。Bootstrapのカードコンポーネントと CSS Grid を使う。

**No.43 | C-1-3：Flaskから一覧データを取得（45分）**

```python
@app.route("/")
def index():
    # ログインチェック
    user_id = get_current_user_line_id()  # セッションから取得
    if not user_id:
        return redirect("/login")

    # カテゴリ取得
    categories = supabase_admin.table("categories") \
        .select("*").eq("line_user_id", user_id).execute()

    # アイテム取得（⚠️ deleted_at IS NULL を忘れずに！）
    items = supabase_admin.table("items") \
        .select("*, categories(name)") \
        .eq("line_user_id", user_id) \
        .is_("deleted_at", "null") \
        .order("created_at", desc=True) \
        .execute()

    return render_template("index.html",
        categories=categories.data,
        items=items.data
    )
```

**No.44 | C-1-4：カテゴリフィルタのJavaScript（30分）**

JavaScriptでカテゴリタブをクリック → そのカテゴリのカードだけ表示するフィルタリング。

**完了チェック：**
- [ ] スマホでLINEログインして一覧が表示される
- [ ] カテゴリタブで絞り込みができる
- [ ] LINEで送ったアイテムが一覧に表示されている

---

### 【余裕があれば】LIFF導入によるLINEアプリ内シームレスログイン（1〜1.5時間）

**これは何か：** B-5-3（セッション永続化）＋ C-5（外部ブラウザ）で基本的なログイン体験は確保できるが、LIFF（LINE Front-end Framework）を導入すれば、LINEアプリ内でもログインボタンなしで一覧表示が可能になる。2/23の作業が予定より早く終わった場合にのみ着手する。

**ユーザー体験の違い：**
```
セッション永続化＋外部ブラウザ（必須対応）：
  通知タップ → 外部ブラウザ起動（1〜2秒）→ 一覧表示（セッション有効時）
  初回のみ：LINEログインボタン1タップが必要

LIFF導入（余裕があれば）：
  通知タップ → LINEアプリ内でそのまま一覧表示（ログイン操作一切不要）
```

**必要な作業：**

**① LINE DevelopersでLIFFアプリを作成（15分）**
- LINE Developers → 既存のプロバイダー → LINE Login チャネル → LIFF タブ
- 「追加」をクリック
- サイズ：Full（画面全体）
- エンドポイントURL：`https://re-find.onrender.com/liff`
- 作成後、**LIFF ID** をメモ（例：`1234567890-AbCdEfGh`）

**② Flask側にLIFF用ルートを追加（45〜60分）**
```python
@app.route("/liff")
def liff_entry():
    """LINEアプリ内から開いた場合のエントリポイント"""
    return render_template("liff.html", liff_id="ここにLIFF IDを設定")

@app.route("/api/liff-login", methods=["POST"])
def liff_login():
    """LIFFから受け取ったユーザー情報でセッションを発行"""
    data = request.json
    line_user_id = data.get("userId")
    display_name = data.get("displayName")

    if not line_user_id:
        return {"error": "userId is required"}, 400

    # セッション発行（通常のログインと同じ状態にする）
    session.permanent = True
    session["line_user_id"] = line_user_id

    return {"ok": True}
```

**③ LIFF用HTMLを作成（30分）**
```html
<!-- templates/liff.html -->
<script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
<script>
    liff.init({ liffId: "{{ liff_id }}" }).then(() => {
        if (!liff.isLoggedIn()) {
            liff.login();
            return;
        }
        // LINEのプロフィール情報を取得
        liff.getProfile().then(profile => {
            // Flaskにユーザー情報を送ってセッション発行
            fetch("/api/liff-login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    userId: profile.userId,
                    displayName: profile.displayName
                })
            }).then(() => {
                // セッション発行完了 → 一覧画面へ
                window.location.href = "/";
            });
        });
    });
</script>
```

**④ 通知URLをLIFF形式に変更（notify.py内）**
```python
# LIFF導入後の通知URL
# LINEアプリ内で開く場合 → LIFF経由（自動ログイン）
liff_url = "https://liff.line.me/ここにLIFF ID"

# 外部ブラウザで開く場合 → 従来通り（セッション永続化）
browser_url = "https://re-find.onrender.com/?openExternalBrowser=1"
```

**⚠️ 注意点：**
- LIFF SDKの `liff.init()` は非同期処理。完了を待ってから `getProfile()` を呼ぶこと
- LIFFはLINEアプリ内でのみ動作する。外部ブラウザからアクセスした場合は通常のログインフローにフォールバックさせる
- セキュリティ：LIFF経由で受け取った `userId` が本物かどうか、本番運用では検証が必要（Phase 1ではスコープ外）

**判断基準：** 2/23の15時時点でB-5とC-1が両方完了していれば着手してOK。そうでなければ見送り。

**完了チェック：**
- [ ] LIFFアプリがLINE Developersで作成されている
- [ ] 通知リンク → LINEアプリ内 → ログイン操作なしで一覧表示される
- [ ] 外部ブラウザからアクセスした場合も正常に動作する

---
---

## 2/24（火）：フロントエンド② — 編集・カテゴリ管理

### ✅ この日のゴール
Webアプリ上でアイテムの編集・カテゴリ管理がすべてできる。

### No.45〜49 | C-2：編集モーダル

カードをタップ → モーダル表示 → カテゴリ変更・メモ追加・対応済み・削除ができるようにする。

**各ボタンのFlask APIエンドポイント例：**

```python
# 保存（カテゴリ変更・メモ追加）
@app.route("/api/items/<item_id>", methods=["POST"])
def update_item(item_id):
    data = request.json
    supabase_admin.table("items") \
        .update(data) \
        .eq("id", item_id) \
        .execute()
    return {"ok": True}

# 対応済み
@app.route("/api/items/<item_id>/done", methods=["POST"])
def mark_done(item_id):
    supabase_admin.table("items") \
        .update({"status": "done"}) \
        .eq("id", item_id) \
        .execute()
    return {"ok": True}

# 削除（ソフトデリート）
@app.route("/api/items/<item_id>/delete", methods=["POST"])
def delete_item(item_id):
    supabase_admin.table("items") \
        .update({"deleted_at": datetime.now(JST).isoformat()}) \
        .eq("id", item_id) \
        .execute()
    return {"ok": True}
```

### No.50〜53 | C-3：カテゴリ管理

カテゴリの名前変更・削除・新規作成ページ。削除時は「未分類」への付け替え処理を忘れずに。

**完了チェック：**
- [ ] モーダルでカテゴリ変更ができる
- [ ] メモを追加して保存できる
- [ ] 「対応済み」にできる
- [ ] 削除ができる（削除後に一覧から消える）
- [ ] カテゴリの名前変更・削除・新規作成ができる

---
---

## 2/25（水）：フロントエンド③ + 通知

### ✅ この日のゴール
Phase 1の全機能が動く状態。

### No.54〜56 | C-4：共有リンク

Flask側で `/share/<token>` のルートを作り、service_role_key でRLSバイパスしてアイテムを表示。

### No.57〜59 | C-5：通知機能

`notify.py` を作成し、Render Cron Job で毎日21時（UTC 12:00）に実行。

**通知ロジック：**
```
next_notify_at が現在時刻を過ぎている
AND status = 'pending'
AND deleted_at IS NULL
→ ユーザーごとにまとめて1通LINE送信
→ notify_count +1、次の通知日時を計算
```

**通知間隔：** 1日後 → 3日後 → 7日後 → 14日後 → 30日後 → 60日後 → archived

**間隔の根拠：** エビングハウスの忘却曲線とSuperMemoの最適間隔を参考に、通知疲れを考慮して設計。

**⚠️ 重要：通知内のWebアプリURLは外部ブラウザで開くようにする**

LINEのアプリ内ブラウザはCookieの扱いが不安定で、B-5-3で設定したセッション永続化が効かない場合がある。通知メッセージ内のURLに `?openExternalBrowser=1` を付けることで、端末のデフォルトブラウザ（Safari/Chrome）で開くようにする。

```python
# 通知メッセージ内のURL生成時
# ❌ NG：LINEアプリ内ブラウザで開く → セッションが切れる可能性あり
web_url = "https://re-find.onrender.com/"

# ✅ OK：外部ブラウザ（Safari/Chrome）で開く → セッションが安定
web_url = "https://re-find.onrender.com/?openExternalBrowser=1"
```

**なぜ必要か：**
- LINEアプリ内ブラウザではCookieが保持されず、毎回ログインが求められる場合がある
- 外部ブラウザなら B-5-3 で設定したセッション永続化（30日間）が効く
- ユーザーは通知をタップ → すぐに一覧を確認できる（初回ログイン以降は不要）
- トレードオフ：LINEアプリから外部ブラウザに切り替わるため一瞬もたつくが、毎回ログインより遥かにマシ

**最終通知（6通目）：** 経過日数と通知回数を明示し、「これが最後の通知です」と伝える。「未対応に戻す」導線も提示。
```
📌 最後のお知らせです
🎹 ピアノ教室の情報
この情報は 60日前 に保存され、これまでに 6回 お知らせしました。
今回が最後の通知です。
まだ気になるなら、Webアプリで「未対応」に戻せます。
[Webアプリで確認する]   ← ※ URLには ?openExternalBrowser=1 を付与
```

**完了チェック：**
- [ ] 共有リンクが発行できる
- [ ] 共有リンクをログインなしで開ける
- [ ] notify.py を手動実行してLINE通知が届く
- [ ] 最終通知メッセージ（経過日数・通知回数表示）が正しく届く
- [ ] Cron Job が設定されている
- [ ] 通知内のURLに `?openExternalBrowser=1` が付いている
- [ ] 通知リンクタップ → 外部ブラウザで開く → ログインなしで一覧表示（セッション維持時）

---
---

## 2/26（木）：結合テスト + ★レビュー②

### No.60〜65 | テスト＋レビュー＋修正

**通しテストの4シナリオ：**
1. LINE でスクショ送信 → AI分類 → Web一覧に表示 → 通知 → 対応済み
2. LINE で URL 送信 → OGP取得 → AI分類 → カテゴリ変更 → 共有リンク発行
3. LINE でテキスト送信 → AI分類 → メモ追加 → 削除
4. カテゴリ管理（新規作成 → 名前変更 → 削除）

**多人数テスト：** チーム3人が別アカウントでログイン → 他の人のデータが見えないことを確認

---
---

## 2/27（金）：発表

### No.66〜69 | デモ準備＋発表

- デモ用データを投入（各カテゴリ3〜5件）
- **デモ前にRenderにアクセスしてウォームアップ**（スリープ対策）
- 万が一の画面キャプチャを用意

---

## 環境変数チェックリスト（Renderに設定するもの）

| 変数名 | 入手場所 | 設定タイミング |
|--------|---------|-------------|
| LINE_CHANNEL_SECRET | LINE Developers → Messaging API | No.10 |
| LINE_CHANNEL_ACCESS_TOKEN | LINE Developers → Messaging API | No.10 |
| SUPABASE_URL | Supabase → Settings → API | No.20 |
| SUPABASE_KEY | Supabase → Settings → API（anon key） | No.20 |
| SUPABASE_SERVICE_ROLE_KEY | Supabase → Settings → API（service_role） | No.20 |
| OPENROUTER_API_KEY | OpenRouter → Keys | No.21 |
| LINE_LOGIN_CHANNEL_ID | LINE Developers → LINE Login チャネル | No.37（B-5-1） |
| LINE_LOGIN_CHANNEL_SECRET | LINE Developers → LINE Login チャネル | No.37（B-5-1） |

> **📝 変更メモ**：`.env.example` に `LINE_LOGIN_CHANNEL_ID` と `LINE_LOGIN_CHANNEL_SECRET` を先行追加済み（B-5 の準備として）。

---
---

## 実装変更サマリー（B-4 全タスク完了時点）

> このセクションは、実装中に当初計画から変更になった点の一覧です。
> B-4-1 〜 B-4-5 すべて実装完了済み。

### AIモデルの変更

| 用途 | 当初予定（ガイド記載） | 実際の実装 | 変更理由 |
|------|---------|-----------|------|
| テキスト分類 | `qwen/qwen3-235b-a22b:free` | **`openrouter/free`** | 特定モデルに依存せず、利用可能な無料モデルを自動選択する方式に。安定性・可用性が向上 |
| 画像分類 | `qwen/qwen-2.5-vl-72b-instruct:free` | **`google/gemma-3-27b-it:free`** | Google Gemma 3 の方が無料マルチモーダルモデルとして精度・安定性が高いと判断 |

### 画像 API リクエスト形式の変更

| 項目 | 当初予定（ガイド記載） | 実際の実装 |
|------|---------|-----------|
| テキスト部分 | `"type": "text"` | `"type": "text"`（変更なし） |
| 画像部分 | `"type": "image_url"` | `"type": "image_url"`（変更なし） |
| 要素の順序 | 画像 → テキスト | **テキスト → 画像**（テキスト指示を先に読ませる） |
| JSON出力強制 | なし | なし（マークダウンコードブロック解析で対応） |

### エラーハンドリング方式の改善

| 項目 | 当初予定（ガイド記載） | 実際の実装 |
|------|---------|-----------|
| 実装タイミング | B-4-4 で一括対応 | **各機能実装時に並行して組み込み** |
| デフォルト返信 | 成功メッセージ → エラー時に差し替え | **エラーメッセージをデフォルト → 成功時に上書き**（より安全） |
| 画像DL失敗 | 汎用エラーメッセージ | **専用メッセージ**（ネスト try-except で分離） |

### 全体的な改善点（ガイドにない追加実装）

| 改善項目 | 内容 |
|---------|------|
| `python-dotenv` 対応 | ローカル開発時に `.env` から環境変数を読み込み。`ai_classifier.py`、`app.py`、`activity_logger.py` で `load_dotenv()` を呼び出し |
| 環境変数の起動時チェック | `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` / `LINE_CHANNEL_*` / `OPENROUTER_API_KEY` が未設定の場合、起動時に `RuntimeError` で停止 |
| ロギング強化 | `app.logger.info` / `app.logger.error` を使用した詳細ログ出力（Render のログで確認可能） |
| LINE返信メッセージの改善 | `📝 〇〇 に保存しました！` → `📝 「〇〇」に保存しました！\nタイトル: ○○` タイトル情報も表示 |
| LINE SDK 署名検証 | `InvalidSignatureError` の明示的なキャッチと `400` レスポンス返却 |
| Storage SDK 互換性対応 | `storage3 2.28.0` の引数名変更に対応、`get_public_url()` の戻り値型チェック追加 |
| Supabase エラーチェック | `getattr(res, "error", None)` による応答エラー検出を各DB操作に追加 |
| API ステータスコードチェック | テキスト・画像両方の AI API 呼び出しで `status_code != 200` をチェックしフォールバック |
| コードブロック解析の統一 | テキスト・画像分類の両方で `max(part, key=len)` 方式に統一（堅牢性向上） |
