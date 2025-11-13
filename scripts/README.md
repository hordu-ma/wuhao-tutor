# 管理脚本使用指南

## promote_admin_server.sh

**用途**: 在生产服务器上直接提升用户为管理员角色

**使用方法**:

### 1. 上传脚本到服务器

```bash
scp scripts/promote_admin_server.sh root@121.199.173.244:/opt/wuhao-tutor/scripts/
```

### 2. SSH 登录并执行

```bash
ssh root@121.199.173.244
cd /opt/wuhao-tutor
bash scripts/promote_admin_server.sh
```

**功能说明**:

- 自动从 `.env.production` 加载数据库配置
- 查询用户当前信息
- 更新角色为 `admin`
- 验证更新结果
- 显示所有管理员列表

**安全提示**:

- ⚠️ 仅在生产服务器上执行
- ✅ 操作具有幂等性，可重复执行
- ✅ 不会影响其他用户数据
- ✅ 修改硬编码的手机号后可用于其他用户

**修改目标用户**:
编辑脚本第 5 行的 `PHONE` 变量：

```bash
PHONE="18888333726"  # 改为目标用户手机号
```

---

## create_user.py

**用途**: 交互式创建学生/教师用户（默认角色为 'student'）

**使用方法**:

```bash
python scripts/create_user.py
```

---

## 其他管理工具

### 通过 API 创建管理员

系统已支持通过 Admin API 创建不同角色的用户：

```bash
curl -X POST "https://horsduroot.com/api/v1/admin/users" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13900000000",
    "name": "管理员姓名",
    "role": "admin"
  }'
```

**支持的角色**:

- `student` - 学生（默认）
- `teacher` - 教师
- `admin` - 管理员
