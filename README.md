# Re:find — 情報再発見サービス

> 「あとで見よう」が、もう一度あなたの目の前に現れる。

---

## Re:find が解決する問題

気になる情報を見つけたとき、人は「あとで見よう」と保存します。
しかし保存した情報は、大量のスクショや読まれないブックマークに埋もれ、
気づけば同じ情報を何度も検索し直しています。

Re:find が扱うのは、**「重要だけど緊急ではない」情報**です。

- 子どもの習い事の候補（調べたけど申し込みまでいかない）
- あとで読もうと思った記事（保存したけど結局読まない）
- 買い物の候補（見つけたけど購入判断を先延ばしにしている）

緊急なものはその場で対処できます。重要でないものは忘れても困りません。
問題は **「重要なのに緊急じゃないから、ずっと後回しにされ続ける」こと**。

---

## Re:find の考え方

```
情報を見つける → 保存する → 埋もれる → 再発見する → やるか決める → 行動する
                              ↑                        ↑
                          ここが問題             ここから先は本人が決める

                ├────── Re:find の守備範囲 ─────┤
                保存 → 埋もれさせない → 再発見
```

Re:find は「行動させる」ことを約束しません。
Re:find の役割は、**忘れていた選択肢を、もう一度テーブルに戻すこと**です。
行動するかどうかは、あなたが決めます。

> **プロダクト名「Re:find」は「再び見つける」という意味です。**
> 行動ではなく、再発見にフォーカスしています。

---

## 主な機能

| 機能 | 説明 |
|------|------|
| LINE Bot 入力 | テキスト・URL・画像を LINE に送るだけで保存。アプリを開く必要なし |
| AI 自動分類 | 送られた内容を AI が理解し、タイトルとカテゴリを自動で付ける |
| OGP 自動取得 | URL を送ると、タイトル・説明・サムネイルを自動取得 |
| 画像解析 | スクショを送ると、AI がテキストを読み取って分類（OCR不要） |
| 忘却曲線リマインド | 1→3→7→14→30→60 日の間隔で LINE 通知（計 6 回）。カテゴリ名・経過日数付き |
| Web UI | カテゴリタブ付きのカード表示。保存した情報を一覧で確認 |
| カテゴリ管理 | AI が自動生成したカテゴリを、手動で修正・追加・削除できる |
| アイテム編集 | タイトル・カテゴリ・メモの編集、ステータス変更 |
| 共有リンク | アイテムごとに公開 URL を発行して他の人と共有（ログイン不要で閲覧可能） |
| LINE ログイン | OAuth 2.0 による認証で複数ユーザー対応 |

### なぜ LINE Bot で入力するのか

**入力の手軽さが、このサービスの命です。**

アプリを開いてログインして……という手間があると、「めんどくさいから後で」になります。
気になった瞬間にすでに開いている LINE に送るだけ、というゼロ摩擦の入力が、
Re:find の核心的な価値を支えています。

---

## リマインドの設計（忘却曲線ベース）

エビングハウスの忘却曲線と SuperMemo の最適間隔を参考に、
**通知疲れが起きない間隔**で設計しています。

```
保存日 ─→ 1日後 ─→ 3日後 ─→ 7日後 ─→ 14日後 ─→ 30日後 ─→ 60日後
          (1回目)   (2回目)   (3回目)   (4回目)    (5回目)    (6回目/最終)
```

- 通知メッセージにはカテゴリ名と通知回数を表示（例: `📁 子どもの習い事｜2回目`）
- 最終通知（6 回目）では経過日数を表示し、「最後のリマインドです」と明示します
- 6 回目の通知後、アイテムは自動で「完了」ステータスに変更されます
- Web アプリから「未対応」に戻すと、通知サイクルが再開します
- `python notify.py --dry-run` で送信せずにメッセージ内容を確認できます

> **通知の技術的制約について**
> LINE Messaging API の無料枠では Push Message（こちらから送る通知）が月 200 件に制限されます。
> そのため通知はまとめ送信（1 メッセージに複数アイテムをまとめる）で件数を節約しています。
> LINE への返信（Reply Message）は無制限のため、Bot との対話は通常通り動作します。

---

## 技術スタック

| レイヤー | 技術 | 備考 |
|----------|------|------|
| バックエンド | Python 3.11 / Flask | Gunicorn で起動 |
| フロントエンド | HTML5 + Bootstrap 5 + Vanilla JS | CDN 利用、ビルド不要 |
| データベース | Supabase (PostgreSQL) | RLS によるユーザー間データ分離 |
| ファイルストレージ | Supabase Storage | 画像保存用（`screenshots/{line_user_id}/{item_id}.png`） |
| AI 分類・画像解析 | OpenRouter API | マルチモーダルモデルで画像を直接処理（OCR不要） |
| メッセージング | LINE Messaging API | Webhook 受信 + Push Message 送信 |
| 認証 | LINE Login (OAuth 2.0) | Flask で直接 OAuth 処理（セッションベース） |
| ホスティング | Render.com | GitHub 連携で自動デプロイ |
| 定期実行 | GitHub Actions | 毎日 JST 21:00 に通知バッチ（notify.py）を実行 |

**運用コスト: ¥0**（全サービス無料枠内で稼働）

### AI 分類の詳細

| 用途 | モデル | 選定理由 |
|------|--------|----------|
| テキスト分類 | `openrouter/free` | 特定モデルに依存せず、利用可能な無料モデルを自動選択。安定性・可用性が高い |
| 画像分類 | `google/gemma-3-27b-it:free` | 無料マルチモーダルモデルとして精度・安定性が高い |

- 1 回の API 呼び出しで **タイトル生成 + カテゴリ分類** を同時に行う
- 画像はマルチモーダル LLM に直接渡して処理（OCR 不要）
- AI API がエラーを返した場合は、タイトル先頭 30 文字 + カテゴリ「未分類」にフォールバック
- AI レスポンスがマークダウンコードブロックで囲まれている場合の解析処理を実装済み

### 当初計画からの主な変更点

| 項目 | 当初予定 | 実際の実装 |
|------|----------|-----------|
| テキスト分類モデル | `qwen/qwen3-235b-a22b:free` | `openrouter/free`（無料モデル自動選択） |
| 画像分類モデル | `qwen/qwen-2.5-vl-72b-instruct:free` | `google/gemma-3-27b-it:free` |
| ユーザー認証 | Supabase Auth | Flask 直接 OAuth（LINE Login） |
| 定期実行 | Render Cron Job | GitHub Actions |
| エラーハンドリング | 全タスク完了後に一括対応 | 各機能実装時に並行して組み込み |
| エラー時の返信 | 成功メッセージ → エラー時に差し替え | エラーメッセージをデフォルト → 成功時に上書き（より安全） |

---

## アーキテクチャ

```
┌─────────┐    Webhook     ┌──────────────┐    AI分類    ┌───────────┐
│  LINE   │ ─────────────→ │  Flask App   │ ──────────→ │ OpenRouter│
│  Bot    │ ←───────────── │  (Render)    │ ←────────── │   API     │
└─────────┘   Push Message └──────┬───────┘             └───────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │ Supabase  │ │ Supabase  │ │  GitHub   │
             │    DB     │ │  Storage  │ │  Actions  │
             └───────────┘ └───────────┘ └─────┬─────┘
                                               │ cron (毎日 JST 21:00)
                                               ↓
                                        ┌────────────┐
                                        │ notify.py  │
                                        └────────────┘
```

### データフロー

1. **保存**: ユーザーが LINE Bot にメッセージ送信 → Webhook で Flask が受信
2. **分類**: AI がタイトル生成＆カテゴリ分類（画像はそのまま AI に渡して処理）→ DB に保存
3. **閲覧**: Web UI に LINE ログインしてアイテム一覧を確認・編集
4. **通知**: GitHub Actions が毎日 `notify.py` を実行 → 対象アイテムを LINE でまとめ通知

### 認証フロー（LINE Login）

```
1. ユーザーが「LINEでログイン」ボタンをクリック
2. Flask が LINE OAuth エンドポイントにリダイレクト
3. LINE が認可コードを /login/callback に返す
4. Flask が認可コードをアクセストークンに交換
5. Flask が LINE プロフィール情報を取得
6. users テーブルに UPSERT（初回ログイン時はデフォルトカテゴリ・設定を作成）
7. Flask セッションにユーザー情報を保存
8. トップページ（/）にリダイレクト
```

---

## プロジェクト構成

```
re-find/
├── app.py                 # メインアプリケーション (Flask)
│                          #   - LINE Webhook 受信
│                          #   - LINE Login OAuth 処理
│                          #   - Web UI ルーティング
│                          #   - REST API エンドポイント
├── notify.py              # 通知バッチスクリプト（GitHub Actions で実行 / --dry-run 対応）
├── ai_classifier.py       # AI テキスト/画像分類（OpenRouter API）
├── ogp_fetcher.py         # Web ページのタイトル・サムネイル取得（OGP）
├── storage_handler.py     # Supabase Storage への画像アップロード
├── activity_logger.py     # ユーザー行動ログ記録
│
├── templates/
│   ├── base.html          # 共通レイアウト（ヘッダー・フッター）
│   ├── index.html         # メインページ（アイテム一覧・カテゴリタブ）
│   ├── login.html         # LINE ログインページ
│   ├── categories.html    # カテゴリ管理ページ
│   ├── shared_item.html   # 共有リンク閲覧ページ（ログイン不要）
│   └── liff.html          # LINE アプリ内ブラウザ対応ページ
│
├── static/
│   ├── css/               # ページ別スタイルシート（6 ファイル）
│   │   ├── common.css     #   共通スタイル
│   │   ├── login.css      #   ログインページ
│   │   ├── index.css      #   メインページ
│   │   ├── modal.css      #   編集モーダル
│   │   ├── categories.css #   カテゴリ管理
│   │   └── shared.css     #   共有ページ
│   ├── js/                # ページ別 JavaScript（4 ファイル）
│   │   ├── common.js      #   共通処理（API呼び出し等）
│   │   ├── index.js       #   メインページ（カテゴリフィルタ等）
│   │   ├── modal.js       #   編集モーダル操作
│   │   └── categories.js  #   カテゴリ管理操作
│   └── img/
│       ├── favicon.ico
│       └── no-image.png   # サムネイルなし時のプレースホルダー
│
├── .github/workflows/
│   └── notify.yml         # 通知バッチの cron ジョブ定義
│
├── requirements.txt       # Python 依存パッケージ
├── runtime.txt            # Python バージョン指定（3.11.8）
└── .env.example           # 環境変数テンプレート
```

### API エンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/health` | ヘルスチェック（認証不要・UptimeRobot 用） |
| GET | `/` | メインページ（アイテム一覧） |
| GET | `/login` | ログインページ |
| GET | `/login/line` | LINE OAuth 認可開始 |
| GET | `/login/callback` | LINE OAuth コールバック |
| GET | `/logout` | ログアウト |
| GET | `/categories` | カテゴリ管理ページ |
| GET | `/share/<token>` | 共有リンク閲覧ページ |
| GET | `/liff` | LIFF 対応ページ |
| PUT | `/api/items/<item_id>` | アイテム更新（タイトル・カテゴリ・メモ・ステータス） |
| DELETE | `/api/items/<item_id>` | アイテム削除（ソフトデリート） |
| POST | `/api/items/<item_id>/share` | 共有リンク作成 |
| POST | `/api/categories` | カテゴリ追加 |
| PUT | `/api/categories/<id>` | カテゴリ名変更 |
| DELETE | `/api/categories/<id>` | カテゴリ削除（アイテムは「未分類」に移動） |
| POST | `/callback` | LINE Webhook エンドポイント |

---

## データベース設計

主要 7 テーブル（Supabase PostgreSQL）。Flask が `service_role_key` で全 DB アクセスを行い、
アプリケーション側でユーザー間のデータ分離を実施しています。

| テーブル | 役割 |
|----------|------|
| `users` | LINE ユーザー情報（`line_user_id` と自動生成 UUID の紐付け） |
| `categories` | カテゴリ（ユーザーごとに独立、`UNIQUE: line_user_id + name`） |
| `items` | 保存アイテム本体（テキスト/URL/画像、ソフトデリート方式） |
| `shared_links` | 共有リンクのトークン管理 |
| `user_settings` | 通知 ON/OFF、通知時刻などの個人設定 |
| `notification_rules` | 通知間隔ルール（忘却曲線ベースの 6 段階） |
| `user_activity_logs` | ユーザー行動ログ（通知送信記録・将来の分析用） |

### 重要な設計ルール

- **ソフトデリート**: items にアクセスするすべての箇所で `deleted_at IS NULL` を条件に含めること
- **カテゴリ削除時**: アイテムは「未分類」カテゴリに移動される
- **`service_role_key`**: RLS をバイパスできる管理者キー。フロントエンド（JS）には絶対に書かない

---

## セットアップ

### 前提条件

- Python 3.11+
- [LINE Developers](https://developers.line.biz/) アカウント（Messaging API + LINE Login チャネル）
- [Supabase](https://supabase.com/) プロジェクト
- [OpenRouter](https://openrouter.ai/) API キー
- [Render](https://render.com/) アカウント（デプロイ用）

### ローカル開発

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/re-find.git
cd re-find

# 仮想環境を作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を編集して各サービスのキーを入力

# 開発モードで起動
# DEV_MODE=true にすると LINE ログインをスキップして開発できる
python app.py
# → http://127.0.0.1:5000 で起動
```

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `LINE_CHANNEL_SECRET` | Messaging API チャネルシークレット | Yes |
| `LINE_CHANNEL_ACCESS_TOKEN` | Messaging API アクセストークン | Yes |
| `LINE_LOGIN_CHANNEL_ID` | LINE Login チャネル ID | Yes |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login チャネルシークレット | Yes |
| `SUPABASE_URL` | Supabase プロジェクト URL | Yes |
| `SUPABASE_KEY` | Supabase anon キー | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role キー（DB アクセス・通知バッチ用） | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API キー | Yes |
| `FLASK_SECRET_KEY` | Flask セッション暗号化キー | Yes |
| `DEV_MODE` | `true` にすると LINE 認証をスキップ（開発時のみ） | No |
| `DEV_USER_ID` | 開発用ダミーユーザー ID（`DEV_MODE` 時に使用） | No |

### デプロイ (Render)

1. GitHub リポジトリを Render に接続
2. Environment に上記の環境変数をすべて設定
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`
5. デプロイ後、LINE Developers で Webhook URL を設定:
   `https://<your-app>.onrender.com/callback`

> **Render 無料枠の注意点**
> 15 分間アクセスがないとサービスがスリープ状態になります。
> `/health` エンドポイント + UptimeRobot（5 分間隔）でスリープを防止しています。

### 通知バッチ (GitHub Actions)

`.github/workflows/notify.yml` が毎日 UTC 12:00（JST 21:00）に `notify.py` を実行します。

GitHub リポジトリの Settings → Secrets and variables → Actions に以下を追加してください：

| Secret 名 | 説明 |
|-----------|------|
| `LINE_CHANNEL_SECRET` | Messaging API チャネルシークレット |
| `LINE_CHANNEL_ACCESS_TOKEN` | Messaging API アクセストークン |
| `SUPABASE_URL` | Supabase プロジェクト URL |
| `SUPABASE_KEY` | Supabase anon キー |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role キー |
| `OPENROUTER_API_KEY` | OpenRouter API キー |

---

## 今後の改善について

### 優先度: 高

| # | 改善内容 | 理由 |
|---|----------|------|
| 1 | **検索・ソート機能** | アイテムが増えると目的の情報を見つけにくくなる。キーワード検索・日付ソートは必須 |
| 2 | **app.py の Blueprint 分割** | 1,000 行超の単一ファイルは保守が難しい。認証・API・Webhook を Blueprint に分離する |
| 3 | **エラーハンドリングの統一** | API エンドポイントごとにエラー処理がバラバラ。共通エラーハンドラを整備する |

### 優先度: 中

| # | 改善内容 | 理由 |
|---|----------|------|
| 5 | **通知時刻のユーザー設定** | `user_settings.notify_time` は DB に存在するが未実装。好きな時刻を設定できるようにする |
| 6 | **AI モデルの改善** | 日本語テキストや画像の分類精度向上のため、より高精度なモデルへの切り替えを検討 |
| 7 | **アクティビティログの活用** | 蓄積されたログを分析し、利用状況や通知の開封率などを可視化する |
| 8 | **PWA 対応** | manifest.json + Service Worker でホーム画面への追加・オフライン閲覧を可能にする |

### 将来構想

| # | 構想 | 説明 |
|---|------|------|
| 9 | **スマート通知タイミング** | ユーザーの LINE 利用パターンを学習し、開封率が高い時間帯に通知を送る |
| 10 | **PDF・動画・音声の対応** | 対応メディアを拡充してユースケースを広げる |
| 11 | **ネイティブアプリ化** | より快適な体験のため、iOS/Android アプリとして再実装する |

---

## プロジェクト概要

| 項目 | 内容 |
|------|------|
| プロダクト名 | Re:find（リファインド） |
| 一言説明 | 保存した情報を埋もれさせない「情報再発見」サービス |
| チーム | 3名（PBL 昼チーム01） |
| 開発期間 | 2週間（2/19〜2/27） |
| 予算 | ¥0（すべて無料枠で運用） |

---

## ライセンス

MIT
