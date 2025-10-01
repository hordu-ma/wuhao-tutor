// 权限系统测试文件
// 测试各种权限控制场景

const { permissionManager } = require('../utils/permission-manager.js');
const { roleManager } = require('../utils/role-manager.js');
const { routeGuard } = require('../utils/route-guard.js');

/**
 * 权限系统测试类
 */
class PermissionSystemTest {
  constructor() {
    this.testResults = [];
  }

  /**
   * 运行所有测试
   */
  async runAllTests() {
    console.log('🚀 开始权限系统测试...');
    
    try {
      await this.testBasicPermissions();
      await this.testRolePermissions();
      await this.testPagePermissions();
      await this.testDynamicPermissions();
      await this.testSensitiveOperations();
      await this.testPermissionGroups();
      
      this.printTestResults();
    } catch (error) {
      console.error('测试执行失败:', error);
    }
  }

  /**
   * 测试基础权限功能
   */
  async testBasicPermissions() {
    console.log('\n📋 测试基础权限功能');
    
    // 模拟学生角色
    await this.simulateRole('student');
    
    // 测试学生应该有的权限
    const shouldHavePermissions = [
      'homework.view',
      'homework.submit',
      'chat.ask',
      'analysis.view_self'
    ];
    
    for (const permission of shouldHavePermissions) {
      const hasPermission = await permissionManager.hasPermission(permission);
      this.addTestResult(`学生应有权限: ${permission}`, hasPermission, true);
    }
    
    // 测试学生不应该有的权限
    const shouldNotHavePermissions = [
      'homework.correct',
      'homework.manage',
      'user.manage_students',
      'admin.system_config'
    ];
    
    for (const permission of shouldNotHavePermissions) {
      const hasPermission = await permissionManager.hasPermission(permission);
      this.addTestResult(`学生不应有权限: ${permission}`, hasPermission, false);
    }
  }

  /**
   * 测试角色权限
   */
  async testRolePermissions() {
    console.log('\n👥 测试角色权限');
    
    const roles = ['student', 'parent', 'teacher'];
    
    for (const role of roles) {
      await this.simulateRole(role);
      
      // 测试角色特定权限
      switch (role) {
        case 'student':
          await this.testStudentPermissions();
          break;
        case 'parent':
          await this.testParentPermissions();
          break;
        case 'teacher':
          await this.testTeacherPermissions();
          break;
      }
    }
  }

  /**
   * 测试学生权限
   */
  async testStudentPermissions() {
    const canSubmitHomework = await permissionManager.hasPermission('homework.submit');
    const canAskQuestion = await permissionManager.hasPermission('chat.ask');
    const canCorrectHomework = await permissionManager.hasPermission('homework.correct');
    
    this.addTestResult('学生可以提交作业', canSubmitHomework, true);
    this.addTestResult('学生可以提问', canAskQuestion, true);
    this.addTestResult('学生不能批改作业', canCorrectHomework, false);
  }

  /**
   * 测试家长权限
   */
  async testParentPermissions() {
    const canViewChildHomework = await permissionManager.hasPermission('homework.view_child');
    const canViewChildAnalysis = await permissionManager.hasPermission('analysis.view_child');
    const canSubmitHomework = await permissionManager.hasPermission('homework.submit');
    
    this.addTestResult('家长可以查看孩子作业', canViewChildHomework, true);
    this.addTestResult('家长可以查看孩子分析', canViewChildAnalysis, true);
    this.addTestResult('家长不能提交作业', canSubmitHomework, false);
  }

  /**
   * 测试教师权限
   */
  async testTeacherPermissions() {
    const canCorrectHomework = await permissionManager.hasPermission('homework.correct');
    const canManageStudents = await permissionManager.hasPermission('user.manage_students');
    const canViewClassAnalysis = await permissionManager.hasPermission('analysis.view_class');
    const canSubmitHomework = await permissionManager.hasPermission('homework.submit');
    
    this.addTestResult('教师可以批改作业', canCorrectHomework, true);
    this.addTestResult('教师可以管理学生', canManageStudents, true);
    this.addTestResult('教师可以查看班级分析', canViewClassAnalysis, true);
    this.addTestResult('教师不能提交作业', canSubmitHomework, false);
  }

  /**
   * 测试页面权限
   */
  async testPagePermissions() {
    console.log('\n📄 测试页面权限');
    
    const pageTests = [
      {
        role: 'student',
        page: 'pages/homework/submit/index',
        shouldAccess: true,
        description: '学生访问作业提交页面'
      },
      {
        role: 'parent',
        page: 'pages/homework/submit/index',
        shouldAccess: false,
        description: '家长访问作业提交页面'
      },
      {
        role: 'teacher',
        page: 'pages/analysis/progress/index',
        shouldAccess: true,
        description: '教师访问学习进度页面'
      },
      {
        role: 'student',
        page: 'pages/analysis/progress/index',
        shouldAccess: false,
        description: '学生访问学习进度页面'
      }
    ];
    
    for (const test of pageTests) {
      await this.simulateRole(test.role);
      const canAccess = await permissionManager.checkPageAccess(test.page);
      this.addTestResult(test.description, canAccess, test.shouldAccess);
    }
  }

  /**
   * 测试动态权限
   */
  async testDynamicPermissions() {
    console.log('\n🔄 测试动态权限');
    
    // 模拟家长角色
    await this.simulateRole('parent');
    
    // 测试查看自己孩子的数据
    const ownChildData = { studentId: 'child123' };
    const canViewOwnChild = await permissionManager.checkDynamicPermission(
      'analysis.view_child',
      ownChildData
    );
    
    // 测试查看别人孩子的数据
    const otherChildData = { studentId: 'other456' };
    const canViewOtherChild = await permissionManager.checkDynamicPermission(
      'analysis.view_child',
      otherChildData
    );
    
    this.addTestResult('家长可以查看自己孩子数据', canViewOwnChild, true);
    this.addTestResult('家长不能查看别人孩子数据', canViewOtherChild, false);
  }

  /**
   * 测试敏感操作
   */
  async testSensitiveOperations() {
    console.log('\n⚠️ 测试敏感操作');
    
    const sensitivePermissions = [
      'homework.delete',
      'user.manage_students',
      'admin.user_manage'
    ];
    
    for (const permission of sensitivePermissions) {
      const isSensitive = permissionManager.isSensitivePermission(permission);
      this.addTestResult(`${permission} 被标记为敏感操作`, isSensitive, true);
    }
    
    // 测试非敏感操作
    const normalPermissions = [
      'homework.view',
      'chat.ask',
      'profile.view_self'
    ];
    
    for (const permission of normalPermissions) {
      const isSensitive = permissionManager.isSensitivePermission(permission);
      this.addTestResult(`${permission} 不是敏感操作`, isSensitive, false);
    }
  }

  /**
   * 测试权限组
   */
  async testPermissionGroups() {
    console.log('\n👫 测试权限组');
    
    // 测试学生基础权限组
    await this.simulateRole('student');
    const hasBasicStudent = await permissionManager.hasPermissionGroup('basic_student');
    this.addTestResult('学生具有基础学生权限组', hasBasicStudent, true);
    
    const hasBasicParent = await permissionManager.hasPermissionGroup('basic_parent');
    this.addTestResult('学生不具有基础家长权限组', hasBasicParent, false);
    
    // 测试教师管理权限组
    await this.simulateRole('teacher');
    const hasManagement = await permissionManager.hasPermissionGroup('management');
    this.addTestResult('教师具有管理权限组', hasManagement, true);
  }

  /**
   * 模拟角色
   */
  async simulateRole(role) {
    // 这里应该模拟设置用户角色
    // 实际应用中需要与 authManager 配合
    console.log(`🎭 切换到角色: ${role}`);
    
    // 模拟设置用户信息
    global.mockUserRole = role;
    global.mockUserInfo = {
      id: 'test_user_' + role,
      role: role,
      children: role === 'parent' ? ['child123'] : [],
      classes: role === 'teacher' ? ['class123'] : []
    };
  }

  /**
   * 添加测试结果
   */
  addTestResult(description, actual, expected) {
    const passed = actual === expected;
    const result = {
      description,
      actual,
      expected,
      passed,
      icon: passed ? '✅' : '❌'
    };
    
    this.testResults.push(result);
    console.log(`  ${result.icon} ${description}: ${actual} (期望: ${expected})`);
  }

  /**
   * 打印测试结果
   */
  printTestResults() {
    console.log('\n📊 测试结果统计:');
    
    const passedTests = this.testResults.filter(r => r.passed).length;
    const totalTests = this.testResults.length;
    const passRate = ((passedTests / totalTests) * 100).toFixed(1);
    
    console.log(`总测试数: ${totalTests}`);
    console.log(`通过测试: ${passedTests}`);
    console.log(`失败测试: ${totalTests - passedTests}`);
    console.log(`通过率: ${passRate}%`);
    
    if (passedTests === totalTests) {
      console.log('🎉 所有测试都通过了！权限系统工作正常。');
    } else {
      console.log('⚠️ 部分测试失败，请检查权限配置。');
      
      // 显示失败的测试
      const failedTests = this.testResults.filter(r => !r.passed);
      console.log('\n失败的测试:');
      failedTests.forEach(test => {
        console.log(`  ❌ ${test.description}`);
        console.log(`     实际: ${test.actual}, 期望: ${test.expected}`);
      });
    }
  }
}

/**
 * 权限系统性能测试
 */
class PermissionPerformanceTest {
  /**
   * 测试权限检查性能
   */
  async testPermissionCheckPerformance() {
    console.log('\n⚡ 权限检查性能测试');
    
    const iterations = 1000;
    const permission = 'homework.view';
    
    // 测试无缓存性能
    permissionManager.permissionCache.clear();
    const startTime = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      await permissionManager.hasPermission(permission);
    }
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    const avgTime = duration / iterations;
    
    console.log(`${iterations} 次权限检查耗时: ${duration}ms`);
    console.log(`平均每次检查: ${avgTime.toFixed(2)}ms`);
    
    // 测试缓存性能
    const cacheStartTime = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      await permissionManager.hasPermission(permission);
    }
    
    const cacheEndTime = Date.now();
    const cacheDuration = cacheEndTime - cacheStartTime;
    const cacheAvgTime = cacheDuration / iterations;
    
    console.log(`${iterations} 次缓存权限检查耗时: ${cacheDuration}ms`);
    console.log(`平均每次检查: ${cacheAvgTime.toFixed(2)}ms`);
    console.log(`缓存提升: ${((duration - cacheDuration) / duration * 100).toFixed(1)}%`);
  }
}

// 导出测试类
module.exports = {
  PermissionSystemTest,
  PermissionPerformanceTest
};

// 如果直接运行此文件，执行测试
if (require.main === module) {
  const tester = new PermissionSystemTest();
  const perfTester = new PermissionPerformanceTest();
  
  (async () => {
    await tester.runAllTests();
    await perfTester.testPermissionCheckPerformance();
  })();
}