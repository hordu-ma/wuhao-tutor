# 用户角色与权限系统完整指南

**最后更新**: 2025-10-04  
**状态**: 生产就绪

---

## 📋 系统概述

本系统实现了一个完整的微信小程序用户角色与权限管理系统，包含角色管理、权限控制、路由守卫、动态TabBar等核心功能。系统支持学生、家长、教师三种角色，每种角色拥有不同的权限和界面布局。

## 🏗️ 系统架构

```
用户角色系统
├── 认证管理 (AuthManager)            # 用户登录和Token管理
├── 角色管理 (RoleManager)            # 角色切换和状态管理
├── 权限管理 (PermissionManager)      # 权限检查和验证
├── 路由守卫 (RouteGuard)             # 页面访问控制
├── TabBar管理 (TabBarManager)        # 动态TabBar配置
├── 页面守卫管理 (PageGuardManager)   # 页面级权限控制
└── 角色TabBar集成 (RoleTabBarIntegration)  # 角色与TabBar联动
```

### 权限层级

```
用户认证层 (登录状态验证)
    ↓
角色权限层 (学生/家长/教师)
    ↓
页面访问权限层 (页面级控制)
    ↓
功能操作权限层 (功能级控制)
    ↓
API调用权限层 (接口级控制)
    ↓
敏感操作确认层 (二次确认)
```

---

## 📁 核心组件

### 1. 认证管理器 (`utils/auth.js`)
- 微信小程序登录集成
- Token管理和自动刷新
- 用户会话状态检查
- 登录状态持久化

### 2. 角色管理器 (`utils/role-manager.js`)
- 三种用户角色定义（学生/家长/教师）
- 角色切换功能实现
- 角色配置管理
- 角色状态同步

### 3. 权限管理器 (`utils/permission-manager.js`)
- 细粒度权限定义（40+权限类型）
- 角色权限映射配置
- 动态权限检查
- 权限缓存机制

### 4. 路由守卫 (`utils/route-guard.js`)
- 登录状态检查
- 页面级权限验证
- 角色访问控制
- 自动重定向处理

### 5. TabBar管理器 (`utils/tabbar-manager.js`)
- 管理角色专属的TabBar配置
- 动态更新TabBar样式和项目
- 控制TabBar徽标和提示

### 6. 页面守卫管理器 (`utils/page-guard-manager.js`)
- 增强页面权限守卫
- 功能级权限守卫
- API权限守卫
- 敏感操作确认守卫

### 7. 角色TabBar集成器 (`utils/role-tabbar-integration.js`)
- 统一管理角色切换和TabBar更新
- 处理用户登录/登出状态
- 协调各种系统组件

---

## 🎭 角色配置详情

### 👨‍🎓 学生角色 (Student)

**主要功能**：
- 查看和提交作业
- AI问答互动
- 查看个人学习报告
- 个人信息管理

**权限列表**：
```javascript
permissions: [
  'homework.view',      // 查看作业
  'homework.submit',    // 提交作业
  'chat.ask',           // AI问答
  'analysis.view_self', // 查看个人报告
  'profile.view_self',  // 个人信息
  'file.upload',        // 文件上传
  'export.own_data'     // 导出数据
]
```

**TabBar配置**：
```javascript
{
  color: '#999999',
  selectedColor: '#1890ff', // 蓝色主题
  list: [
    { pagePath: 'pages/index/index', text: '首页' },
    { pagePath: 'pages/homework/list/index', text: '作业' },
    { pagePath: 'pages/chat/index/index', text: '问答' },
    { pagePath: 'pages/analysis/report/index', text: '报告' },
    { pagePath: 'pages/profile/index/index', text: '我的' }
  ]
}
```

### 👨‍👩‍👧‍👦 家长角色 (Parent)

**主要功能**：
- 查看孩子学习情况
- 监控作业完成情况
- 查看学习进度分析
- 接收学习通知

**权限列表**：
```javascript
permissions: [
  'homework.view_child',   // 查看孩子作业
  'analysis.view_child',   // 查看孩子学情
  'profile.view_family',   // 家庭信息
  'stats.view_child',      // 孩子统计
  'export.child_data',     // 导出孩子数据
  'notification.receive'   // 接收通知
]
```

**TabBar配置**：
```javascript
{
  color: '#999999',
  selectedColor: '#52c41a', // 绿色主题
  list: [
    { pagePath: 'pages/index/index', text: '首页' },
    { pagePath: 'pages/analysis/progress/index', text: '学情' },
    { pagePath: 'pages/homework/list/index', text: '作业' },
    { pagePath: 'pages/profile/index/index', text: '我的' }
  ]
}
```

### 👨‍🏫 教师角色 (Teacher)

**主要功能**：
- 创建和管理作业
- 批改学生作业
- 查看班级分析报告
- 管理学生信息

**权限列表**：
```javascript
permissions: [
  'homework.view_all',     // 查看所有作业
  'homework.correct',      // 批改作业
  'homework.manage',       // 管理作业
  'homework.create',       // 创建作业
  'analysis.view_class',   // 班级分析
  'user.manage_students',  // 管理学生
  'notification.send'      // 发送通知
]
```

**TabBar配置**：
```javascript
{
  color: '#999999',
  selectedColor: '#faad14', // 橙色主题
  list: [
    { pagePath: 'pages/index/index', text: '首页' },
    { pagePath: 'pages/homework/list/index', text: '作业' },
    { pagePath: 'pages/analysis/report/index', text: '分析' },
    { pagePath: 'pages/profile/index/index', text: '我的' }
  ]
}
```

---

## 🚀 快速开始

### 1. 系统初始化

在 `app.js` 中初始化角色TabBar系统：

```javascript
const { roleTabBarIntegration } = require('./utils/role-tabbar-integration.js');

App({
  async onLaunch() {
    // 初始化角色TabBar系统
    await roleTabBarIntegration.initialize();
  }
});
```

### 2. 用户登录

```javascript
// 登录成功后
const userRole = await authManager.getUserRole();
await roleTabBarIntegration.handleLogin(userRole);
```

### 3. 角色切换

```javascript
// 在角色选择页面
const result = await roleTabBarIntegration.switchRole('teacher', {
  showConfirmDialog: true,
  showSuccessToast: true,
  autoNavigate: true,
  updateTabBar: true
});

if (result.success) {
  console.log('角色切换成功:', result.toRole);
}
```

### 4. 用户登出

```javascript
await roleTabBarIntegration.handleLogout();
```

---

## 🛡️ 权限控制使用

### 1. 页面级权限控制

使用守卫包装器保护页面：

```javascript
const { enhancedPageGuard } = require('../utils/enhanced-page-guard.js');

// 方式1：使用守卫包装器
const guardedPage = enhancedPageGuard.createGuardedPage({
  data: {},
  onLoad() {
    // 页面逻辑
  }
}, 'pages/homework/list/index');

// 方式2：使用装饰器
const { requirePermissions } = require('../utils/enhanced-page-guard.js');

const protectedPage = requirePermissions(['homework.view'], ['teacher'])({
  data: {},
  onLoad() {
    // 只有教师角色且拥有homework.view权限才能访问
  }
});
```

**页面权限配置示例**：

```javascript
const PAGE_PERMISSION_CONFIG = {
  'pages/homework/manage/index': {
    permissions: ['homework.manage'],
    roles: ['teacher'],
    requireLogin: true,
    description: '作业管理页面'
  }
};
```

### 2. 功能模块权限验证

检查功能级别的权限：

```javascript
const { featurePermissionGuard } = require('../utils/feature-permission-guard.js');

// 检查功能权限
async function submitHomework() {
  const result = await featurePermissionGuard.checkFeaturePermission('homework.submit', {
    homeworkId: 'hw_123'
  });
  
  if (!result.success) {
    featurePermissionGuard.handlePermissionFailure(result);
    return;
  }
  
  // 执行提交逻辑
}

// 便捷方法
const canSubmit = await featurePermissionGuard.canSubmitHomework('hw_123');
```

**功能权限配置示例**：

```javascript
const FEATURE_PERMISSION_CONFIG = {
  'homework.submit': {
    permission: 'homework.submit',
    roles: ['student'],
    conditions: {
      timeRestriction: '06:00-23:00', // 时间限制
      maxDaily: 10                    // 每日限制
    },
    errorMessage: '您没有提交作业的权限',
    sensitive: true                   // 标记为敏感操作
  }
};
```

### 3. API调用权限管理

保护API调用：

```javascript
const { apiPermissionGuard } = require('../utils/api-permission-guard.js');

// 检查API权限
async function callAPI() {
  const result = await apiPermissionGuard.checkApiPermission('POST', '/homework', {
    body: homeworkData
  });
  
  if (!result.success) {
    console.error('API权限检查失败:', result.message);
    return;
  }
  
  // 执行API调用
}

// 使用拦截器（自动检查）
apiPermissionGuard.setupInterceptors();
```

**API权限配置示例**：

```javascript
const API_PERMISSION_CONFIG = {
  'POST /homework': {
    permission: 'homework.create',
    roles: ['teacher'],
    description: '创建作业'
  },
  'DELETE /homework/:id': {
    permission: 'homework.delete',
    roles: ['teacher', 'student'],
    description: '删除作业',
    sensitive: true  // 敏感操作标记
  }
};
```

### 4. 敏感操作二次确认

对于敏感操作进行二次确认：

```javascript
const { sensitiveOperationGuard } = require('../utils/sensitive-operation-guard.js');

// 敏感操作确认
async function deleteHomework(homeworkId) {
  const result = await sensitiveOperationGuard.confirmSensitiveOperation(
    'homework.delete',
    {
      homeworkId,
      homeworkTitle: '数学作业1',
      ownerId: 'teacher_123'
    }
  );
  
  if (!result.success) {
    console.log('用户取消了删除操作');
    return;
  }
  
  // 执行删除逻辑
}
```

**敏感操作配置**：
- **简单确认**: 普通对话框确认
- **密码确认**: 需要输入密码验证
- **理由确认**: 需要填写操作理由

---

## 🎨 TabBar徽标管理

### 显示徽标

```javascript
// 显示红点提示
tabBarManager.showRedDot(index);

// 显示数字徽标
tabBarManager.setBadge(index, '5');

// 隐藏徽标
tabBarManager.hideRedDot(index);
tabBarManager.removeBadge(index);
```

### 自动更新徽标

```javascript
// 系统会根据角色自动更新徽标
await roleTabBarIntegration.updateBadges();

// 学生：显示新作业、AI回复等
// 家长：显示新学习报告等  
// 教师：显示待批改作业数量等
```

---

## 🔄 系统工作流程

### 1. 用户登录流程

```
用户打开小程序
    ↓
检查登录状态
    ↓
未登录 → 跳转登录页面 → 微信授权登录
    ↓
登录成功 → 获取用户角色 → 初始化权限和TabBar
    ↓
跳转到角色对应的首页
```

### 2. 角色切换流程

```
用户进入角色选择页面
    ↓
选择新角色 → 显示确认对话框
    ↓
确认切换 → 更新后端角色信息
    ↓
更新本地状态 → 更新TabBar配置
    ↓
跳转到新角色首页
```

### 3. 页面访问流程

```
用户访问页面
    ↓
路由守卫检查 → 登录状态验证
    ↓
权限检查 → 角色权限验证
    ↓
权限通过 → 加载页面内容
    ↓
权限不足 → 显示提示并重定向
```

---

## 📱 页面导航处理

### TabBar页面导航

```javascript
// 如果目标页面在TabBar中，使用switchTab
wx.switchTab({
  url: '/pages/homework/list/index'
});
```

### 非TabBar页面导航

```javascript
// 如果目标页面不在TabBar中，使用其他导航方式
wx.navigateTo({
  url: '/pages/homework/detail/index?id=123'
});
```

### 角色主页导航

```javascript
// 系统会自动检测主页是否在TabBar中
// 并选择合适的导航方式
navigateToRoleHome(newRole);
```

---

## 🔧 系统状态管理

### 获取当前状态

```javascript
const state = roleTabBarIntegration.getCurrentState();
console.log('当前角色:', state.currentRole);
console.log('TabBar状态:', state.tabBarState);
console.log('是否初始化:', state.isInitialized);
```

### 权限缓存

```javascript
// 权限检查结果会自动缓存
// 提高性能并减少重复检查
const canAccess = await permissionManager.checkPageAccess(pagePath);
```

---

## 📝 配置文件说明

### 权限配置文件 (`utils/permission-config.js`)

定义所有权限类型、角色权限映射和页面权限配置。

### TabBar配置

每个角色的TabBar配置包含：
- 颜色配置（默认色和选中色）
- TabBar项目列表
- 图标配置
- 页面路径

---

## 🎯 最佳实践

1. **总是使用权限守卫保护敏感页面**
2. **在执行重要操作前检查权限**
3. **为敏感操作添加二次确认**
4. **合理设置权限缓存时间**
5. **及时清理过期的权限缓存**
6. **使用角色TabBar集成器统一管理状态**

---

## 🔍 故障排查

### 常见问题

1. **TabBar未更新** - 检查角色切换是否成功，调用 `roleTabBarIntegration.updateTabBar()`
2. **权限检查失败** - 确认用户角色和权限配置正确
3. **页面访问被拒绝** - 检查页面权限配置和用户角色
4. **导航异常** - 确认目标页面是否在TabBar中，使用正确的导航方法

---

## 📚 相关文档

- **API集成指南**: `api-integration.md`
- **网络架构**: `network-architecture.md`
- **权限配置**: `../utils/permission-config.js`
- **测试文档**: `../tests/permission-system-test.js`

---

**维护者**: Liguo Ma <maliguo@outlook.com>  
**最后更新**: 2025-10-04
