# 项目概述 - 五好伴学 (Wuhao Tutor)

## 项目目的
基于阿里云百炼智能体的 K12 智能学习支持平台，提供：
- 智能作业批改 (完成度95%)
- 个性化学习问答 
- 全面学情分析服务

## 技术栈
### 后端
- **Python 3.11+** with FastAPI 0.104+
- **SQLAlchemy 2.x** (异步) + PostgreSQL/SQLite
- **Redis** 缓存和会话存储
- **阿里云百炼** AI 服务集成
- **JWT** 认证系统

### 前端
- **Vue 3.4+** with Composition API
- **TypeScript** 严格模式
- **Element Plus** UI 组件库
- **Pinia** 状态管理
- **Vite** 构建工具

### 开发工具
- **uv** Python 包管理
- **Docker** 容器化部署
- **pytest** 测试框架
- **black/flake8** 代码格式化和检查

## 当前状态
- **版本**: 0.4.x (Phase 4 - 智能上下文增强)
- **整体评分**: B+ (良好)
- **架构**: 四层架构 (API → Services → Repositories → Models)
- **生产就绪度**: B- (缺少向量数据库和 RAG 实现)