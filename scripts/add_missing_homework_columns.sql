-- 为生产环境的 homework 表添加缺失的列
-- 执行时间: 2025-10-11

-- 检查列是否存在并添加 (PostgreSQL 不支持 IF NOT EXISTS for ADD COLUMN before 9.6)
-- 我们需要安全地添加列

DO $$
BEGIN
    -- 添加 homework_type 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'homework_type'
    ) THEN
        ALTER TABLE homework ADD COLUMN homework_type VARCHAR(20) NOT NULL DEFAULT 'daily';
        COMMENT ON COLUMN homework.homework_type IS '作业类型';
    END IF;

    -- 添加 grade_level 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'grade_level'
    ) THEN
        ALTER TABLE homework ADD COLUMN grade_level VARCHAR(20) NOT NULL DEFAULT '8';
        COMMENT ON COLUMN homework.grade_level IS '适用学段';
    END IF;

    -- 添加 subject 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'subject'
    ) THEN
        ALTER TABLE homework ADD COLUMN subject VARCHAR(20) NOT NULL DEFAULT 'other';
        COMMENT ON COLUMN homework.subject IS '学科';
    END IF;

    -- 添加 difficulty_level 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'difficulty_level'
    ) THEN
        ALTER TABLE homework ADD COLUMN difficulty_level VARCHAR(10) NOT NULL DEFAULT 'medium';
        COMMENT ON COLUMN homework.difficulty_level IS '难度级别';
    END IF;

    -- 添加 description 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'description'
    ) THEN
        ALTER TABLE homework ADD COLUMN description TEXT;
        COMMENT ON COLUMN homework.description IS '作业描述';
    END IF;

    -- 添加 chapter 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'chapter'
    ) THEN
        ALTER TABLE homework ADD COLUMN chapter VARCHAR(100);
        COMMENT ON COLUMN homework.chapter IS '章节';
    END IF;

    -- 添加 knowledge_points 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'knowledge_points'
    ) THEN
        ALTER TABLE homework ADD COLUMN knowledge_points JSON;
        COMMENT ON COLUMN homework.knowledge_points IS '知识点列表(JSON格式)';
    END IF;

    -- 添加 estimated_duration 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'estimated_duration'
    ) THEN
        ALTER TABLE homework ADD COLUMN estimated_duration INTEGER;
        COMMENT ON COLUMN homework.estimated_duration IS '预计完成时间(分钟)';
    END IF;

    -- 添加 deadline 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'deadline'
    ) THEN
        ALTER TABLE homework ADD COLUMN deadline TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN homework.deadline IS '截止时间';
    END IF;

    -- 添加 creator_id 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'creator_id'
    ) THEN
        ALTER TABLE homework ADD COLUMN creator_id UUID;
        COMMENT ON COLUMN homework.creator_id IS '创建者ID(教师)';
    END IF;

    -- 添加 creator_name 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'creator_name'
    ) THEN
        ALTER TABLE homework ADD COLUMN creator_name VARCHAR(50);
        COMMENT ON COLUMN homework.creator_name IS '创建者姓名';
    END IF;

    -- 添加 is_active 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE homework ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
        COMMENT ON COLUMN homework.is_active IS '是否激活';
    END IF;

    -- 添加 is_template 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'is_template'
    ) THEN
        ALTER TABLE homework ADD COLUMN is_template BOOLEAN NOT NULL DEFAULT FALSE;
        COMMENT ON COLUMN homework.is_template IS '是否为模板';
    END IF;

    -- 添加 total_submissions 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'total_submissions'
    ) THEN
        ALTER TABLE homework ADD COLUMN total_submissions INTEGER NOT NULL DEFAULT 0;
        COMMENT ON COLUMN homework.total_submissions IS '总提交数';
    END IF;

    -- 添加 avg_score 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'homework' AND column_name = 'avg_score'
    ) THEN
        ALTER TABLE homework ADD COLUMN avg_score FLOAT;
        COMMENT ON COLUMN homework.avg_score IS '平均分';
    END IF;

END $$;

-- 创建索引 (如果不存在)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'homework' AND indexname = 'idx_homework_subject_grade'
    ) THEN
        CREATE INDEX idx_homework_subject_grade ON homework(subject, grade_level);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'homework' AND indexname = 'idx_homework_creator_active'
    ) THEN
        CREATE INDEX idx_homework_creator_active ON homework(creator_id, is_active);
    END IF;
END $$;

-- 验证结果
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'homework' 
AND column_name IN ('homework_type', 'grade_level', 'subject', 'difficulty_level')
ORDER BY column_name;
