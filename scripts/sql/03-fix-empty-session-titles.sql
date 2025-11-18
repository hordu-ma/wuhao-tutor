-- SQL 修复脚本：填充空的会话标题
-- 此脚本用于修复 PostgreSQL 数据库中 title 为空的会话记录
--
-- 功能：
-- 1. 查找所有 title 为 NULL 或空字符串的会话
-- 2. 从会话的第一个问题中提取内容作为标题
-- 3. 如果没有问题，使用会话创建时间作为标题
--
-- 使用方法：
--   psql -U user -d database -f scripts/sql/03-fix-empty-session-titles.sql
--
-- 注意：请先备份数据库！

-- 开始事务
BEGIN;

-- 记录修复前的统计
SELECT
    COUNT(*) as empty_title_count,
    COUNT(DISTINCT user_id) as affected_users
FROM chat_sessions
WHERE title IS NULL OR TRIM(title) = '';

-- 步骤 1：为有问题的会话从第一个问题生成标题
WITH first_questions AS (
    SELECT DISTINCT ON (session_id)
        session_id,
        content,
        created_at
    FROM questions
    WHERE session_id IN (
        SELECT id FROM chat_sessions
        WHERE title IS NULL OR TRIM(title) = ''
    )
    ORDER BY session_id, created_at ASC
)
UPDATE chat_sessions cs
SET title = CASE
    WHEN fq.content IS NOT NULL THEN
        CASE
            WHEN LENGTH(TRIM(fq.content)) > 20 THEN
                SUBSTRING(TRIM(fq.content), 1, 20) || '...'
            ELSE
                TRIM(fq.content)
        END
    ELSE
        '会话 ' || TO_CHAR(cs.created_at, 'MM-DD HH:MI')
END,
updated_at = CURRENT_TIMESTAMP
FROM first_questions fq
WHERE cs.id = fq.session_id
  AND (cs.title IS NULL OR TRIM(cs.title) = '');

-- 步骤 2：为没有问题的会话设置默认标题
UPDATE chat_sessions
SET title = '会话 ' || TO_CHAR(created_at, 'MM-DD HH:MI'),
    updated_at = CURRENT_TIMESTAMP
WHERE title IS NULL OR TRIM(title) = '';

-- 验证修复结果
SELECT
    COUNT(*) as remaining_empty_titles,
    COUNT(CASE WHEN title LIKE '会话%' THEN 1 END) as auto_generated_titles,
    COUNT(CASE WHEN title NOT LIKE '会话%' THEN 1 END) as user_generated_titles
FROM chat_sessions
WHERE title IS NOT NULL;

-- 提交事务
COMMIT;

-- 打印完成消息
\echo '✅ 会话标题修复完成！'
