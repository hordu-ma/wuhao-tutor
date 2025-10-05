# 任务完成后的必执行步骤

## 代码质量检查
```bash
# 1. 格式化代码
uv run black .

# 2. 代码检查
uv run flake8 .

# 3. 类型检查
uv run mypy src

# 4. 运行测试
uv run pytest tests/ --cov=src --cov-report=term-missing

# 或使用 Makefile 组合命令
make lint    # black + flake8 + mypy
make test    # pytest with coverage
```

## 数据库迁移 (如果修改了模型)
```bash
# 1. 生成迁移文件
uv run alembic revision --autogenerate -m "描述修改内容"

# 2. 应用迁移
uv run alembic upgrade head

# 3. 验证迁移
uv run python scripts/diagnose.py
```

## 功能验证
```bash
# 1. 启动开发服务器
./scripts/start-dev.sh

# 2. 运行 API 集成测试
uv run python scripts/test_api.py

# 3. 检查服务状态
make monitor
```

## Git 提交流程
```bash
# 1. 查看修改文件
git status

# 2. 添加修改 (选择性)
git add src/services/new_service.py
git add tests/services/test_new_service.py

# 3. 提交 (遵循约定)
git commit -m "feat(services): 添加 KnowledgeContextBuilder 服务

- 实现薄弱知识点分析算法
- 添加学习偏好提取功能  
- 完善单元测试覆盖"

# 4. 推送
git push origin feature/knowledge-context
```

## 性能检查 (如适用)
```bash
# 数据库查询性能
uv run python scripts/performance_monitor.py

# 内存和 CPU 使用
ps aux | grep python
```

## 文档更新 (如需要)
```bash
# 更新 API 文档 (自动生成)
# 访问 http://localhost:8000/docs

# 更新 README 或相关文档
# 特别是添加新功能或 API 端点时
```

## 错误检查清单
- [ ] 代码格式化通过 (black)
- [ ] 静态检查通过 (flake8, mypy)  
- [ ] 单元测试通过 (pytest)
- [ ] 集成测试通过 (API tests)
- [ ] 数据库迁移正确应用
- [ ] 服务正常启动
- [ ] Git 提交消息符合规范
- [ ] 相关文档已更新

## 优先级顺序
1. **Critical**: 测试通过、服务启动
2. **High**: 代码检查、类型安全
3. **Medium**: 性能验证、文档更新  
4. **Low**: 代码优化、注释完善

> **注意**: 如果是 P0 级任务，必须完成 Critical 和 High 优先级检查