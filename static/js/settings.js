/* ==========================================================
   Re:find — settings.js
   通知設定画面の JavaScript

   ■ このファイルの役割：
     - 通知時間の変更を保存
     - 通知 ON/OFF の切り替え
     - 保存ボタンのクリック処理

   ■ 使用する共通関数（common.js で定義）：
     - apiPut()    → PUT /api/settings にデータを送信
     - showToast() → 画面上部に「保存しました」等を表示
   ========================================================== */


/* ----------------------------------------------------------
   ページ読み込み完了後に実行
   ---------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function () {

    // ── DOM要素の取得 ──
    const timeSelect     = document.getElementById('notify-time');      // 通知時間セレクトボックス
    const enabledCheckbox = document.getElementById('notify-enabled');  // 通知ON/OFFチェックボックス
    const toggleLabel    = document.getElementById('toggle-label');     // ON/OFF のテキスト表示
    const saveBtn        = document.getElementById('save-settings-btn'); // 保存ボタン


    /* ----------------------------------------------------------
       トグルスイッチのラベル更新

       チェックボックスの状態が変わったら、
       左側の「ON」「OFF」テキストをリアルタイムで切り替える。
       ---------------------------------------------------------- */
    enabledCheckbox.addEventListener('change', function () {
        toggleLabel.textContent = this.checked ? 'ON' : 'OFF';
    });


    /* ----------------------------------------------------------
       保存ボタンのクリック処理

       セレクトボックスとチェックボックスの値を
       PUT /api/settings に送信して DB を更新する。
       ---------------------------------------------------------- */
    saveBtn.addEventListener('click', async function () {
        // 送信データを組み立て
        const data = {
            notify_time: timeSelect.value,        // 例: "21:00", "07:30"
            notify_enabled: enabledCheckbox.checked, // true / false
        };

        // API に送信（common.js の apiPut を使用）
        const result = await apiPut('/api/settings', data);

        if (result && result.ok) {
            showToast('設定を保存しました');
        }
    });
});
