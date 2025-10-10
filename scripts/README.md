# 部署脚本文档

这个目录包含了五好伴学(Wuhao Tutor)项目的部署自动化脚本。

## 📁 目录结构

```
scripts/
├── README.md                          # 本文档
├── deploy_to_production.sh            # 一键生产环境部署脚本 ⭐
├── pre_deploy_check.sh               # 部署前检查脚本
├── build_frontend.sh                 # 前端构建脚本
└── deploy/
    ├── rollback.sh                   # 生产环境回滚脚本
    └── health_check.sh               # 健康检查脚本(未来)
```

## 🚀 主要部署脚本

### 1. 一键部署脚本 (推荐)

**使用方法:**

```bash
./scripts/deploy_to_production.sh
```

**功能特性:**

- ✅ **三阶段自动化部署**: 本地检查 → 远程同步 → 健康验证
- ✅ **代码安全检查**: Python 语法检查、Git 状态验证
- ✅ **前端自动构建**: TypeScript 类型检查 + Vite 生产构建
- ✅ **智能文件同步**: 仅同步必要文件，排除开发文件
- ✅ **服务平滑重启**: Python 后端 + Nginx 前端同步更新
- ✅ **健康状态验证**: API 响应检查 + 服务状态确认

**部署流程详解:**

1. **阶段 1: 本地准备**

   - 检查关键文件完整性
   - 验证 Python 代码语法
   - 构建前端生产版本
   - 用户确认部署

2. **阶段 2: 服务器操作**

   - 同步后端代码 (`src/` → `/opt/wuhao-tutor/src/`)
   - 同步前端构建产物 (`frontend/dist/` → `/var/www/wuhao-tutor/`)
   - 同步配置和依赖 (`.env.production`, `requirements.prod.txt`)
   - 更新 Python 依赖包
   - 重启 wuhao-tutor 服务
   - 重新加载 Nginx 配置

3. **阶段 3: 部署验证**
   - 检查 systemd 服务状态
   - 验证 API 健康端点响应
   - 输出访问地址和监控命令

**目标服务器**: `root@121.199.173.244`  
**部署目录**: `/opt/wuhao-tutor`  
**前端目录**: `/var/www/wuhao-tutor`

### 2. 单独执行脚本

#### 部署前检查

```bash
./scripts/pre_deploy_check.sh
```

- 验证关键文件存在
- 检查 Git 仓库状态
- Python 语法检查

#### 前端构建

```bash
./scripts/build_frontend.sh
```

- npm 依赖安装
- TypeScript 类型检查
- Vite 生产构建

#### 生产环境回滚

```bash
./scripts/deploy/rollback.sh
```

- Git 版本回滚
- 前端备份恢复
- 服务重启

## 🔧 配置要求

### 本地环境

- **Node.js**: ≥ 18.0.0 (前端构建)
- **Python**: ≥ 3.10 (代码检查)
- **uv**: Python 依赖管理
- **Git**: 版本控制
- **SSH**: 无密码访问生产服务器

### 生产服务器

- **操作系统**: Ubuntu 22.04 LTS
- **Python**: 3.10 + venv 虚拟环境
- **服务管理**: systemd (wuhao-tutor.service)
- **Web 服务器**: Nginx (HTTPS + 反向代理)
- **数据库**: PostgreSQL (阿里云 RDS)
- **缓存**: Redis (阿里云)

### 环境配置文件

- **开发环境**: `.env` (SQLite + 本地配置)
- **生产环境**: `.env.production` (PostgreSQL + OSS + Redis)

## 📊 监控和运维

### 实时日志监控

```bash
# 查看应用日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor -f'

# 查看Nginx日志
ssh root@121.199.173.244 'tail -f /var/log/nginx/access.log'

# 查看系统资源
ssh root@121.199.173.244 'htop'
```

### 服务状态检查

```bash
# 服务状态
ssh root@121.199.173.244 'systemctl status wuhao-tutor'

# API健康检查
curl -k https://121.199.173.244/api/v1/files/health

# 前端访问
open https://121.199.173.244
```

### 备份和恢复

```bash
# 数据库备份（PostgreSQL）
ssh root@121.199.173.244 'pg_dump -h pgm-bp1ce0sp88j6ha90.pg.rds.aliyuncs.com -U horsdu_ma wuhao_tutor > backup_$(date +%Y%m%d).sql'

# 代码备份
ssh root@121.199.173.244 'tar -czf /opt/backup/code_$(date +%Y%m%d).tar.gz /opt/wuhao-tutor'
```

## ⚠️ 注意事项

### 部署安全

1. **环境变量保护**: 生产环境敏感信息存储在 `.env.production`
2. **网络安全**: 仅开放必要端口 (80, 443, 22)
3. **SSL 证书**: 自签名证书，定期更新

### 常见问题

**问题 1: 部署失败 - 权限错误**

```bash
# 检查SSH密钥配置
ssh root@121.199.173.244 'whoami'

# 检查目录权限
ssh root@121.199.173.244 'ls -la /opt/wuhao-tutor'
```

**问题 2: 前端构建失败**

```bash
# 清理node_modules重试
cd frontend && rm -rf node_modules package-lock.json
npm install
```

**问题 3: 服务启动失败**

```bash
# 检查详细错误日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor -n 50'

# 检查虚拟环境
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && python -c "import sys; print(sys.version)"'
```

**问题 4: 数据库连接失败**

```bash
# 检查生产配置
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && cat .env | grep POSTGRES'

# 测试数据库连接
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && python -c "from src.core.database import engine; print(\"DB OK\")"'
```

## 🔄 版本历史

- **v3.0** (2025-10-10): 添加图片上传 API 修复，优化前端集成
- **v2.0** (2025-10-08): 一键部署脚本，三阶段自动化流程
- **v1.0** (2025-10-01): 基础部署脚本，手动操作

## 📧 技术支持

遇到部署问题可以：

1. 查看详细日志排查
2. 使用回滚脚本恢复
3. 联系开发团队技术支持

---

**🌟 最佳实践**: 部署前在开发环境充分测试，使用一键部署脚本确保一致性，定期备份生产数据。
