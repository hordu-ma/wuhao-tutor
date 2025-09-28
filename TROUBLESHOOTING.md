# 五好伴学项目故障排除指南

## 🔧 常见问题和解决方案

### 1. 配置相关问题

#### 1.1 CORS配置错误
**问题**: `error parsing value for field "BACKEND_CORS_ORIGINS" from source "DotEnvSettingsSource"`

**原因**: Pydantic Settings 对List类型字段有特殊处理，期望JSON格式或使用自定义验证器

**解决方案**:
```bash
# 方案1：注释掉.env文件中的CORS配置（使用默认值）
# BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 方案2：使用环境变量
export BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

**已修复**: 项目中的配置验证器已支持逗号分隔格式

#### 1.2 环境变量加载失败
**问题**: 配置加载失败或使用了错误的配置

**解决方案**:
```bash
# 确认环境变量设置
export ENVIRONMENT=development
export DEBUG=true

# 或者使用测试环境（不读取.env文件）
export ENVIRONMENT=testing
```

### 2. 导入相关问题

#### 2.1 模块未找到错误
**问题**: `ModuleNotFoundError: No module named 'src'`

**解决方案**:
```bash
# 方案1：使用模块方式运行
python -m src.main

# 方案2：使用uvicorn直接运行
uvicorn src.main:app --reload

# 方案3：设置PYTHONPATH（如果需要）
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2.2 循环导入问题
**问题**: 导入时出现循环依赖错误

**解决方案**:
1. 检查导入顺序
2. 使用延迟导入（在函数内部导入）
3. 将类型提示移到 `TYPE_CHECKING` 块中

### 3. 数据库相关问题

#### 3.1 数据库连接失败
**问题**: 无法连接到数据库

**解决方案**:
```bash
# 开发环境使用SQLite（默认配置）
# 数据库文件：./wuhao_tutor_dev.db

# 测试环境使用内存数据库
export ENVIRONMENT=testing

# 检查数据库文件权限
ls -la wuhao_tutor_dev.db
```

#### 3.2 数据库表不存在
**问题**: 表结构未创建

**解决方案**:
```bash
# 运行数据库初始化脚本（如果有）
python scripts/init_database.py

# 或者删除数据库文件重新创建
rm wuhao_tutor_dev.db
python -c "from src.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. 依赖相关问题

#### 4.1 包未安装
**问题**: 某些依赖包未正确安装

**解决方案**:
```bash
# 使用uv同步依赖
uv sync

# 重新安装所有依赖
uv pip install -r requirements.txt

# 检查虚拟环境
uv venv --python 3.11
source .venv/bin/activate
```

#### 4.2 版本冲突
**问题**: 依赖包版本冲突

**解决方案**:
```bash
# 检查依赖版本
uv pip list

# 更新特定包
uv pip install --upgrade fastapi sqlalchemy

# 重新生成lock文件
uv lock
```

### 5. 服务启动问题

#### 5.1 端口被占用
**问题**: `OSError: [Errno 48] Address already in use`

**解决方案**:
```bash
# 检查端口占用
lsof -i :8000

# 杀死占用进程
kill -9 <PID>

# 或使用不同端口
uvicorn src.main:app --port 8001
```

#### 5.2 权限问题
**问题**: 文件权限不足

**解决方案**:
```bash
# 检查文件权限
ls -la src/

# 修正权限
chmod +x scripts/*.py
chmod 755 src/
```

## 🛠️ 调试工具和脚本

### 诊断脚本
运行综合诊断检查所有模块：

```bash
# 运行诊断脚本
uv run python scripts/diagnose.py

# 预期输出：🟢 所有检查通过
```

### 单独测试模块导入
```python
# 测试单个模块
python -c "import src.main; print('OK')"
python -c "import src.core.config; print('OK')"
python -c "import src.services.bailian_service; print('OK')"
```

### 配置验证
```python
# 验证配置加载
python -c "
from src.core.config import get_settings
settings = get_settings()
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.SQLALCHEMY_DATABASE_URI}')
"
```

### 数据库连接测试
```python
# 测试数据库连接
python -c "
import asyncio
from src.core.database import async_session
from sqlalchemy import text

async def test_db():
    async with async_session() as session:
        result = await session.execute(text('SELECT 1'))
        print('Database OK:', result.scalar())

asyncio.run(test_db())
"
```

## 📝 开发环境设置

### 推荐的开发流程

1. **环境准备**
```bash
# 克隆项目
git clone <repo>
cd wuhao-tutor

# 安装依赖
uv sync

# 设置环境变量
export ENVIRONMENT=development
```

2. **验证安装**
```bash
# 运行诊断脚本
uv run python scripts/diagnose.py

# 启动开发服务器
uv run uvicorn src.main:app --reload
```

3. **IDE配置**
- VSCode: 设置Python解释器为 `.venv/bin/python`
- PyCharm: 配置项目解释器指向虚拟环境

### 环境变量配置

开发环境必需的环境变量：
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

可选的环境变量：
```bash
# 阿里云服务（可选）
ALICLOUD_ACCESS_KEY_ID=your_key
ALICLOUD_ACCESS_KEY_SECRET=your_secret

# 百炼AI服务（可选，用于AI功能）
BAILIAN_API_KEY=sk-your-api-key
```

## 🚨 紧急问题处理

### 完全重置环境
如果遇到无法解决的问题，可以完全重置：

```bash
# 1. 删除虚拟环境
rm -rf .venv

# 2. 删除数据库文件
rm -f *.db

# 3. 重新创建环境
uv sync

# 4. 重新运行诊断
uv run python scripts/diagnose.py
```

### 获取详细错误信息
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 使用Python直接运行获取完整错误信息
python -c "
import traceback
import sys
sys.path.insert(0, '.')
try:
    from src.main import app
    print('✅ 导入成功')
except Exception as e:
    print('❌ 导入失败:')
    traceback.print_exc()
"
```

---

## 📞 联系方式

如果以上解决方案都无效，请提供以下信息：
1. 错误的完整堆栈跟踪
2. 操作系统和Python版本
3. 运行的具体命令
4. 环境变量设置

**项目维护者**: Liguo Ma  
**邮箱**: maliguo@outlook.com