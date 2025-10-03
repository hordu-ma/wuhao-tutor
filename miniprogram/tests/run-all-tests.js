/**
 * 综合测试执行脚本
 * 一次性运行所有类型的测试，生成完整的测试报告
 *
 * @author AI Assistant
 * @since 2025-01-15
 * @version 1.0.0
 */

const { ApiTester } = require('./api-tester.js');
const { FrontendTester } = require('./frontend-tester.js');
const { PerformanceUtils } = require('./performance-monitor.js');

/**
 * 测试套件配置
 */
const TEST_SUITE_CONFIG = {
  // 测试类型配置
  testTypes: {
    api: {
      enabled: true,
      timeout: 300000, // 5分钟
      critical: true,  // 关键测试，失败则整体失败
    },
    frontend: {
      enabled: true,
      timeout: 180000, // 3分钟
      critical: true,
    },
    performance: {
      enabled: true,
      timeout: 120000, // 2分钟
      critical: false, // 非关键测试
    },
  },

  // 报告配置
  report: {
    outputFormat: 'console', // console, file, both
    includeDetails: true,
    includeSuggestions: true,
    saveToStorage: true,
  },

  // 测试环境配置
  environment: {
    requireBackend: true,  // 是否需要后端服务
    checkConnectivity: true, // 检查网络连接
    validateEnvironment: true, // 验证环境配置
  },
};

/**
 * 测试结果聚合器
 */
class TestResultAggregator {
  constructor() {
    this.results = {
      summary: {
        totalTests: 0,
        totalPassed: 0,
        totalFailed: 0,
        totalSkipped: 0,
        startTime: null,
        endTime: null,
        duration: 0,
        overallStatus: 'unknown',
      },
      testSuites: {},
      issues: [],
      suggestions: [],
      environmentInfo: {},
    };
  }

  /**
   * 开始测试
   */
  startTesting() {
    this.results.summary.startTime = new Date().toISOString();
    console.log('🚀 开始执行综合测试套件');
    console.log('='.repeat(60));
  }

  /**
   * 结束测试
   */
  endTesting() {
    this.results.summary.endTime = new Date().toISOString();
    this.results.summary.duration = Date.now() - new Date(this.results.summary.startTime).getTime();

    // 计算总体状态
    this.calculateOverallStatus();

    console.log('\n📊 测试套件执行完成');
    console.log('='.repeat(60));
  }

  /**
   * 添加测试套件结果
   * @param {string} suiteName 测试套件名称
   * @param {Object} result 测试结果
   */
  addSuiteResult(suiteName, result) {
    this.results.testSuites[suiteName] = {
      ...result,
      timestamp: new Date().toISOString(),
    };

    // 更新总计
    this.results.summary.totalTests += result.total || 0;
    this.results.summary.totalPassed += result.passed || 0;
    this.results.summary.totalFailed += result.failed || 0;

    // 收集问题
    if (result.errors && result.errors.length > 0) {
      this.results.issues.push(...result.errors.map(error => ({
        suite: suiteName,
        ...error,
      })));
    }
  }

  /**
   * 添加性能建议
   * @param {Array} suggestions 建议列表
   */
  addSuggestions(suggestions) {
    this.results.suggestions.push(...suggestions);
  }

  /**
   * 设置环境信息
   * @param {Object} envInfo 环境信息
   */
  setEnvironmentInfo(envInfo) {
    this.results.environmentInfo = envInfo;
  }

  /**
   * 计算总体状态
   */
  calculateOverallStatus() {
    const { totalTests, totalPassed, totalFailed } = this.results.summary;

    if (totalTests === 0) {
      this.results.summary.overallStatus = 'no_tests';
    } else if (totalFailed === 0) {
      this.results.summary.overallStatus = 'passed';
    } else {
      // 检查关键测试是否失败
      const criticalFailures = Object.entries(this.results.testSuites)
        .filter(([suiteName, result]) => {
          const config = TEST_SUITE_CONFIG.testTypes[suiteName];
          return config && config.critical && result.failed > 0;
        });

      if (criticalFailures.length > 0) {
        this.results.summary.overallStatus = 'failed';
      } else {
        this.results.summary.overallStatus = 'passed_with_warnings';
      }
    }
  }

  /**
   * 生成测试报告
   */
  generateReport() {
    const report = {
      ...this.results,
      generatedAt: new Date().toISOString(),
      version: '1.0.0',
    };

    if (TEST_SUITE_CONFIG.report.outputFormat === 'console' ||
      TEST_SUITE_CONFIG.report.outputFormat === 'both') {
      this.printConsoleReport();
    }

    if (TEST_SUITE_CONFIG.report.saveToStorage) {
      this.saveReportToStorage(report);
    }

    return report;
  }

  /**
   * 控制台打印报告
   */
  printConsoleReport() {
    const { summary } = this.results;

    console.log('\n📋 测试执行总结');
    console.log('='.repeat(60));

    // 基本统计
    console.log(`📊 测试统计:`);
    console.log(`   总测试数: ${summary.totalTests}`);
    console.log(`   通过数: ${summary.totalPassed}`);
    console.log(`   失败数: ${summary.totalFailed}`);
    console.log(`   跳过数: ${summary.totalSkipped}`);
    console.log(`   通过率: ${summary.totalTests > 0 ? ((summary.totalPassed / summary.totalTests) * 100).toFixed(1) : 0}%`);
    console.log(`   执行时长: ${Math.round(summary.duration / 1000)}秒`);

    // 总体状态
    const statusEmoji = {
      passed: '✅',
      failed: '❌',
      passed_with_warnings: '⚠️',
      no_tests: '❓',
      unknown: '❓',
    };

    console.log(`   总体状态: ${statusEmoji[summary.overallStatus]} ${summary.overallStatus.toUpperCase()}`);

    // 各测试套件详情
    if (TEST_SUITE_CONFIG.report.includeDetails) {
      console.log('\n📝 测试套件详情:');
      Object.entries(this.results.testSuites).forEach(([suiteName, result]) => {
        const passRate = result.total > 0 ? ((result.passed / result.total) * 100).toFixed(1) : 0;
        const status = result.failed === 0 ? '✅' : '❌';

        console.log(`   ${status} ${suiteName}: ${result.passed}/${result.total} 通过 (${passRate}%)`);

        if (result.failed > 0 && result.errors) {
          result.errors.slice(0, 3).forEach(error => {
            console.log(`      └─ ❌ ${error.test || error.message}`);
          });

          if (result.errors.length > 3) {
            console.log(`      └─ ... 还有 ${result.errors.length - 3} 个错误`);
          }
        }
      });
    }

    // 性能问题
    if (this.results.issues.length > 0) {
      console.log('\n⚠️ 发现的问题:');
      this.results.issues.slice(0, 5).forEach((issue, index) => {
        console.log(`   ${index + 1}. [${issue.suite}] ${issue.test || issue.message}`);
      });

      if (this.results.issues.length > 5) {
        console.log(`   ... 还有 ${this.results.issues.length - 5} 个问题`);
      }
    }

    // 优化建议
    if (TEST_SUITE_CONFIG.report.includeSuggestions && this.results.suggestions.length > 0) {
      console.log('\n💡 优化建议:');
      this.results.suggestions.slice(0, 5).forEach((suggestion, index) => {
        console.log(`   ${index + 1}. ${suggestion.title}`);
        console.log(`      ${suggestion.description}`);
        if (suggestion.recommendations && suggestion.recommendations.length > 0) {
          console.log(`      推荐: ${suggestion.recommendations[0]}`);
        }
      });

      if (this.results.suggestions.length > 5) {
        console.log(`   ... 还有 ${this.results.suggestions.length - 5} 个建议`);
      }
    }

    console.log('='.repeat(60));
  }

  /**
   * 保存报告到本地存储
   * @param {Object} report 测试报告
   */
  saveReportToStorage(report) {
    try {
      const reportKey = `test_report_${Date.now()}`;
      wx.setStorageSync(reportKey, report);
      console.log(`💾 测试报告已保存: ${reportKey}`);

      // 清理旧报告，只保留最近5个
      this.cleanOldTestReports();
    } catch (error) {
      console.warn('保存测试报告失败:', error);
    }
  }

  /**
   * 清理旧的测试报告
   */
  cleanOldTestReports() {
    try {
      const storageInfo = wx.getStorageInfoSync();
      const reportKeys = storageInfo.keys
        .filter(key => key.startsWith('test_report_'))
        .sort();

      if (reportKeys.length > 5) {
        const oldKeys = reportKeys.slice(0, reportKeys.length - 5);
        oldKeys.forEach(key => {
          wx.removeStorageSync(key);
        });
      }
    } catch (error) {
      console.warn('清理旧报告失败:', error);
    }
  }
}

/**
 * 综合测试执行器
 */
class ComprehensiveTestRunner {
  constructor() {
    this.aggregator = new TestResultAggregator();
    this.environment = null;
  }

  /**
   * 执行所有测试
   */
  async runAllTests() {
    this.aggregator.startTesting();

    try {
      // 1. 环境检查
      await this.checkEnvironment();

      // 2. 启动性能监控
      if (TEST_SUITE_CONFIG.testTypes.performance.enabled) {
        PerformanceUtils.startGlobalMonitoring();
      }

      // 3. 执行API测试
      if (TEST_SUITE_CONFIG.testTypes.api.enabled) {
        await this.runApiTests();
      }

      // 4. 执行前端测试
      if (TEST_SUITE_CONFIG.testTypes.frontend.enabled) {
        await this.runFrontendTests();
      }

      // 5. 执行性能测试
      if (TEST_SUITE_CONFIG.testTypes.performance.enabled) {
        await this.runPerformanceTests();
      }

    } catch (error) {
      console.error('❌ 测试执行过程中发生严重错误:', error);
      this.aggregator.addSuiteResult('system', {
        total: 1,
        passed: 0,
        failed: 1,
        errors: [{ test: 'system_error', message: error.message }],
      });
    } finally {
      // 停止性能监控
      if (TEST_SUITE_CONFIG.testTypes.performance.enabled) {
        PerformanceUtils.stopGlobalMonitoring();
      }

      this.aggregator.endTesting();
    }

    return this.aggregator.generateReport();
  }

  /**
   * 检查测试环境
   */
  async checkEnvironment() {
    console.log('🔍 检查测试环境...');

    const envInfo = {
      timestamp: new Date().toISOString(),
      miniprogram: {},
      system: {},
      network: {},
    };

    try {
      // 获取小程序信息
      if (typeof wx !== 'undefined') {
        const accountInfo = wx.getAccountInfoSync();
        envInfo.miniprogram = {
          appId: accountInfo.miniProgram.appId,
          version: accountInfo.miniProgram.version,
          envVersion: accountInfo.miniProgram.envVersion,
        };

        // 获取系统信息
        const systemInfo = wx.getSystemInfoSync();
        envInfo.system = {
          brand: systemInfo.brand,
          model: systemInfo.model,
          system: systemInfo.system,
          platform: systemInfo.platform,
          version: systemInfo.version,
          SDKVersion: systemInfo.SDKVersion,
        };

        // 获取网络信息
        const networkInfo = await this.getNetworkInfo();
        envInfo.network = networkInfo;
      }

      this.aggregator.setEnvironmentInfo(envInfo);

      // 验证测试环境
      if (TEST_SUITE_CONFIG.environment.validateEnvironment) {
        await this.validateEnvironment(envInfo);
      }

      console.log('✅ 环境检查完成');
    } catch (error) {
      console.warn('⚠️ 环境检查部分失败:', error);
    }
  }

  /**
   * 获取网络信息
   */
  async getNetworkInfo() {
    return new Promise((resolve) => {
      wx.getNetworkType({
        success: (res) => {
          resolve({
            networkType: res.networkType,
            isConnected: res.networkType !== 'none',
          });
        },
        fail: () => {
          resolve({
            networkType: 'unknown',
            isConnected: false,
          });
        },
      });
    });
  }

  /**
   * 验证测试环境
   * @param {Object} envInfo 环境信息
   */
  async validateEnvironment(envInfo) {
    const issues = [];

    // 检查网络连接
    if (TEST_SUITE_CONFIG.environment.checkConnectivity) {
      if (!envInfo.network.isConnected) {
        issues.push('网络未连接，可能影响API测试');
      }
    }

    // 检查环境版本
    if (envInfo.miniprogram.envVersion === 'release') {
      issues.push('当前为生产环境，建议在开发环境进行测试');
    }

    // 检查后端服务
    if (TEST_SUITE_CONFIG.environment.requireBackend) {
      try {
        // 简单的健康检查
        const healthCheck = await this.checkBackendHealth();
        if (!healthCheck) {
          issues.push('后端服务不可用');
        }
      } catch (error) {
        issues.push(`后端服务检查失败: ${error.message}`);
      }
    }

    if (issues.length > 0) {
      console.warn('⚠️ 环境验证发现问题:');
      issues.forEach(issue => console.warn(`   - ${issue}`));
    }
  }

  /**
   * 检查后端服务健康状态
   */
  async checkBackendHealth() {
    try {
      // 这里应该调用实际的健康检查API
      // 暂时返回true，实际实现时需要替换
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 执行API测试
   */
  async runApiTests() {
    console.log('\n🌐 开始API集成测试...');

    try {
      const apiTester = new ApiTester();
      const result = await Promise.race([
        apiTester.runAllTests(),
        this.createTimeout(TEST_SUITE_CONFIG.testTypes.api.timeout, 'API测试超时'),
      ]);

      this.aggregator.addSuiteResult('api', result);
      console.log(`✅ API测试完成: ${result.passed}/${result.total} 通过`);
    } catch (error) {
      console.error('❌ API测试失败:', error.message);
      this.aggregator.addSuiteResult('api', {
        total: 1,
        passed: 0,
        failed: 1,
        errors: [{ test: 'api_suite', message: error.message }],
      });
    }
  }

  /**
   * 执行前端测试
   */
  async runFrontendTests() {
    console.log('\n🎨 开始前端功能测试...');

    try {
      const frontendTester = new FrontendTester();
      const result = await Promise.race([
        frontendTester.runAllTests(),
        this.createTimeout(TEST_SUITE_CONFIG.testTypes.frontend.timeout, '前端测试超时'),
      ]);

      this.aggregator.addSuiteResult('frontend', result);
      console.log(`✅ 前端测试完成: ${result.passed}/${result.total} 通过`);
    } catch (error) {
      console.error('❌ 前端测试失败:', error.message);
      this.aggregator.addSuiteResult('frontend', {
        total: 1,
        passed: 0,
        failed: 1,
        errors: [{ test: 'frontend_suite', message: error.message }],
      });
    }
  }

  /**
   * 执行性能测试
   */
  async runPerformanceTests() {
    console.log('\n🚀 开始性能测试...');

    try {
      const performanceResult = await Promise.race([
        this.runPerformanceAnalysis(),
        this.createTimeout(TEST_SUITE_CONFIG.testTypes.performance.timeout, '性能测试超时'),
      ]);

      this.aggregator.addSuiteResult('performance', performanceResult.testResult);

      if (performanceResult.suggestions) {
        this.aggregator.addSuggestions(performanceResult.suggestions);
      }

      console.log(`✅ 性能测试完成`);
    } catch (error) {
      console.error('❌ 性能测试失败:', error.message);
      this.aggregator.addSuiteResult('performance', {
        total: 1,
        passed: 0,
        failed: 1,
        errors: [{ test: 'performance_suite', message: error.message }],
      });
    }
  }

  /**
   * 执行性能分析
   */
  async runPerformanceAnalysis() {
    // 获取性能报告
    const performanceReport = PerformanceUtils.getPerformanceReport();

    // 获取优化建议
    const suggestions = PerformanceUtils.getOptimizationSuggestions();

    // 检查性能健康状态
    const healthCheck = PerformanceUtils.checkPerformanceHealth();

    // 生成测试结果
    const testResult = {
      total: 1,
      passed: healthCheck.health === 'good' ? 1 : 0,
      failed: healthCheck.health === 'poor' ? 1 : 0,
      performanceScore: healthCheck.score,
      details: performanceReport,
    };

    if (healthCheck.health === 'poor') {
      testResult.errors = [{
        test: 'performance_health',
        message: `性能健康状况较差，得分: ${healthCheck.score}`,
      }];
    }

    return {
      testResult,
      suggestions,
      healthCheck,
    };
  }

  /**
   * 创建超时Promise
   * @param {number} timeout 超时时间
   * @param {string} message 超时消息
   */
  createTimeout(timeout, message) {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(message));
      }, timeout);
    });
  }

  /**
   * 执行快速测试（仅核心功能）
   */
  async runQuickTests() {
    console.log('⚡ 开始执行快速测试套件');

    this.aggregator.startTesting();

    try {
      // 环境检查
      await this.checkEnvironment();

      // 只执行关键测试
      if (TEST_SUITE_CONFIG.testTypes.api.enabled) {
        console.log('\n🌐 执行API快速测试...');
        const apiTester = new ApiTester();
        const result = await apiTester.runQuickTests();
        this.aggregator.addSuiteResult('api_quick', result);
      }

      if (TEST_SUITE_CONFIG.testTypes.frontend.enabled) {
        console.log('\n🎨 执行前端快速测试...');
        const frontendTester = new FrontendTester();
        const result = await frontendTester.runQuickTests();
        this.aggregator.addSuiteResult('frontend_quick', result);
      }

    } catch (error) {
      console.error('❌ 快速测试失败:', error);
    } finally {
      this.aggregator.endTesting();
    }

    return this.aggregator.generateReport();
  }
}

/**
 * 导出和使用接口
 */
const TestRunner = {
  /**
   * 运行完整测试套件
   */
  async runFullSuite() {
    const runner = new ComprehensiveTestRunner();
    return await runner.runAllTests();
  },

  /**
   * 运行快速测试
   */
  async runQuickSuite() {
    const runner = new ComprehensiveTestRunner();
    return await runner.runQuickTests();
  },

  /**
   * 获取测试配置
   */
  getConfig() {
    return TEST_SUITE_CONFIG;
  },

  /**
   * 更新测试配置
   * @param {Object} newConfig 新配置
   */
  updateConfig(newConfig) {
    Object.assign(TEST_SUITE_CONFIG, newConfig);
  },
};

// 导出
module.exports = {
  TestRunner,
  ComprehensiveTestRunner,
  TestResultAggregator,
  TEST_SUITE_CONFIG,
};

// 如果直接运行此文件，执行完整测试套件
if (typeof require !== 'undefined' && require.main === module) {
  TestRunner.runFullSuite().then((report) => {
    console.log('\n🎉 综合测试执行完成');

    const exitCode = report.summary.overallStatus === 'passed' ? 0 : 1;

    if (typeof process !== 'undefined') {
      process.exit(exitCode);
    }
  }).catch((error) => {
    console.error('❌ 测试套件执行失败:', error);

    if (typeof process !== 'undefined') {
      process.exit(1);
    }
  });
}

// 小程序环境下的快捷调用
if (typeof wx !== 'undefined') {
  // 全局测试函数
  global.runTests = TestRunner.runQuickSuite;
  global.runFullTests = TestRunner.runFullSuite;

  console.log('🧪 测试工具已加载');
  console.log('   使用 runTests() 执行快速测试');
  console.log('   使用 runFullTests() 执行完整测试');
}
