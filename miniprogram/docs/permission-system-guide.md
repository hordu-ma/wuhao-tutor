# TODO 2.4 权限控制系统完整指南

## 概述

本文档详细介绍了微信小程序中完整的权限控制系统实现，包括页面级权限控制、功能模块权限验证、API调用权限管理、敏感操作二次确认机制以及友好的权限提示系统。

## 系统架构

### 核心组件

1. **enhanced-page-guard.js** - 增强页面权限守卫
2. **feature-permission-guard.js** - 功能级权限守卫
3. **api-permission-guard.js** - API权限守卫
4. **sensitive-operation-guard.js** - 敏感操作确认守卫
5. **friendly-permission-dialog.js** - 友好权限提示系统
6. **sensitive-confirm-modal** - 敏感操作确认组件

### 权限层级

```
用户认证层
    ↓
角色权限层 (学生/家长/教师)
    ↓
页面访问权限层
    ↓
功能操作权限层
    ↓
API调用权限层
    ↓
敏感操作确认层
```

## 1. 页面级权限控制

### 功能特性
- 基于角色的页面访问控制
- 登录状态验证
- 动态权限检查
- 角色切换检测

### 使用方法

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

### 配置示例

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

## 2. 功能模块权限验证

### 功能特性
- 细粒度权限检查
- 条件验证（时间限制、次数限制等）
- 所有权验证
- 文件类型和大小验证

### 使用方法

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

### 配置示例

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

## 3. API调用权限管理

### 功能特性
- HTTP方法和URL匹配
- 请求拦截器
- 响应拦截器
- 资源所有权验证
- 敏感API标记

### 使用方法

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

### 配置示例

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
    sensitive: true                   // 敏感操作标记
  }
};
```

## 4. 敏感操作二次确认

### 功能特性
- 分级确认（简单确认、密码确认、理由确认）
- 操作日志记录
- 权限预检查
- 资源所有权验证

### 使用方法

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
    console.log('用户取消操作或权限不足');
    return;
  }
  
  // 执行删除操作
  await performDelete(homeworkId);
}
```

### 配置示例

```javascript
const SENSITIVE_OPERATION_CONFIG = {
  'homework.batch_delete': {
    title: '批量删除作业',
    message: '确认要删除选中的 {count} 个作业吗？删除后将无法恢复。',
    requirePassword: true,            // 需要密码确认
    requireReason: true,              // 需要理由说明
    type: 'danger',                   // 危险级别
    icon: 'delete'
  }
};
```

## 5. 友好权限提示系统

### 功能特性
- 多种错误类型支持
- 用户友好的提示信息
- 操作指导和解决方案
- 权限申请流程

### 使用方法

```javascript
const { friendlyPermissionDialog } = require('../utils/friendly-permission-dialog.js');

// 显示权限错误提示
function handlePermissionError() {
  friendlyPermissionDialog.showPermissionError('role_not_allowed', {
    userRole: 'student',
    requiredRoles: ['teacher'],
    message: '此功能仅限教师使用'
  });
}
```

### 支持的错误类型

- `not_logged_in` - 未登录
- `role_not_allowed` - 角色权限不足
- `permission_denied` - 基础权限被拒绝
- `condition_failed` - 使用条件不满足
- `time_restriction` - 时间限制
- `daily_limit` - 次数限制
- `not_owner` - 资源所有权问题
- `network_error` - 网络错误
- `server_error` - 服务器错误

## 6. 敏感操作确认组件

### 组件特性
- 支持密码验证
- 支持理由输入
- 实时表单验证
- 自定义样式主题

### 使用方法

```wxml
<sensitive-confirm-modal
  show="{{showConfirmModal}}"
  config="{{confirmConfig}}"
  bind:confirm="onConfirmOperation"
/>
```

```javascript
// 页面中使用
data: {
  showConfirmModal: false,
  confirmConfig: {}
},

showSensitiveConfirm() {
  this.setData({
    showConfirmModal: true,
    confirmConfig: {
      title: '删除确认',
      message: '确认要删除这个作业吗？',
      requirePassword: true,
      requireReason: false,
      type: 'danger'
    }
  });
},

onConfirmOperation(e) {
  const { confirmed, extraData } = e.detail;
  if (confirmed) {
    // 用户确认操作
    console.log('密码:', extraData.password);
    console.log('理由:', extraData.reason);
  }
  this.setData({ showConfirmModal: false });
}
```

## 完整使用示例

### 作业管理页面示例

```javascript
const { enhancedPageGuard } = require('../utils/enhanced-page-guard.js');
const { featurePermissionGuard } = require('../utils/feature-permission-guard.js');
const { sensitiveOperationGuard } = require('../utils/sensitive-operation-guard.js');

const homeworkPage = enhancedPageGuard.createGuardedPage({
  data: {
    homeworkList: []
  },

  async onDeleteHomework(e) {
    const homeworkId = e.currentTarget.dataset.id;
    
    try {
      // 1. 检查功能权限
      const canDelete = await featurePermissionGuard.checkFeaturePermission(
        'homework.delete',
        { homeworkId }
      );
      
      if (!canDelete.success) {
        featurePermissionGuard.handlePermissionFailure(canDelete);
        return;
      }

      // 2. 敏感操作确认
      const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(
        'homework.delete',
        { homeworkId }
      );
      
      if (!confirmResult.success) {
        return;
      }

      // 3. 执行删除
      await this.deleteHomeworkAPI(homeworkId);
      this.refreshHomeworkList();
      
    } catch (error) {
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '删除失败，请稍后重试'
      });
    }
  }

}, 'pages/homework/manage/index');
```

## 最佳实践

### 1. 权限设计原则
- **最小权限原则**: 用户只获得完成任务所需的最小权限
- **角色分离**: 清晰定义不同角色的权限边界
- **分层验证**: 在多个层面进行权限检查
- **友好提示**: 提供清晰的错误信息和解决方案

### 2. 性能优化
- **权限缓存**: 合理使用缓存机制避免重复检查
- **异步检查**: 使用异步方式进行权限验证
- **批量验证**: 对多个权限进行批量检查
- **懒加载**: 按需加载权限配置

### 3. 安全考虑
- **前后端双重验证**: 前端权限检查仅用于用户体验，后端必须再次验证
- **敏感操作保护**: 对危险操作实施多重确认
- **日志记录**: 记录所有权限相关操作
- **定期审查**: 定期审查权限配置和使用情况

### 4. 错误处理
- **统一错误处理**: 使用统一的错误处理机制
- **用户友好**: 提供易懂的错误信息
- **操作指导**: 为用户提供解决问题的指导
- **优雅降级**: 在权限不足时提供替代方案

## 调试和测试

### 调试模式
```javascript
// 启用调试模式
enhancedPageGuard.enableDebugMode();
featurePermissionGuard.enableDebugMode();

// 获取调试信息
const debugInfo = enhancedPageGuard.getDebugInfo();
console.log('权限调试信息:', debugInfo);
```

### 权限测试
```javascript
// 测试页面权限
const pageAccess = await enhancedPageGuard.checkFeaturePermission('view_analysis');

// 测试功能权限
const featureAccess = await featurePermissionGuard.checkFeaturePermission('homework.submit');

// 测试敏感操作
const sensitiveResult = await sensitiveOperationGuard.confirmSensitiveOperation('homework.delete');
```

## 总结

TODO 2.4权限控制系统提供了完整的权限管理解决方案，包括：

1. ✅ **页面级权限控制** - 实现基于角色和权限的页面访问控制
2. ✅ **功能模块权限验证** - 提供细粒度的功能权限检查
3. ✅ **API调用权限管理** - 建立API调用的权限验证层
4. ✅ **敏感操作二次确认** - 为危险操作添加确认流程
5. ✅ **友好权限提示** - 提供清晰的错误信息和用户引导

该系统具有以下优势：
- **模块化设计**: 各组件独立，易于维护和扩展
- **配置驱动**: 通过配置文件管理权限规则
- **用户友好**: 提供清晰的提示和指导
- **安全可靠**: 多层权限验证，确保系统安全
- **性能优化**: 合理的缓存和异步处理机制

通过这套权限控制系统，可以有效保护应用的安全性，同时提供良好的用户体验。