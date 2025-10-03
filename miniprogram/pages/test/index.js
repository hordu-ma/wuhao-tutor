/**
 * Task 1.5 测试页面
 * 在微信开发者工具中运行的测试界面
 *
 * @author AI Assistant
 * @since 2025-01-15
 * @version 1.0.0
 */

const { TestRunner } = require('../../tests/run-all-tests.js');
const { ApiTester } = require('../../tests/api-tester.js');
const { FrontendTester } = require('../../tests/frontend-tester.js');
const { PerformanceUtils } = require('../../tests/performance-monitor.js');

Page({
  data: {
    // 测试状态
    isRunning: false,
    currentTest: '',

    // 测试结果
    testResults: null,
    testLogs: [],

    // 配置选项
    testConfig: {
      runApiTests: true,
      runFrontendTests: true,
      runPerformanceTests: true,
      enableDetailedLogs: true,
    },

    // 性能监控
    performanceData: null,
  },

  onLoad() {
    console.log('🧪 Task 1.5 测试页面加载');

    // 启动性能监控
    PerformanceUtils.startGlobalMonitoring();

    // 初始化测试日志
    this.addLog('测试页面初始化完成', 'info');
    this.addLog('性能监控已启动', 'info');

    // 显示环境信息
    this.displayEnvironmentInfo();
  },

  onUnload() {
    // 停止性能监控
    PerformanceUtils.stopGlobalMonitoring();
  },

  /**
   * 显示环境信息
   */
  displayEnvironmentInfo() {
    try {
      const accountInfo = wx.getAccountInfoSync();
      const systemInfo = wx.getSystemInfoSync();

      this.addLog(`小程序环境: ${accountInfo.miniProgram.envVersion}`, 'info');
      this.addLog(`设备型号: ${systemInfo.brand} ${systemInfo.model}`, 'info');
      this.addLog(`系统版本: ${systemInfo.system}`, 'info');
      this.addLog(`微信版本: ${systemInfo.version}`, 'info');

    } catch (error) {
      this.addLog(`获取环境信息失败: ${error.message}`, 'error');
    }
  },

  /**
   * 添加测试日志
   */
  addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const log = {
      time: timestamp,
      message,
      type, // info, success, error, warning
    };

    const logs = this.data.testLogs;
    logs.push(log);

    // 只保留最新50条日志
    if (logs.length > 50) {
      logs.shift();
    }

    this.setData({
      testLogs: logs,
    });

    // 控制台输出
    const emoji = {
      info: 'ℹ️',
      success: '✅',
      error: '❌',
      warning: '⚠️',
    };

    console.log(`${emoji[type]} [${timestamp}] ${message}`);
  },

  /**
   * 运行快速测试
   */
  async runQuickTests() {
    if (this.data.isRunning) {
      this.addLog('测试正在进行中，请等待完成', 'warning');
      return;
    }

    this.setData({
      isRunning: true,
      currentTest: '快速测试',
      testResults: null,
    });

    this.addLog('开始执行快速测试...', 'info');

    try {
      // 执行API快速测试
      if (this.data.testConfig.runApiTests) {
        await this.runApiQuickTests();
      }

      // 执行前端快速测试
      if (this.data.testConfig.runFrontendTests) {
        await this.runFrontendQuickTests();
      }

      // 获取性能报告
      if (this.data.testConfig.runPerformanceTests) {
        this.getPerformanceReport();
      }

      this.addLog('快速测试完成', 'success');

    } catch (error) {
      this.addLog(`快速测试失败: ${error.message}`, 'error');
    } finally {
      this.setData({
        isRunning: false,
        currentTest: '',
      });
    }
  },

  /**
   * 运行完整测试
   */
  async runFullTests() {
    if (this.data.isRunning) {
      this.addLog('测试正在进行中，请等待完成', 'warning');
      return;
    }

    this.setData({
      isRunning: true,
      currentTest: '完整测试',
      testResults: null,
    });

    this.addLog('开始执行完整测试...', 'info');

    try {
      const runner = TestRunner;
      const results = await runner.runFullSuite();

      this.setData({
        testResults: results,
      });

      if (results.summary.overallStatus === 'passed') {
        this.addLog('完整测试全部通过', 'success');
      } else {
        this.addLog(`完整测试完成，但有${results.summary.failed}个失败`, 'warning');
      }

    } catch (error) {
      this.addLog(`完整测试失败: ${error.message}`, 'error');
    } finally {
      this.setData({
        isRunning: false,
        currentTest: '',
      });
    }
  },

  /**
   * 运行API快速测试
   */
  async runApiQuickTests() {
    this.setData({ currentTest: 'API测试' });
    this.addLog('开始API测试...', 'info');

    try {
      const apiTester = new ApiTester();
      const results = await apiTester.runQuickTests();

      this.addLog(`API测试完成: ${results.passed}/${results.total} 通过`, 'success');

      return results;
    } catch (error) {
      this.addLog(`API测试失败: ${error.message}`, 'error');
      throw error;
    }
  },

  /**
   * 运行前端快速测试
   */
  async runFrontendQuickTests() {
    this.setData({ currentTest: '前端测试' });
    this.addLog('开始前端测试...', 'info');

    try {
      const frontendTester = new FrontendTester();
      const results = await frontendTester.runQuickTests();

      this.addLog(`前端测试完成: ${results.passed}/${results.total} 通过`, 'success');

      return results;
    } catch (error) {
      this.addLog(`前端测试失败: ${error.message}`, 'error');
      throw error;
    }
  },

  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    this.setData({ currentTest: '性能分析' });
    this.addLog('生成性能报告...', 'info');

    try {
      const performanceReport = PerformanceUtils.getPerformanceReport();
      const suggestions = PerformanceUtils.getOptimizationSuggestions();
      const healthCheck = PerformanceUtils.checkPerformanceHealth();

      this.setData({
        performanceData: {
          report: performanceReport,
          suggestions,
          health: healthCheck,
        },
      });

      this.addLog(`性能报告生成完成，健康得分: ${healthCheck.score}`, 'success');

      if (suggestions.length > 0) {
        this.addLog(`发现${suggestions.length}个性能优化建议`, 'warning');
      }

    } catch (error) {
      this.addLog(`性能报告生成失败: ${error.message}`, 'error');
    }
  },

  /**
   * 测试单个API
   */
  async testSingleApi() {
    this.addLog('测试单个API调用...', 'info');

    try {
      const api = require('../../api/index.js');

      // 测试获取作业模板
      const result = await api.homework.getTemplates();

      if (result.success) {
        this.addLog(`API调用成功: 获取${result.data.templates.length}个模板`, 'success');
      } else {
        this.addLog(`API调用失败: ${result.message}`, 'error');
      }

    } catch (error) {
      this.addLog(`API调用异常: ${error.message}`, 'error');
    }
  },

  /**
   * 清空测试日志
   */
  clearLogs() {
    this.setData({
      testLogs: [],
    });
    this.addLog('日志已清空', 'info');
  },

  /**
   * 导出测试结果
   */
  exportResults() {
    const data = {
      timestamp: new Date().toISOString(),
      testResults: this.data.testResults,
      testLogs: this.data.testLogs,
      performanceData: this.data.performanceData,
    };

    try {
      // 保存到本地存储
      const reportKey = `test_report_${Date.now()}`;
      wx.setStorageSync(reportKey, data);

      this.addLog(`测试结果已导出: ${reportKey}`, 'success');

      // 提示用户
      wx.showToast({
        title: '导出成功',
        icon: 'success',
      });

    } catch (error) {
      this.addLog(`导出失败: ${error.message}`, 'error');

      wx.showToast({
        title: '导出失败',
        icon: 'error',
      });
    }
  },

  /**
   * 切换测试配置
   */
  toggleConfig(e) {
    const { key } = e.currentTarget.dataset;
    const config = this.data.testConfig;
    config[key] = !config[key];

    this.setData({
      testConfig: config,
    });

    this.addLog(`配置已更新: ${key} = ${config[key]}`, 'info');
  },

  /**
   * 查看详细结果
   */
  viewDetailedResults() {
    if (!this.data.testResults) {
      wx.showToast({
        title: '没有测试结果',
        icon: 'none',
      });
      return;
    }

    // 显示详细结果弹窗
    wx.showModal({
      title: '测试结果详情',
      content: JSON.stringify(this.data.testResults.summary, null, 2),
      showCancel: false,
    });
  },

  /**
   * 查看性能建议
   */
  viewPerformanceSuggestions() {
    if (!this.data.performanceData || !this.data.performanceData.suggestions.length) {
      wx.showToast({
        title: '没有性能建议',
        icon: 'none',
      });
      return;
    }

    const suggestions = this.data.performanceData.suggestions
      .map((item, index) => `${index + 1}. ${item.title}: ${item.description}`)
      .join('\n\n');

    wx.showModal({
      title: '性能优化建议',
      content: suggestions,
      showCancel: false,
    });
  },

  /**
   * 分享测试结果
   */
  shareResults() {
    if (!this.data.testResults) {
      wx.showToast({
        title: '没有测试结果',
        icon: 'none',
      });
      return;
    }

    const summary = this.data.testResults.summary;
    const content = `Task 1.5 测试结果:\n总测试数: ${summary.total_tests}\n通过数: ${summary.passed_tests}\n通过率: ${summary.pass_rate}\n状态: ${summary.overall_status}`;

    wx.setClipboardData({
      data: content,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success',
        });
      },
    });
  },
});
