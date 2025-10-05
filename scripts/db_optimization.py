"""
数据库索引优化脚本
为作业相关表添加性能优化索引
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# 索引创建SQL列表
INDEX_QUERIES = [
    # HomeworkSubmission表的复合索引
    {
        "name": "idx_submissions_student_created",
        "table": "homework_submissions",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_submissions_student_created 
        ON homework_submissions(student_id, created_at DESC);
        """,
        "description": "学生ID + 创建时间复合索引，优化按学生查询提交历史",
    },
    {
        "name": "idx_submissions_status_created",
        "table": "homework_submissions",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_submissions_status_created 
        ON homework_submissions(status, created_at DESC);
        """,
        "description": "状态 + 创建时间复合索引，优化按状态筛选",
    },
    {
        "name": "idx_submissions_student_status",
        "table": "homework_submissions",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_submissions_student_status 
        ON homework_submissions(student_id, status);
        """,
        "description": "学生ID + 状态复合索引，优化用户状态筛选",
    },
    # HomeworkReview表的索引
    {
        "name": "idx_reviews_submission_status",
        "table": "homework_reviews",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_reviews_submission_status 
        ON homework_reviews(submission_id, status);
        """,
        "description": "提交ID + 批改状态复合索引，优化批改状态查询",
    },
    {
        "name": "idx_reviews_completed_at",
        "table": "homework_reviews",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_reviews_completed_at 
        ON homework_reviews(completed_at DESC) 
        WHERE completed_at IS NOT NULL;
        """,
        "description": "完成时间索引（部分索引），优化批改完成时间查询",
    },
    # Homework表的复合索引
    {
        "name": "idx_homework_subject_grade",
        "table": "homework",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_homework_subject_grade 
        ON homework(subject, grade_level);
        """,
        "description": "学科 + 年级复合索引，优化按学科年级筛选",
    },
    {
        "name": "idx_homework_active_created",
        "table": "homework",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_homework_active_created 
        ON homework(is_active, created_at DESC) 
        WHERE deleted_at IS NULL;
        """,
        "description": "激活状态 + 创建时间复合索引（部分索引），优化活跃作业查询",
    },
    # HomeworkImage表的索引
    {
        "name": "idx_images_submission_order",
        "table": "homework_images",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_images_submission_order 
        ON homework_images(submission_id, image_order);
        """,
        "description": "提交ID + 图片顺序复合索引，优化图片序列查询",
    },
]


def create_indexes():
    """创建所有性能优化索引"""
    print("🔧 开始创建性能优化索引...")

    for index_info in INDEX_QUERIES:
        try:
            print(f"📌 创建索引: {index_info['name']}")
            print(f"   表: {index_info['table']}")
            print(f"   说明: {index_info['description']}")

            # 执行创建索引的SQL
            op.execute(text(index_info["sql"]))
            print(f"   ✅ 成功创建索引: {index_info['name']}")

        except Exception as e:
            print(f"   ❌ 创建索引失败: {index_info['name']} - {e}")

    print("\n✅ 索引创建完成!")


def drop_indexes():
    """删除所有优化索引（用于回滚）"""
    print("🗑️  开始删除优化索引...")

    for index_info in reversed(INDEX_QUERIES):
        try:
            drop_sql = f"DROP INDEX IF EXISTS {index_info['name']};"
            print(f"🔻 删除索引: {index_info['name']}")

            op.execute(text(drop_sql))
            print(f"   ✅ 成功删除索引: {index_info['name']}")

        except Exception as e:
            print(f"   ❌ 删除索引失败: {index_info['name']} - {e}")

    print("\n✅ 索引删除完成!")


def analyze_tables():
    """分析表统计信息以优化查询计划"""
    tables = ["homework", "homework_submissions", "homework_reviews", "homework_images"]

    print("📊 开始分析表统计信息...")

    for table in tables:
        try:
            analyze_sql = f"ANALYZE {table};"
            print(f"🔍 分析表: {table}")

            op.execute(text(analyze_sql))
            print(f"   ✅ 成功分析表: {table}")

        except Exception as e:
            print(f"   ❌ 分析表失败: {table} - {e}")

    print("\n✅ 表分析完成!")


def get_index_usage_report():
    """获取索引使用情况报告"""
    report_sql = """
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_tup_read,
        idx_tup_fetch,
        idx_scan
    FROM pg_stat_user_indexes 
    WHERE schemaname = 'public' 
      AND tablename IN ('homework', 'homework_submissions', 'homework_reviews', 'homework_images')
    ORDER BY tablename, idx_scan DESC;
    """

    try:
        print("📈 索引使用情况报告:")
        result = op.get_bind().execute(text(report_sql))

        print(f"{'表名':<20} {'索引名':<30} {'扫描次数':<10} {'读取次数':<10}")
        print("-" * 80)

        for row in result:
            print(f"{row[1]:<20} {row[2]:<30} {row[5]:<10} {row[3]:<10}")

    except Exception as e:
        print(f"❌ 获取索引报告失败: {e}")


if __name__ == "__main__":
    print("🗄️  数据库性能优化工具")
    print("请在Alembic迁移文件中使用这些函数")
    print("\n可用函数:")
    print("- create_indexes(): 创建性能优化索引")
    print("- drop_indexes(): 删除优化索引")
    print("- analyze_tables(): 分析表统计信息")
    print("- get_index_usage_report(): 获取索引使用报告")
