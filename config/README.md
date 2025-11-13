# config/ 目录

## 📁 目录结构

```
config/
└── templates/         # 配置模板和默认值
```

## 📝 目录说明

### config/ 的角色

**用途**：存储应用程序的各种配置文件和模板

**与 pyproject.toml 的关系**：

- `pyproject.toml`：Python 项目的元数据和依赖配置（全局）
- `config/`：应用特定的业务配置和模板（运行时）

### templates/

**用途**：配置模板和默认值

- **类型**：配置文件模板（YAML、JSON、Jinja2 等）
- **来源**：开发者定义的默认配置
- **Git 跟踪**：✅ 是（这些是项目必需的配置）
- **修改频率**：低（仅当需要调整默认值时）
- **常见使用**：
  - 邮件模板
  - 报告模板
  - API 响应模板
  - 数据导出模板

## 🔧 配置加载优先级

```
项目默认值 (config/templates/)
        ↓ (低优先级)
   环境变量 (.env)
        ↓
   运行时配置 (pyproject.toml)
        ↓ (高优先级)
   应用配置对象
```

## 🛠️ 使用示例

```python
# src/core/config.py 中的配置加载
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 从环境变量或 .env 文件加载
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "your-secret-key"

    # 从配置文件加载
    email_template_path: Path = Path("config/templates/email.jinja2")

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 📌 最佳实践

- ✅ 将默认配置放在 `config/templates/`
- ✅ 使用环境变量覆盖生产配置（见 `.env.example`）
- ❌ 不要在 `config/` 中提交敏感信息（密钥、密码）
- 📝 为每个配置文件添加注释说明
- 🔒 在 CI/CD 中注入生产配置

## 🔄 配置流程

```
初始化
  ↓
读取 config/templates/ (默认值)
  ↓
读取 .env (环境变量覆盖)
  ↓
读取运行时参数 (命令行参数)
  ↓
应用程序使用最终配置
```

## 📂 添加新配置文件

如需添加新配置：

```bash
# 1. 创建配置文件
touch config/templates/my_config.yaml

# 2. 在 pyproject.toml 或 .env 中定义路径
MY_CONFIG_PATH=config/templates/my_config.yaml

# 3. 在应用代码中加载
from pathlib import Path
config = Path(os.getenv("MY_CONFIG_PATH")).read_text()
```

---

**更新**：2025-11-13

**相关文件**：

- `pyproject.toml` - Python 项目配置
- `.env.example` - 环境变量模板
- `src/core/config.py` - 配置加载逻辑
