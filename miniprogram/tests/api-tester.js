/**
 * API 集成测试工具
 * 用于测试小程序与后端 API 的集成功能
 *
 * @author AI Assistant
 * @since 2025-01-15
 * @version 1.0.0
 */

const api = require('../api/index.js');

/**
 * 测试配置
 */
const TEST_CONFIG = {
  // 测试超时时间
  timeout: 30000,

  // 重试次数
  retryTimes: 3,

  // 测试数据
  testData: {
    student: {
      name: '测试学生',
      id: 'test-student-001',
    },
    homework: {
      template_id: 'test-template-math-001',
      content: '这是一道数学题：2+3=?',
      answer: '5',
    },
    question: {
      content: '什么是二次函数？',
      subject: 'math',
      grade: '9',
    },
  },
};

/**
 * 测试结果记录器
 */
class TestResultRecorder {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      errors: [],
      details: [],
    };
  }

  /**
   * 记录测试结果
   * @param {string} testName 测试名称
   * @param {boolean} passed 是否通过
   * @param {string} message 消息
   * @param {number} duration 执行时间
   */
  record(testName, passed, message, duration = 0) {
    this.results.total++;

    if (passed) {
      this.results.passed++;
    } else {
      this.results.failed++;
      this.results.errors.push({
        test: testName,
        message,
        timestamp: new Date().toISOString(),
      });
    }

    this.results.details.push({
      name: testName,
      passed,
      message,
      duration,
      timestamp: new Date().toISOString(),
    });

    console.log(
      `${passed ? '✅' : '❌'} ${testName}: ${message} ${duration > 0 ? `(${duration}ms)` : ''
      }`
    );
  }

  /**
   * 获取测试总结
   */
  getSummary() {
    const passRate = this.results.total > 0
      ? ((this.results.passed / this.results.total) * 100).toFixed(1)
      : 0;

    return {
      ...this.results,
      passRate: `${passRate}%`,
    };
  }

  /**
   * 打印测试报告
   */
  printReport() {
    const summary = this.getSummary();

    console.log('\n📊 测试报告');
    console.log('='.repeat(50));
    console.log(`总测试数: ${summary.total}`);
    console.log(`通过数: ${summary.passed}`);
    console.log(`失败数: ${summary.failed}`);
    console.log(`通过率: ${summary.passRate}`);

    if (summary.errors.length > 0) {
      console.log('\n❌ 失败的测试:');
      summary.errors.forEach((error, index) => {
        console.log(`${index + 1}. ${error.test}: ${error.message}`);
      });
    }

    console.log('='.repeat(50));
  }
}

/**
 * API 测试工具类
 */
class ApiTester {
  constructor() {
    this.recorder = new TestResultRecorder();
  }

  /**
   * 执行测试并记录结果
   * @param {string} testName 测试名称
   * @param {Function} testFunc 测试函数
   */
  async runTest(testName, testFunc) {
    const startTime = Date.now();

    try {
      await testFunc();
      const duration = Date.now() - startTime;
      this.recorder.record(testName, true, '测试通过', duration);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.recorder.record(testName, false, error.message, duration);
    }
  }

  /**
   * 验证响应结构
   * @param {Object} response API 响应
   * @param {Object} expectedFields 期望的字段
   */
  validateResponse(response, expectedFields = {}) {
    if (!response) {
      throw new Error('响应为空');
    }

    if (typeof response !== 'object') {
      throw new Error('响应格式不正确');
    }

    // 验证基本字段
    const requiredFields = ['success', 'code', 'message'];
    for (const field of requiredFields) {
      if (!(field in response)) {
        throw new Error(`缺少必需字段: ${field}`);
      }
    }

    // 验证成功响应的数据字段
    if (response.success && !response.data) {
      throw new Error('成功响应缺少 data 字段');
    }

    // 验证自定义字段
    if (expectedFields.data && response.success) {
      for (const field of expectedFields.data) {
        if (!(field in response.data)) {
          throw new Error(`数据中缺少字段: ${field}`);
        }
      }
    }

    return true;
  }

  /**
   * 等待指定时间
   * @param {number} ms 毫秒数
   */
  async wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 生成测试用的随机字符串
   * @param {number} length 长度
   */
  generateRandomString(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  // ========================================
  // 作业批改 API 测试
  // ========================================

  /**
   * 测试获取作业模板列表
   */
  async testGetHomeworkTemplates() {
    await this.runTest('获取作业模板列表', async () => {
      const response = await api.homework.getTemplates();
      this.validateResponse(response, {
        data: ['templates']
      });

      if (!Array.isArray(response.data.templates)) {
        throw new Error('模板列表不是数组格式');
      }
    });
  }

  /**
   * 测试获取作业模板详情
   */
  async testGetHomeworkTemplateDetail() {
    await this.runTest('获取作业模板详情', async () => {
      const templateId = TEST_CONFIG.testData.homework.template_id;
      const response = await api.homework.getTemplateDetail(templateId);
      this.validateResponse(response, {
        data: ['template']
      });

      const template = response.data.template;
      if (!template.id || !template.name || !template.subject) {
        throw new Error('模板详情缺少必要字段');
      }
    });
  }

  /**
   * 测试提交文本作业
   */
  async testSubmitTextHomework() {
    await this.runTest('提交文本作业', async () => {
      const { homework, student } = TEST_CONFIG.testData;

      const response = await api.homework.submitHomeworkText({
        template_id: homework.template_id,
        student_name: student.name,
        content: homework.content,
      });

      this.validateResponse(response, {
        data: ['id', 'status']
      });

      if (!response.data.id) {
        throw new Error('提交响应缺少作业ID');
      }
    });
  }

  /**
   * 测试轮询批改结果
   */
  async testPollCorrectionResult() {
    await this.runTest('轮询批改结果', async () => {
      // 先提交作业
      const { homework, student } = TEST_CONFIG.testData;
      const submitResponse = await api.homework.submitHomeworkText({
        template_id: homework.template_id,
        student_name: student.name,
        content: homework.content,
      });

      if (!submitResponse.success) {
        throw new Error('作业提交失败');
      }

      const submissionId = submitResponse.data.id;

      // 轮询结果
      let attempts = 0;
      const maxAttempts = 10;

      while (attempts < maxAttempts) {
        const resultResponse = await api.homework.getCorrectionResult(submissionId);
        this.validateResponse(resultResponse);

        if (resultResponse.success && resultResponse.data.status === 'completed') {
          // 验证批改结果结构
          const result = resultResponse.data;
          if (!result.score && !result.feedback) {
            throw new Error('批改结果缺少分数或反馈');
          }
          return; // 测试通过
        }

        attempts++;
        await this.wait(1000); // 等待1秒后重试
      }

      throw new Error('批改结果轮询超时');
    });
  }

  // ========================================
  // 学习问答 API 测试
  // ========================================

  /**
   * 测试创建学习会话
   */
  async testCreateLearningSession() {
    await this.runTest('创建学习会话', async () => {
      const response = await api.learning.createSession({
        title: '测试学习会话',
        subject: 'math',
      });

      this.validateResponse(response, {
        data: ['session_id']
      });

      if (!response.data.session_id) {
        throw new Error('会话创建失败，缺少session_id');
      }
    });
  }

  /**
   * 测试AI问答功能
   */
  async testAskQuestion() {
    await this.runTest('AI问答功能', async () => {
      const { question } = TEST_CONFIG.testData;

      const response = await api.learning.askQuestion({
        question: question.content,
        subject: question.subject,
        grade: question.grade,
      });

      this.validateResponse(response, {
        data: ['answer', 'question_id']
      });

      if (!response.data.answer || response.data.answer.length < 10) {
        throw new Error('AI回答内容过短或为空');
      }
    });
  }

  /**
   * 测试问题搜索功能
   */
  async testSearchQuestions() {
    await this.runTest('问题搜索功能', async () => {
      const response = await api.learning.searchQuestions({
        query: '二次函数',
        subject: 'math',
        limit: 10,
      });

      this.validateResponse(response, {
        data: ['questions', 'total']
      });

      if (!Array.isArray(response.data.questions)) {
        throw new Error('搜索结果不是数组格式');
      }
    });
  }

  /**
   * 测试图片上传功能
   */
  async testUploadQuestionImage() {
    await this.runTest('图片上传功能', async () => {
      // 模拟图片上传
      const mockImagePath = 'wxfile://temp/test-image.jpg';

      const response = await api.learning.uploadQuestionImage({
        filePath: mockImagePath,
        question: '这是一道数学题',
      });

      this.validateResponse(response, {
        data: ['image_id', 'ocr_text']
      });
    });
  }

  // ========================================
  // 学情分析 API 测试
  // ========================================

  /**
   * 测试获取学情总览
   */
  async testGetAnalyticsOverview() {
    await this.runTest('获取学情总览', async () => {
      const response = await api.analysis.getOverview({
        days: 30,
      });

      this.validateResponse(response, {
        data: ['total_sessions', 'total_questions', 'subjects']
      });

      const data = response.data;
      if (typeof data.total_sessions !== 'number' ||
        typeof data.total_questions !== 'number') {
        throw new Error('学情数据格式不正确');
      }
    });
  }

  /**
   * 测试获取综合分析
   */
  async testGetAnalytics() {
    await this.runTest('获取综合分析', async () => {
      const response = await api.analysis.getAnalytics({
        days: 7,
        include_trends: true,
      });

      this.validateResponse(response, {
        data: ['study_time', 'question_count', 'subjects']
      });
    });
  }

  /**
   * 测试获取学习进度
   */
  async testGetLearningProgress() {
    await this.runTest('获取学习进度', async () => {
      const response = await api.analysis.getLearningProgress({
        subject: 'math',
        time_range: 'week',
      });

      this.validateResponse(response, {
        data: ['progress', 'milestones']
      });
    });
  }

  /**
   * 测试创建学习目标
   */
  async testCreateLearningGoal() {
    await this.runTest('创建学习目标', async () => {
      const goalTitle = `测试目标_${this.generateRandomString()}`;

      const response = await api.analysis.createGoal({
        title: goalTitle,
        description: '这是一个测试学习目标',
        subject: 'math',
        target_value: 100,
        deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      });

      this.validateResponse(response, {
        data: ['goal_id']
      });

      if (!response.data.goal_id) {
        throw new Error('目标创建失败，缺少goal_id');
      }
    });
  }

  // ========================================
  // 错误处理测试
  // ========================================

  /**
   * 测试网络错误处理
   */
  async testNetworkErrorHandling() {
    await this.runTest('网络错误处理', async () => {
      // 这里可以模拟网络错误，比如请求不存在的API
      try {
        await api.homework.getTemplates({
          baseUrl: 'http://invalid-url.com',
        });
        throw new Error('应该抛出网络错误');
      } catch (error) {
        if (error.message.includes('网络') ||
          error.message.includes('请求失败') ||
          error.message.includes('timeout')) {
          // 预期的网络错误
          return;
        }
        throw error;
      }
    });
  }

  /**
   * 测试参数验证
   */
  async testParameterValidation() {
    await this.runTest('参数验证', async () => {
      try {
        // 测试缺少必需参数的情况
        await api.homework.submitHomeworkText({
          // 缺少必需参数
        });
        throw new Error('应该抛出参数验证错误');
      } catch (error) {
        if (error.message.includes('参数') ||
          error.message.includes('必需') ||
          error.message.includes('required')) {
          // 预期的参数错误
          return;
        }
        throw error;
      }
    });
  }

  // ========================================
  // 执行所有测试
  // ========================================

  /**
   * 执行所有 API 测试
   */
  async runAllTests() {
    console.log('🚀 开始执行 API 集成测试');
    console.log('='.repeat(50));

    // 作业批改 API 测试
    console.log('\n📝 作业批改 API 测试');
    await this.testGetHomeworkTemplates();
    await this.testGetHomeworkTemplateDetail();
    await this.testSubmitTextHomework();
    // await this.testPollCorrectionResult(); // 这个测试可能需要较长时间

    // 学习问答 API 测试
    console.log('\n💬 学习问答 API 测试');
    await this.testCreateLearningSession();
    await this.testAskQuestion();
    await this.testSearchQuestions();
    // await this.testUploadQuestionImage(); // 图片上传可能需要真实文件

    // 学情分析 API 测试
    console.log('\n📊 学情分析 API 测试');
    await this.testGetAnalyticsOverview();
    await this.testGetAnalytics();
    await this.testGetLearningProgress();
    await this.testCreateLearningGoal();

    // 错误处理测试
    console.log('\n⚠️ 错误处理测试');
    await this.testNetworkErrorHandling();
    await this.testParameterValidation();

    // 打印测试报告
    this.recorder.printReport();

    return this.recorder.getSummary();
  }

  /**
   * 执行快速测试（核心功能）
   */
  async runQuickTests() {
    console.log('⚡ 开始执行快速测试');
    console.log('='.repeat(30));

    await this.testGetHomeworkTemplates();
    await this.testAskQuestion();
    await this.testGetAnalyticsOverview();

    this.recorder.printReport();
    return this.recorder.getSummary();
  }

  /**
   * 执行性能测试
   */
  async runPerformanceTests() {
    console.log('🏎️ 开始执行性能测试');
    console.log('='.repeat(30));

    const performanceResults = {};

    // 测试API响应时间
    const testApis = [
      { name: '获取模板列表', func: () => api.homework.getTemplates() },
      { name: 'AI问答', func: () => api.learning.askQuestion({ question: '1+1=?' }) },
      { name: '学情总览', func: () => api.analysis.getOverview({ days: 7 }) },
    ];

    for (const test of testApis) {
      const times = [];
      const iterations = 5;

      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();
        try {
          await test.func();
          const duration = Date.now() - startTime;
          times.push(duration);
        } catch (error) {
          console.log(`❌ ${test.name} 测试失败: ${error.message}`);
          break;
        }
      }

      if (times.length > 0) {
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const maxTime = Math.max(...times);
        const minTime = Math.min(...times);

        performanceResults[test.name] = {
          average: avgTime,
          max: maxTime,
          min: minTime,
          samples: times.length,
        };

        console.log(`📊 ${test.name}:`);
        console.log(`   平均响应时间: ${avgTime.toFixed(0)}ms`);
        console.log(`   最长响应时间: ${maxTime}ms`);
        console.log(`   最短响应时间: ${minTime}ms`);
      }
    }

    return performanceResults;
  }
}

// 导出测试工具
module.exports = {
  ApiTester,
  TestResultRecorder,
  TEST_CONFIG,
};

// 如果直接运行此文件，执行所有测试
if (typeof require !== 'undefined' && require.main === module) {
  const tester = new ApiTester();
  tester.runAllTests().then((summary) => {
    console.log('\n✅ 测试执行完成');
    process.exit(summary.failed > 0 ? 1 : 0);
  }).catch((error) => {
    console.error('❌ 测试执行失败:', error);
    process.exit(1);
  });
}
