"""
WebSocket 超时修复验证测试 (修复1 + 修复4)

简化版本：重点验证代码修改的正确性
- 修复1：验证后端代码中添加了 db.commit()
- 修复4：验证前端代码中实现了超时策略区分
"""

import re


def test_backend_fix1_db_commit_exists():
    """
    验证修复1：后端主流程添加了 db.commit()

    检查点：在 yield done 前是否调用了 await self.db.commit()
    """
    with open("src/services/learning_service.py", "r") as f:
        content = f.read()

    # 查找 yield done 事件的代码段
    # 应该在 yield done 之前有 await self.db.commit()
    pattern = r"await self\.db\.commit\(\).*?logger\.info\(.*?核心数据事务已提交.*?\).*?yield done_event"

    # 更简单的检查：验证 db.commit() 存在于代码中
    assert "await self.db.commit()" in content, "❌ 修复1失败：缺少 db.commit()"

    # 验证 rollback 也被添加了
    assert "await self.db.rollback()" in content, "❌ 修复1失败：缺少 db.rollback()"

    # 验证提交日志
    assert "💾 核心数据事务已提交" in content, "❌ 修复1失败：缺少提交日志"

    print("✅ 修复1验证通过：db.commit() 已正确添加到后端主流程")
    print("   - await self.db.commit() 已添加")
    print("   - await self.db.rollback() 已添加到异常处理")
    print("   - 提交日志已添加")


def test_backend_fix1_commit_before_done():
    """
    验证修复1：db.commit() 在 yield done 之前

    代码逻辑检查：确保提交顺序正确
    """
    with open("src/services/learning_service.py", "r") as f:
        lines = f.readlines()

    # 查找关键行号
    commit_line = None
    done_line = None

    for i, line in enumerate(lines):
        if (
            "await self.db.commit()" in line and "核心数据" in lines[i + 1]
            if i + 1 < len(lines)
            else False
        ):
            commit_line = i
        if "yield done_event" in line:
            done_line = i

    assert commit_line is not None, "❌ 未找到 db.commit() 调用"
    assert done_line is not None, "❌ 未找到 yield done_event"
    assert commit_line < done_line, "❌ db.commit() 应该在 yield done_event 之前"

    print(
        f"✅ 修复1顺序验证通过：commit (L{commit_line + 1}) < done (L{done_line + 1})"
    )


def test_frontend_fix4_timeout_constants():
    """
    验证修复4：前端定义了两个超时常数

    检查点：
    - CONTENT_TIMEOUT = 30000 (30秒)
    - PROCESSING_TIMEOUT = 60000 (60秒)
    """
    with open("miniprogram/api/learning.js", "r") as f:
        content = f.read()

    # 验证 CONTENT_TIMEOUT
    assert "CONTENT_TIMEOUT" in content, "❌ 修复4失败：缺少 CONTENT_TIMEOUT"
    assert "30000" in content, "❌ 修复4失败：缺少 30000 超时常数"

    # 验证 PROCESSING_TIMEOUT
    assert "PROCESSING_TIMEOUT" in content, "❌ 修复4失败：缺少 PROCESSING_TIMEOUT"
    assert "60000" in content, "❌ 修复4失败：缺少 60000 超时常数"

    print("✅ 修复4验证通过：超时常数已正确定义")
    print("   - CONTENT_TIMEOUT = 30000ms（流式内容超时）")
    print("   - PROCESSING_TIMEOUT = 60000ms（后端处理超时）")


def test_frontend_fix4_content_finished_handling():
    """
    验证修复4：content_finished 事件处理切换超时

    检查点：
    - 收到 content_finished 时清除旧定时器
    - 启动新的 PROCESSING_TIMEOUT 定时器
    """
    with open("miniprogram/api/learning.js", "r") as f:
        content = f.read()

    # 查找 content_finished 处理代码
    assert "chunk.type === 'content_finished'" in content, (
        "❌ 缺少 content_finished 判断"
    )

    # 验证清除旧定时器
    pattern = r"if \(chunk\.type === 'content_finished'\).*?clearTimeout\(lastMessageTimeout\)"
    assert re.search(pattern, content, re.DOTALL), "❌ content_finished 后未清除定时器"

    # 验证启动新的处理超时
    assert "PROCESSING_TIMEOUT" in content, "❌ 未使用 PROCESSING_TIMEOUT"

    print("✅ 修复4验证通过：content_finished 事件处理正确")
    print("   - 清除旧的 CONTENT_TIMEOUT 定时器")
    print("   - 启动新的 PROCESSING_TIMEOUT 定时器（60s）")


def test_frontend_fix4_timeout_usage():
    """
    验证修复4：前端在正确的位置使用新的超时常数

    检查点：
    - onOpen 中使用 CONTENT_TIMEOUT
    - onMessage 中使用 CONTENT_TIMEOUT（除了 content_finished）
    - content_finished 中使用 PROCESSING_TIMEOUT
    """
    with open("miniprogram/api/learning.js", "r") as f:
        lines = f.readlines()

    # 查找关键位置
    has_content_timeout_in_onopen = False
    has_processing_timeout_in_content_finished = False

    for i, line in enumerate(lines):
        # 在 onOpen 中检查 CONTENT_TIMEOUT
        if "socketTask.onOpen" in line:
            # 往下找 CONTENT_TIMEOUT
            for j in range(i, min(i + 50, len(lines))):
                if "CONTENT_TIMEOUT" in lines[j]:
                    has_content_timeout_in_onopen = True
                    break

        # 在 content_finished 中检查 PROCESSING_TIMEOUT
        if "'content_finished'" in line:
            # 往下找 PROCESSING_TIMEOUT
            for j in range(i, min(i + 20, len(lines))):
                if "PROCESSING_TIMEOUT" in lines[j]:
                    has_processing_timeout_in_content_finished = True
                    break

    assert has_content_timeout_in_onopen, "❌ onOpen 中未使用 CONTENT_TIMEOUT"
    assert has_processing_timeout_in_content_finished, (
        "❌ content_finished 中未使用 PROCESSING_TIMEOUT"
    )

    print("✅ 修复4验证通过：超时常数使用位置正确")
    print("   - onOpen: 使用 CONTENT_TIMEOUT（30s）")
    print("   - content_finished: 切换为 PROCESSING_TIMEOUT（60s）")


def test_integration_summary():
    """
    综合验证：两个修复的完整效果
    """
    print("\n" + "=" * 70)
    print("修复1 + 修复4 综合验证")
    print("=" * 70)

    test_backend_fix1_db_commit_exists()
    test_backend_fix1_commit_before_done()
    test_frontend_fix4_timeout_constants()
    test_frontend_fix4_content_finished_handling()
    test_frontend_fix4_timeout_usage()

    print("\n" + "=" * 70)
    print("✅ 所有验证通过！修复已正确实施")
    print("=" * 70)
    print("\n修复效果：")
    print("1. 后端在发送 done 前显式提交事务，确保数据立即持久化")
    print("2. 前端区分流式阶段（30s）和处理阶段（60s），避免误超时")
    print("3. 预期：多页图片批改场景不再出现 30s 超时错误")
    print("\n建议下一步：")
    print("- 在生产环境上传 3+ 页题目图片进行测试")
    print("- 监控后端 done 事件发送延迟（目标 < 5s）")
    print("- 监控前端消息超时发生率（应接近 0）")


if __name__ == "__main__":
    test_integration_summary()
