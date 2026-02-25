-- ============================================
-- カテゴリ並び替え機能: DBマイグレーション
-- ============================================
-- このファイルは Supabase SQL Editor に貼り付けて手動実行する。
-- Flask からは実行しない。

-- categories テーブルに sort_order カラムを追加（INTEGER, DEFAULT 0）
ALTER TABLE categories
ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;

-- 既存カテゴリに連番を振る（created_at 順）
-- 「未分類」は 999999 に固定
UPDATE categories
SET sort_order = sub.new_order
FROM (
    SELECT
        id,
        CASE
            WHEN name = '未分類' THEN 999999
            ELSE ROW_NUMBER() OVER (
                PARTITION BY line_user_id
                ORDER BY created_at ASC
            )
        END AS new_order
    FROM categories
) AS sub
WHERE categories.id = sub.id;
