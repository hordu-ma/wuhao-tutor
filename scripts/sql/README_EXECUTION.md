# 生产环境数据库修复说明

## 在生产服务器上执行以下命令：

```bash
# 1. SSH 连接生产服务器
ssh root@121.199.173.244

# 2. 进入项目目录
cd /opt/wuhao-tutor

# 3. 备份数据库
pg_dump -U postgres -d wuhao_tutor > backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# 4. 执行修复 - 选择一种方式：

# 方式 A：使用 Python 脚本（推荐）
python3 scripts/migrations/fix_empty_session_titles.py

# 方式 B：使用 SQL 脚本（快速）
psql -U postgres -d wuhao_tutor -f scripts/sql/03-fix-empty-session-titles.sql

# 5. 验证修复结果
psql -U postgres -d wuhao_tutor -c "SELECT COUNT(*) FROM chat_sessions WHERE title IS NULL OR TRIM(title) = '';"

# 预期结果：count = 0

# 6. 检查后端服务状态
systemctl status wuhao-tutor.service

# 7. 查看后端日志
journalctl -u wuhao-tutor.service -n 50
```

## 验证修复成功的标志：

1. Python/SQL 脚本执行完成，无错误
2. SELECT COUNT 查询返回 0
3. 后端服务运行正常
4. 小程序中历史会话显示摘要而非"新会话"
