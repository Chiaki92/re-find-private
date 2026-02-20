# ==============================================================
# ogp_fetcher.py
# ==============================================================
# 役割：URLからOGP情報（タイトル・説明・サムネイル画像）を取得する
#
# OGP（Open Graph Protocol）とは？
#   Webページに埋め込まれた「そのページの要約情報」のこと。
#   LINEやXでURLを貼ったときに表示されるプレビューの元データ。
#   HTMLの<head>内に以下のようなmetaタグとして記述される：
#     <meta property="og:title" content="ページのタイトル">
#     <meta property="og:description" content="ページの説明">
#     <meta property="og:image" content="サムネイル画像のURL">
#
# 使い方：
#   from ogp_fetcher import fetch_ogp
#   result = fetch_ogp("https://example.com/article")
#   print(result)
#   # → {"title": "記事タイトル", "description": "記事の説明", "image": "https://..."}
#
# 呼び出し元：
#   app.py の URL受信ハンドラ（No.30 B-4-2 で実装予定）
# ==============================================================

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_ogp(url):
    """
    URLからOGP情報（タイトル・説明・画像URL）を取得する。

    処理の流れ：
      1. URLにHTTPリクエストを送る
      2. 返ってきたHTMLをBeautifulSoupで解析する
      3. og:title, og:description, og:image のmetaタグを探す
      4. 見つかった情報を辞書で返す

    取得できなかった場合のフォールバック（代替処理）：
      - OGPタグがない → HTMLの<title>タグから取得を試みる
      - <title>もない → URLそのものをタイトルにする
      - リクエスト自体が失敗 → URLのドメイン名をタイトルにする

    引数:
        url (str): OGP情報を取得したいWebページのURL
                   例: "https://news.yahoo.co.jp/articles/xxxxx"

    戻り値:
        dict: 以下のキーを持つ辞書
            - "title" (str): ページのタイトル（必ず何かの値が入る）
            - "description" (str): ページの説明文（取得できない場合は空文字）
            - "image" (str or None): サムネイル画像のURL（取得できない場合はNone）
    """
    try:
        # -------------------------------------------------------
        # Step 1: URLにHTTPリクエストを送る
        # -------------------------------------------------------
        # timeout=10 : 10秒待っても応答がなければ諦める（アプリが固まるのを防ぐ）
        # User-Agent : ブラウザからのアクセスに見せかける（Bot対策回避）
        #   → 一部のサイトはBotからのアクセスをブロックするため必要
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # ステータスコードが200番台以外（404エラー等）ならエラーを発生させる
        response.raise_for_status()

        # -------------------------------------------------------
        # Step 2: HTMLをBeautifulSoupで解析する
        # -------------------------------------------------------
        # "html.parser" : Python標準のHTMLパーサー（追加インストール不要）
        soup = BeautifulSoup(response.text, "html.parser")

        # -------------------------------------------------------
        # Step 3: OGPのmetaタグを探す
        # -------------------------------------------------------
        # soup.find("meta", property="og:title") は以下のようなタグを探す：
        #   <meta property="og:title" content="ページのタイトル">
        #
        # 見つかった場合 → タグオブジェクトが返る → ["content"]で中身を取得
        # 見つからなかった場合 → None が返る
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")

        # OGPタグが見つかった場合は content 属性の値を取得、なければ None
        title = og_title["content"] if og_title else None
        description = og_desc["content"] if og_desc else None
        image = og_image["content"] if og_image else None

        # -------------------------------------------------------
        # Step 4: フォールバック処理（OGPタイトルがない場合）
        # -------------------------------------------------------
        if not title:
            # OGPタイトルがない → HTMLの<title>タグを探す
            # 例: <title>Yahoo!ニュース - 国内最大級のニュースサイト</title>
            title_tag = soup.find("title")
            title = title_tag.string if title_tag else url
            # title_tag.string : <title>タグの中のテキストを取得
            # それもなければ URL そのものをタイトルにする

        # -------------------------------------------------------
        # Step 5: 結果を辞書で返す
        # -------------------------------------------------------
        return {
            "title": title or url,          # Noneや空文字の場合はURLを使う
            "description": description or "",  # Noneの場合は空文字にする
            "image": image                  # 画像URLはNoneのままでもOK
        }

    except Exception as e:
        # -------------------------------------------------------
        # エラー時のフォールバック処理
        # -------------------------------------------------------
        # どんなエラーでもアプリが落ちないようにキャッチする
        # - requests.exceptions.Timeout : タイムアウト
        # - requests.exceptions.ConnectionError : 接続エラー
        # - requests.exceptions.HTTPError : 404, 500等
        # - その他の予期しないエラー
        print(f"OGP取得エラー ({url}): {e}")

        # URLからドメイン名を抽出してタイトルの代わりにする
        # 例: "https://news.yahoo.co.jp/articles/xxx" → "news.yahoo.co.jp"
        domain = urlparse(url).netloc

        return {
            "title": domain or url,    # ドメイン名が取れなければURLそのもの
            "description": "",
            "image": None
        }






