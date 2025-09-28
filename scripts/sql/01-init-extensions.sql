-- 01-init-extensions.sql
-- PostgreSQL数据库扩展初始化脚本
-- 用于启用必要的数据库扩展和功能

-- 启用UUID生成扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用加密函数扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 启用全文搜索扩展
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 启用数组操作扩展
CREATE EXTENSION IF NOT EXISTS "intarray";

-- 创建自定义函数：生成UUID v4
CREATE OR REPLACE FUNCTION generate_uuid_v4()
RETURNS uuid AS $$
BEGIN
    RETURN uuid_generate_v4();
END;
$$ LANGUAGE plpgsql;

-- 创建自定义函数：更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建自定义函数：生成短ID
CREATE OR REPLACE FUNCTION generate_short_id(length INTEGER DEFAULT 8)
RETURNS TEXT AS $$
DECLARE
    chars TEXT := '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz';
    result TEXT := '';
    i INTEGER := 0;
BEGIN
    IF length < 1 THEN
        RAISE EXCEPTION 'Length must be at least 1';
    END IF;

    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 创建自定义函数：JSON数组包含检查
CREATE OR REPLACE FUNCTION jsonb_array_contains_text(jsonb_array JSONB, search_text TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN jsonb_array ? search_text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 创建自定义函数：计算字符串相似度
CREATE OR REPLACE FUNCTION text_similarity_score(text1 TEXT, text2 TEXT)
RETURNS FLOAT AS $$
BEGIN
    RETURN similarity(text1, text2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '✅ PostgreSQL扩展和自定义函数初始化完成';
    RAISE NOTICE '   - UUID生成扩展已启用';
    RAISE NOTICE '   - 加密函数扩展已启用';
    RAISE NOTICE '   - 全文搜索扩展已启用';
    RAISE NOTICE '   - 自定义函数已创建';
END $$;
