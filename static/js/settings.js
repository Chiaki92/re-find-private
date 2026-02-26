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


    /* ==========================================================
       忘却曲線リマインド説明ポップアップ
       ========================================================== */

    // ── DOM要素の取得 ──
    var infoHelpBtn  = document.getElementById('info-help-btn');
    var infoPopup    = document.getElementById('info-popup');
    var infoCloseBtn = document.getElementById('info-close-btn');

    /** ポップアップを開く */
    function openInfoPopup() {
        infoPopup.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // タイムラインは初回だけ生成
        var timeline = document.getElementById('info-timeline');
        if (!timeline.hasChildNodes()) {
            buildInfoTimeline(timeline);
        }
    }

    /** ポップアップを閉じる */
    function closeInfoPopup() {
        infoPopup.style.display = 'none';
        document.body.style.overflow = '';
    }

    // イベント登録
    infoHelpBtn.addEventListener('click', openInfoPopup);
    infoCloseBtn.addEventListener('click', closeInfoPopup);
    infoPopup.addEventListener('click', function (e) {
        if (e.target === this) closeInfoPopup();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && infoPopup.style.display === 'flex') {
            closeInfoPopup();
        }
    });

    /** 6段階タイムラインを生成 */
    function buildInfoTimeline(container) {
        var stages = [
            { d: '1日後',  t: '情報を忘れ始めるタイミング' },
            { d: '3日後',  t: '完全に忘れる前に届ける' },
            { d: '7日後',  t: '生活サイクル1周分' },
            { d: '14日後', t: '多くは行動済みの時期' },
            { d: '30日後', t: '1ヶ月の節目リマインド' },
            { d: '60日後', t: '最終通知', final: true },
        ];

        var html = '';
        for (var i = 0; i < stages.length; i++) {
            var isLast = (i === stages.length - 1);
            var lastClass = isLast ? ' last' : '';

            html += '<div class="tl-item">';
            html += '  <div class="tl-dot-col"><div class="tl-dot' + lastClass + '"></div>';
            if (!isLast) html += '  <div class="tl-line"></div>';
            html += '  </div>';
            html += '  <div class="tl-body"><div class="tl-row">';
            html += '    <span class="tl-day' + lastClass + '">' + stages[i].d + '</span>';
            html += '    <span class="tl-desc">' + stages[i].t + '</span>';
            if (isLast) html += '    <span class="tl-final-tag">最終</span>';
            html += '  </div>';

            // 最終通知の詳細説明
            if (isLast) {
                html += '  <div class="tl-final-detail">';
                html += '「これが最後のリマインドです」と経過日数・通知回数を伝えます。';
                html += '通知終了後はアーカイブされますが、必要であればWebアプリ上で通知を最初から再開できます。';
                html += '  </div>';
            }

            html += '  </div>';
            html += '</div>';
        }

        container.innerHTML = html;
    }
});
