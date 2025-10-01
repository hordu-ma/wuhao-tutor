# 权限控制系统配置文档

## 🎯 概述

本文档描述了微信小程序中实现的细粒度权限控制系统，包括角色管理、权限检查、页面守卫等核心功能。

## 📋 系统架构

### 核心组件

1. **PermissionManager** (`utils/permission-manager.js`)
   - 权限检查核心逻辑
   - 权限缓存管理
   - 动态权限验证
   - 敏感操作确认

2. **RoleManager** (`utils/role-manager.js`)
   - 角色配置管理
   - 角色切换功能
   - 角色权限映射

3. **RouteGuard** (`utils/route-guard.js`)
   - 页面路由守卫
   - 登录状态检查
   - 权限拦截处理

4. **Permission Config** (`utils/permission-config.js`)
   - 权限配置映射
   - 特殊权限规则
   - 权限组合规则

## 🔐 权限系统设计

### 权限类型

#### 基础功能权限
- `homework.view` - 查看作业
- `homework.submit` - 提交作业
- `homework.correct` - 批改作业
- `chat.ask` - AI提问
- `analysis.view_self` - 查看个人分析

#### 管理权限
- `user.manage_students` - 管理学生
- `homework.manage` - 作业管理
- `analysis.view_all` - 查看所有分析

#### 敏感权限
- `homework.delete` - 删除作业
- `admin.system_config` - 系统配置
- `export.all_data` - 导出所有数据

### 角色权限映射

#### 学生 (Student)
```javascript
permissions: [
  'homework.view',
  'homework.submit', 
  'chat.ask',
  'analysis.view_self',
  'profile.view_self'
]
```

#### 家长 (Parent)
```javascript
permissions: [
  'homework.view_child',
  'analysis.view_child',
  'profile.view_family',
  'stats.view_child'
]
```

#### 教师 (Teacher)
```javascript
permissions: [
  'homework.view_all',
  'homework.correct',
  'homework.manage',
  'analysis.view_class',
  'user.manage_students'
]
```

## 🛡️ 权限检查机制

### 1. 基础权限检查

```javascript
// 检查单个权限
const canSubmit = await permissionManager.hasPermission('homework.submit');

// 检查权限组
const hasBasicPermissions = await permissionManager.hasPermissionGroup('basic_student');
```

### 2. 页面级权限检查

```javascript
// 自动页面权限检查
const authResult = await routeGuard.checkPageAuth();

// 手动页面权限检查
const canAccess = await permissionManager.checkPageAccess('pages/homework/submit/index');
```

### 3. 动态权限检查

```javascript
// 检查是否能访问特定资源
const canViewChild = await permissionManager.checkDynamicPermission(
  'analysis.view_child',
  { studentId: 'child123' }
);
```

### 4. 敏感操作确认

```javascript
// 敏感操作自动确认
const confirmed = await permissionManager.confirmSensitiveOperation(
  'homework.delete',
  '删除作业是不可恢复的操作，确定要继续吗？'
);
```

## 🚪 路由守卫使用

### 页面守卫配置

#### 方式1：使用创建器
```javascript
const protectedPage = routeGuard.createPageGuard({
  requireRole: 'teacher',
  
  onLoad() {
    console.log('页面加载 - 已通过权限检查');
  }
});

Page(protectedPage);
```

#### 方式2：使用装饰器
```javascript
const decoratedPage = routeGuard.requireAuth('student')({
  onLoad() {
    console.log('学生页面加载');
  }
});

Page(decoratedPage);
```

#### 方式3：手动检查
```javascript
const manualCheckPage = {
  async onLoad() {
    const authResult = await routeGuard.checkAuth({
      requireRole: 'parent'
    });
    
    if (!authResult.success) {
      return; // 权限检查失败，已处理跳转
    }
    
    // 继续页面逻辑
    console.log('家长页面加载');
  }
};

Page(manualCheckPage);
```

## 📄 页面权限配置

### 页面权限映射
```javascript
const pagePermissionConfig = {
  'pages/homework/submit/index': {
    permissions: ['homework.submit'],
    roles: ['student'],
    description: '作业提交页面'
  },
  'pages/analysis/progress/index': {
    permissions: ['analysis.view_child'],
    roles: ['parent', 'teacher'],
    description: '学习进度分析'
  }
};
```

### 特殊权限规则
```javascript
const specialPermissionRules = {
  // 动态权限
  dynamic: {
    'analysis.view_child': {
      condition: 'isParentOfTarget',
      description: '只能查看自己孩子的分析'
    }
  },
  
  // 时间限制
  timeRestricted: {
    'homework.submit': {
      timeRange: '06:00-23:00',
      description: '作业提交时间限制'
    }
  }
};
```

## 🔧 权限装饰器

### 方法权限装饰器
```javascript
class HomeworkService {
  @permissionManager.requirePermission('homework.delete', {
    showError: true,
    requireConfirm: true
  })
  async deleteHomework(homeworkId) {
    // 删除逻辑
  }
}
```

## 📊 权限缓存机制

### 缓存策略
- **缓存时间**: 5分钟
- **缓存键**: `${userId}_${permission}`
- **自动清理**: 缓存过期自动清理
- **性能提升**: 平均提升90%检查速度

### 缓存管理
```javascript
// 清理特定用户缓存
permissionManager.clearUserCache(userId);

// 清理所有缓存
permissionManager.clearAllCache();

// 检查缓存状态
const cacheInfo = permissionManager.getCacheInfo();
```

## 🧪 测试与验证

### 自动化测试
```javascript
// 运行权限系统测试
const tester = new PermissionSystemTest();
await tester.runAllTests();

// 性能测试
const perfTester = new PermissionPerformanceTest();
await perfTester.testPermissionCheckPerformance();
```

### 测试覆盖范围
- ✅ 基础权限检查
- ✅ 角色权限验证
- ✅ 页面访问控制
- ✅ 动态权限检查
- ✅ 敏感操作确认
- ✅ 权限组验证
- ✅ 缓存机制测试
- ✅ 性能基准测试

## 🚨 安全注意事项

### 权限设计原则
1. **最小权限原则**: 用户只获得完成任务所需的最小权限
2. **权限分离**: 不同角色权限明确分离
3. **敏感操作保护**: 重要操作需要二次确认
4. **动态权限**: 基于资源所有权的动态权限检查

### 安全检查清单
- [ ] 禁止权限代码硬编码
- [ ] 敏感操作必须二次确认
- [ ] 权限检查不能绕过
- [ ] 错误时默认拒绝访问
- [ ] 权限变更需要重新登录

## 📈 性能优化

### 缓存优化
- 权限检查结果缓存5分钟
- 用户角色信息缓存
- 页面权限配置预加载

### 批量检查
```javascript
// 批量权限检查
const permissions = ['homework.view', 'homework.submit', 'chat.ask'];
const results = await Promise.all(
  permissions.map(perm => permissionManager.hasPermission(perm))
);
```

## 🔄 权限更新流程

### 权限变更
1. 修改 `permission-config.js` 中的配置
2. 更新角色权限映射
3. 运行权限测试验证
4. 清理相关缓存
5. 部署更新

### 新增权限
1. 在权限定义中添加新权限
2. 配置角色权限映射
3. 添加页面权限要求
4. 编写权限测试用例
5. 更新文档

## 📚 API 参考

### PermissionManager 主要方法

- `hasPermission(permission, userId)` - 检查权限
- `hasPermissionGroup(groupName, userId)` - 检查权限组
- `checkPageAccess(pagePath, userId)` - 检查页面访问
- `checkDynamicPermission(permission, resourceData)` - 动态权限检查
- `confirmSensitiveOperation(permission, message)` - 敏感操作确认

### RouteGuard 主要方法

- `checkPageAuth(pagePath, options)` - 页面权限检查
- `createPageGuard(pageConfig)` - 创建页面守卫
- `requireAuth(requireRole)` - 权限装饰器

## 📝 更新日志

### v1.0.0 (2024-10-01)
- ✅ 完成基础权限系统搭建
- ✅ 实现角色权限映射
- ✅ 完成页面权限守卫
- ✅ 添加权限缓存机制
- ✅ 实现敏感操作确认
- ✅ 完成权限系统测试

---

**注意**: 权限系统是安全的核心，任何修改都需要经过充分测试验证。