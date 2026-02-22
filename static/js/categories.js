/* ==========================================================
   Re:find — categories.js
   カテゴリ管理画面の JavaScript
   
   ■ このファイルの役割：
     1. 新規カテゴリの追加
     2. カテゴリ名のインライン編集（フォーカスが外れたら自動保存）
     3. カテゴリの削除（確認ダイアログ付き）
   
   ■ 前提：
     - common.js が先に読み込まれていること（apiPost, apiPut, apiDelete, showToast）
   ========================================================== */

document.addEventListener('DOMContentLoaded', function() {

    /* ----------------------------------------------------------
       1. 新規カテゴリの追加
       
       「+ 追加」ボタンを押すと、入力欄のテキストを
       新しいカテゴリとして Flask API に送信する。
       ---------------------------------------------------------- */

    const addBtn = document.getElementById('add-category-btn');
    const addInput = document.getElementById('new-category-input');

    addBtn.addEventListener('click', async function() {
        // 入力値を取得（前後の空白を除去）
        const name = addInput.value.trim();

        // 空欄チェック
        if (!name) {
            showToast('カテゴリ名を入力してください', 'error');
            return;
        }

        // Flask API にPOSTリクエスト
        const result = await apiPost('/api/categories', { name: name });

        if (result) {
            showToast(`「${name}」を追加しました`);
            // ページをリロードして最新状態を表示
            window.location.reload();
        }
    });

    // Enterキーでも追加できるようにする
    addInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            addBtn.click();
        }
    });


    /* ----------------------------------------------------------
       2. カテゴリ名のインライン編集
       
       カテゴリ名の input からフォーカスが外れたとき、
       元の名前と変わっていれば自動的に保存する。
       ---------------------------------------------------------- */

    // すべてのカテゴリ名 input を取得
    const nameInputs = document.querySelectorAll('.category-name-input');

    nameInputs.forEach(function(input) {
        // フォーカスが外れたとき（blur イベント）
        input.addEventListener('blur', async function() {
            const newName = this.value.trim();
            const originalName = this.getAttribute('data-original-name');

            // 名前が変わっていなければ何もしない
            if (newName === originalName) return;

            // 空欄チェック
            if (!newName) {
                // 空欄にされた場合は元の名前に戻す
                this.value = originalName;
                showToast('カテゴリ名は空にできません', 'error');
                return;
            }

            // カテゴリIDを取得（親要素の data-category-id）
            const categoryId = this.closest('.category-item').getAttribute('data-category-id');

            // Flask API にPUTリクエスト
            const result = await apiPut(`/api/categories/${categoryId}`, { name: newName });

            if (result) {
                // 元の名前を更新（次回の比較用）
                this.setAttribute('data-original-name', newName);
                showToast('カテゴリ名を変更しました');
            } else {
                // 失敗時は元に戻す
                this.value = originalName;
            }
        });

        // Enterキーでフォーカスを外す（＝保存をトリガー）
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    });


    /* ----------------------------------------------------------
       3. カテゴリの削除
       
       ゴミ箱ボタンを押すと確認ダイアログを出して、
       OKならカテゴリを削除する。
       アイテムは「未分類」に移動される（Flask API側で処理）。
       ---------------------------------------------------------- */

    const deleteBtns = document.querySelectorAll('.category-delete-btn');

    deleteBtns.forEach(function(btn) {
        btn.addEventListener('click', async function() {
            // 親要素からカテゴリIDと名前を取得
            const categoryItem = this.closest('.category-item');
            const categoryId = categoryItem.getAttribute('data-category-id');
            const categoryName = categoryItem.querySelector('.category-name-input').value;

            // 確認ダイアログ
            const confirmed = confirm(
                `「${categoryName}」を削除しますか？\n` +
                `このカテゴリのアイテムは「未分類」に移動されます。`
            );

            if (!confirmed) return;

            // Flask API にDELETEリクエスト
            const result = await apiDelete(`/api/categories/${categoryId}`);

            if (result) {
                showToast(`「${categoryName}」を削除しました`);
                // 画面からカテゴリ行を削除（リロードなし）
                categoryItem.remove();
            }
        });
    });
});