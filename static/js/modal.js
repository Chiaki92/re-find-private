/* ==========================================================
   Re:find — modal.js
   編集モーダルの JavaScript
   
   ■ このファイルの役割：
     1. モーダルを開く（openModal）
     2. モーダルを閉じる（closeModal）
     3. 保存ボタンの処理
     4. 削除ボタンの処理
     5. 「対応済みにする」ボタンの処理
     6. 共有リンク作成ボタンの処理
   
   ■ 前提：
     - common.js が先に読み込まれていること（apiPut, apiDelete, showToast）
     - index.js が先に読み込まれていること
     - ITEMS_DATA が index.html で定義されていること
   ========================================================== */


/* ----------------------------------------------------------
   0. グローバル変数
   
   現在モーダルで編集中のアイテムIDを保持する。
   保存・削除のときに「どのアイテムを操作するか」を知るために使う。
   ---------------------------------------------------------- */
let currentItemId = null;


/* ----------------------------------------------------------
   1. モーダルを開く
   
   index.js のカードクリックから呼ばれる。
   アイテムのデータをモーダルの各フォームに反映する。
   
   ■ 引数 item のプロパティ：
     - id           : アイテムID
     - title        : タイトル
     - category_id  : カテゴリID
     - memo         : メモ
     - type         : 'image' | 'url' | 'text'
     - status       : 'pending' | 'done'
     - image_url    : 画像URL（imageタイプ）
     - ogp_image    : OGP画像URL（urlタイプ）
     - original_url : 元のURL（urlタイプ）
     - created_at   : 保存日
   ---------------------------------------------------------- */
function openModal(item) {
    // 現在編集中のアイテムIDを記録
    currentItemId = item.id;

    // --- タイトルを設定 ---
    document.getElementById('modal-title').value = item.title || '';

    // --- カテゴリを設定 ---
    const categorySelect = document.getElementById('modal-category');
    if (categorySelect) {
        categorySelect.value = item.category_id || '';
    }

    // --- メモを設定 ---
    document.getElementById('modal-memo').value = item.memo || '';

    // --- サムネイルを設定 ---
    const thumbContainer = document.getElementById('modal-thumb');
    if (item.type === 'image' && item.image_url) {
        // 画像タイプ：保存された画像を表示
        thumbContainer.innerHTML = `<img src="${item.image_url}" alt="">`;
    } else if (item.type === 'url' && item.ogp_image) {
        // URLタイプ：OGP画像を表示
        thumbContainer.innerHTML = `<img src="${item.ogp_image}" alt="">`;
    } else {
        // テキスト or 画像なし：アイコン表示
        const icon = item.type === 'image' ? '📷' : item.type === 'url' ? '🔗' : '📝';
        thumbContainer.innerHTML = `<div class="edit-modal-thumb-icon">${icon}</div>`;
    }

    // --- 元のURL（URLタイプのみ表示） ---
    const urlSection = document.getElementById('modal-url-section');
    const urlLink = document.getElementById('modal-url');
    if (item.type === 'url' && item.original_url) {
        urlSection.style.display = '';
        urlLink.href = item.original_url;
        urlLink.textContent = item.original_url;
    } else {
        urlSection.style.display = 'none';
    }

    // --- 保存日を設定 ---
    const dateEl = document.getElementById('modal-date');
    if (item.created_at) {
        // ISO日時を読みやすい形式に変換
        const date = new Date(item.created_at);
        dateEl.textContent = `保存日：${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
    } else {
        dateEl.textContent = '';
    }

    // --- 対応済みボタンの状態を反映 ---
    const doneBtn = document.getElementById('modal-done-btn');
    if (item.status === 'done') {
        doneBtn.textContent = '↩ 未対応に戻す';
        doneBtn.classList.add('is-done');
    } else {
        doneBtn.textContent = '✓ 対応済みにする';
        doneBtn.classList.remove('is-done');
    }

    // --- 共有リンクボタンをリセット ---
    const shareBtn = document.getElementById('modal-share-btn');
    shareBtn.textContent = '🔗 共有リンクを作成';
    shareBtn.classList.remove('copied');

    // --- モーダルを表示 ---
    document.getElementById('edit-modal').style.display = 'flex';

    // body のスクロールを無効にする（モーダルの後ろが動かないように）
    document.body.style.overflow = 'hidden';
}


/* ----------------------------------------------------------
   2. モーダルを閉じる
   ---------------------------------------------------------- */
function closeModal() {
    document.getElementById('edit-modal').style.display = 'none';
    
    // body のスクロールを元に戻す
    document.body.style.overflow = '';
    
    // 編集中のアイテムIDをリセット
    currentItemId = null;
}


/* ----------------------------------------------------------
   3. イベントリスナーの設定
   ---------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function() {

    // --- ✕ 閉じるボタン ---
    document.getElementById('modal-close-btn').addEventListener('click', closeModal);

    // --- オーバーレイクリックで閉じる ---
    document.getElementById('edit-modal').addEventListener('click', function(e) {
        // オーバーレイ自体がクリックされた場合のみ閉じる
        // （モーダル本体のクリックでは閉じない）
        if (e.target === this) {
            closeModal();
        }
    });

    // --- ESCキーで閉じる ---
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });


    /* --- 保存ボタン --- */
    document.getElementById('modal-save-btn').addEventListener('click', async function() {
        if (!currentItemId) return;

        // フォームから値を取得
        const data = {
            title: document.getElementById('modal-title').value,
            category_id: document.getElementById('modal-category').value,
            memo: document.getElementById('modal-memo').value,
        };

        // Flask API にPUTリクエスト
        const result = await apiPut(`/api/items/${currentItemId}`, data);

        if (result) {
            showToast('保存しました');
            // ページをリロードして最新データを表示
            // （リアルタイム更新はPhase 1では省略）
            window.location.reload();
        }
    });


    /* --- 削除ボタン --- */
    document.getElementById('modal-delete-btn').addEventListener('click', async function() {
        if (!currentItemId) return;

        // 確認ダイアログ
        if (!confirm('このアイテムを削除しますか？')) return;

        // Flask API にDELETEリクエスト
        const result = await apiDelete(`/api/items/${currentItemId}`);

        if (result) {
            showToast('削除しました');
            window.location.reload();
        }
    });


    /* --- 「対応済みにする」ボタン --- */
    document.getElementById('modal-done-btn').addEventListener('click', async function() {
        if (!currentItemId) return;

        // 現在のステータスを取得して反転する
        const item = ITEMS_DATA.find(i => String(i.id) === String(currentItemId));
        const newStatus = (item && item.status === 'done') ? 'pending' : 'done';

        // Flask API にPUTリクエスト
        const result = await apiPut(`/api/items/${currentItemId}`, {
            status: newStatus,
        });

        if (result) {
            const message = newStatus === 'done' ? '対応済みにしました' : '未対応に戻しました';
            showToast(message);
            window.location.reload();
        }
    });


    /* --- 共有リンク作成ボタン --- */
    document.getElementById('modal-share-btn').addEventListener('click', async function() {
        if (!currentItemId) return;

        const shareBtn = this;

        // Flask API にPOSTリクエスト（共有トークンを生成）
        const result = await apiPost(`/api/items/${currentItemId}/share`, {});

        if (result && result.share_url) {
            // クリップボードにコピー
            try {
                await navigator.clipboard.writeText(result.share_url);
                shareBtn.textContent = '✓ リンクをコピーしました！';
                shareBtn.classList.add('copied');
                showToast('共有リンクをコピーしました');
            } catch (err) {
                // クリップボードAPIが使えない環境のフォールバック
                prompt('共有リンクをコピーしてください：', result.share_url);
            }

            // 3秒後にボタンを元に戻す
            setTimeout(function() {
                shareBtn.textContent = '🔗 共有リンクを作成';
                shareBtn.classList.remove('copied');
            }, 3000);
        }
    });
});