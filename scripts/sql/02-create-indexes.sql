-- 02-create-indexes.sql
-- PostgreSQL数据库索引优化脚本
-- 用于创建性能优化索引，提高查询效率

-- ==============================================
-- 用户表索引
-- ==============================================

-- 手机号查询索引（登录频繁使用）
CREATE INDEX IF NOT EXISTS idx_users_phone_active
ON users(phone) WHERE is_active = true;

-- 微信OpenID查询索引
CREATE INDEX IF NOT EXISTS idx_users_wechat_openid
ON users(wechat_openid) WHERE wechat_openid IS NOT NULL;

-- 微信UnionID查询索引
CREATE INDEX IF NOT EXISTS idx_users_wechat_unionid
ON users(wechat_unionid) WHERE wechat_unionid IS NOT NULL;

-- 用户角色和状态组合索引
CREATE INDEX IF NOT EXISTS idx_users_role_active_created
ON users(role, is_active, created_at DESC);

-- 学校和年级组合索引（用于统计分析）
CREATE INDEX IF NOT EXISTS idx_users_school_grade
ON users(school, grade_level) WHERE school IS NOT NULL AND grade_level IS NOT NULL;

-- ==============================================
-- 用户会话表索引
-- ==============================================

-- 用户会话查询索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active
ON user_sessions(user_id, is_revoked, expires_at);

-- 访问令牌查询索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_access_token
ON user_sessions(access_token_jti) WHERE is_revoked = false;

-- 刷新令牌查询索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token
ON user_sessions(refresh_token_jti) WHERE is_revoked = false;

-- 设备和IP查询索引（安全分析）
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_ip
ON user_sessions(device_id, ip_address, created_at DESC);

-- ==============================================
-- 作业表索引
-- ==============================================

-- 学科和年级查询索引（最常用查询）
CREATE INDEX IF NOT EXISTS idx_homework_subject_grade_active
ON homework(subject, grade_level, is_active, created_at DESC);

-- 创建者查询索引
CREATE INDEX IF NOT EXISTS idx_homework_creator_template
ON homework(creator_id, is_template, is_active);

-- 作业难度和类型索引
CREATE INDEX IF NOT EXISTS idx_homework_difficulty_type
ON homework(difficulty_level, homework_type, subject);

-- 知识点搜索索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_knowledge_points
ON homework USING GIN(knowledge_points);

-- 截止日期查询索引
CREATE INDEX IF NOT EXISTS idx_homework_deadline
ON homework(deadline) WHERE deadline IS NOT NULL AND is_active = true;

-- 章节查询索引
CREATE INDEX IF NOT EXISTS idx_homework_chapter
ON homework(chapter, subject) WHERE chapter IS NOT NULL;

-- ==============================================
-- 作业提交表索引
-- ==============================================

-- 学生查询索引（学生查看自己的提交）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_student_status
ON homework_submissions(student_id, status, submitted_at DESC);

-- 作业查询索引（教师查看作业的所有提交）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_homework_status
ON homework_submissions(homework_id, status, submitted_at DESC);

-- 学生和作业组合索引（唯一约束辅助）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_student_homework
ON homework_submissions(student_id, homework_id);

-- 提交时间范围查询索引
CREATE INDEX IF NOT EXISTS idx_homework_submissions_submitted_range
ON homework_submissions(submitted_at DESC) WHERE submitted_at IS NOT NULL;

-- 分数查询索引（统计分析）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_score
ON homework_submissions(total_score) WHERE total_score IS NOT NULL;

-- AI审核数据索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_ai_review
ON homework_submissions USING GIN(ai_review_data);

-- 薄弱知识点索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_submissions_weak_points
ON homework_submissions USING GIN(weak_knowledge_points);

-- ==============================================
-- 作业图片表索引
-- ==============================================

-- 提交ID查询索引（最常用）
CREATE INDEX IF NOT EXISTS idx_homework_images_submission_order
ON homework_images(submission_id, display_order);

-- OCR处理状态索引
CREATE INDEX IF NOT EXISTS idx_homework_images_ocr_processed
ON homework_images(is_processed, ocr_processed_at);

-- 主图片查询索引
CREATE INDEX IF NOT EXISTS idx_homework_images_primary
ON homework_images(submission_id, is_primary) WHERE is_primary = true;

-- 文件类型查询索引
CREATE INDEX IF NOT EXISTS idx_homework_images_mime_type
ON homework_images(mime_type, file_size);

-- OCR置信度查询索引（质量分析）
CREATE INDEX IF NOT EXISTS idx_homework_images_ocr_confidence
ON homework_images(ocr_confidence) WHERE ocr_confidence IS NOT NULL;

-- OCR数据搜索索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_images_ocr_data
ON homework_images USING GIN(ocr_data);

-- ==============================================
-- 作业批改表索引
-- ==============================================

-- 提交ID查询索引（一对多关系）
CREATE INDEX IF NOT EXISTS idx_homework_reviews_submission_status
ON homework_reviews(submission_id, status, completed_at DESC);

-- 批改员查询索引
CREATE INDEX IF NOT EXISTS idx_homework_reviews_reviewer_status
ON homework_reviews(reviewer_id, status, created_at DESC) WHERE reviewer_id IS NOT NULL;

-- 批改类型和状态索引
CREATE INDEX IF NOT EXISTS idx_homework_reviews_type_status
ON homework_reviews(review_type, status, started_at);

-- 完成时间查询索引（统计分析）
CREATE INDEX IF NOT EXISTS idx_homework_reviews_completed
ON homework_reviews(completed_at DESC) WHERE completed_at IS NOT NULL;

-- 分数范围查询索引
CREATE INDEX IF NOT EXISTS idx_homework_reviews_score_range
ON homework_reviews(total_score, accuracy_rate) WHERE total_score IS NOT NULL;

-- AI模型版本索引（版本分析）
CREATE INDEX IF NOT EXISTS idx_homework_reviews_ai_model
ON homework_reviews(ai_model_version, ai_confidence_score) WHERE ai_model_version IS NOT NULL;

-- 需要人工审核索引
CREATE INDEX IF NOT EXISTS idx_homework_reviews_manual_needed
ON homework_reviews(needs_manual_review, status) WHERE needs_manual_review = true;

-- 知识点分析索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_reviews_knowledge_analysis
ON homework_reviews USING GIN(knowledge_point_analysis);

-- 问题批改索引（GIN索引用于JSONB）
CREATE INDEX IF NOT EXISTS idx_homework_reviews_question_reviews
ON homework_reviews USING GIN(question_reviews);

-- ==============================================
-- 复合查询索引
-- ==============================================

-- 学生作业完成情况查询（dashboard常用）
CREATE INDEX IF NOT EXISTS idx_student_homework_dashboard
ON homework_submissions(student_id, homework_id, status, submitted_at DESC, total_score);

-- 教师作业管理查询
CREATE INDEX IF NOT EXISTS idx_teacher_homework_management
ON homework(creator_id, subject, grade_level, is_active, created_at DESC, total_submissions);

-- 作业批改工作流查询
CREATE INDEX IF NOT EXISTS idx_homework_review_workflow
ON homework_reviews(submission_id, review_type, status, started_at, completed_at);

-- 学生学习分析查询
CREATE INDEX IF NOT EXISTS idx_student_learning_analysis
ON homework_submissions(student_id, submitted_at DESC, total_score, accuracy_rate)
WHERE total_score IS NOT NULL;

-- ==============================================
-- 全文搜索索引
-- ==============================================

-- 作业标题和描述全文搜索
CREATE INDEX IF NOT EXISTS idx_homework_fulltext_search
ON homework USING GIN(to_tsvector('chinese', coalesce(title, '') || ' ' || coalesce(description, '')));

-- 用户姓名搜索
CREATE INDEX IF NOT EXISTS idx_users_name_search
ON users USING GIN(to_tsvector('chinese', coalesce(name, '') || ' ' || coalesce(nickname, '')));

-- OCR文本全文搜索
CREATE INDEX IF NOT EXISTS idx_homework_images_ocr_fulltext
ON homework_images USING GIN(to_tsvector('chinese', coalesce(ocr_text, '')))
WHERE ocr_text IS NOT NULL;

-- ==============================================
-- 分区表索引（如果使用分区）
-- ==============================================

-- 按时间分区的索引（适用于大数据量场景）
-- CREATE INDEX IF NOT EXISTS idx_homework_submissions_partition_time
-- ON homework_submissions(created_at, student_id)
-- WHERE created_at >= '2024-01-01';

-- ==============================================
-- 索引使用统计和监控
-- ==============================================

-- 创建索引使用统计视图
CREATE OR REPLACE VIEW v_index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    CASE
        WHEN idx_scan = 0 THEN '未使用'
        WHEN idx_scan < 100 THEN '低频使用'
        WHEN idx_scan < 1000 THEN '中频使用'
        ELSE '高频使用'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 输出索引创建完成信息
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname NOT LIKE '%_pkey';

    RAISE NOTICE '✅ 数据库索引优化完成';
    RAISE NOTICE '   - 共创建 % 个自定义索引', index_count;
    RAISE NOTICE '   - B-tree索引：用于等值和范围查询';
    RAISE NOTICE '   - GIN索引：用于JSONB和全文搜索';
    RAISE NOTICE '   - 部分索引：用于条件过滤优化';
    RAISE NOTICE '   - 复合索引：用于多字段组合查询';
    RAISE NOTICE '   - 全文搜索索引：用于中文文本搜索';
    RAISE NOTICE '';
    RAISE NOTICE '💡 使用 SELECT * FROM v_index_usage_stats; 查看索引使用情况';
END $$;
