// 测试页面 - 验证 async/await 支持
// 路径: miniprogram/pages/test-async/index.js

Page({
  data: {
    testResult: '等待测试...',
    status: 'pending',
  },

  onLoad() {
    console.log('=== 开始 async/await 测试 ===');
    this.runTests();
  },

  /**
   * 运行所有测试
   */
  async runTests() {
    try {
      // 测试 1: 基本 async/await
      console.log('测试 1: 基本 async/await');
      await this.testBasicAsync();

      // 测试 2: Promise.all
      console.log('测试 2: Promise.all');
      await this.testPromiseAll();

      // 测试 3: 错误处理
      console.log('测试 3: 错误处理');
      await this.testErrorHandling();

      // 所有测试通过
      this.setData({
        testResult: '✅ 所有测试通过！async/await 工作正常',
        status: 'success',
      });

      console.log('=== 测试完成：成功 ===');

      wx.showToast({
        title: '测试通过',
        icon: 'success',
      });
    } catch (error) {
      console.error('=== 测试失败 ===', error);

      this.setData({
        testResult: `❌ 测试失败：${error.message}`,
        status: 'error',
      });

      wx.showModal({
        title: '测试失败',
        content: error.message + '\n\n请启用增强编译！',
        showCancel: false,
      });
    }
  },

  /**
   * 测试 1: 基本 async/await
   */
  async testBasicAsync() {
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

    console.log('  - 开始延迟 100ms');
    await delay(100);
    console.log('  - 延迟完成');

    return 'test1-ok';
  },

  /**
   * 测试 2: Promise.all
   */
  async testPromiseAll() {
    const task1 = Promise.resolve('任务1完成');
    const task2 = Promise.resolve('任务2完成');
    const task3 = Promise.resolve('任务3完成');

    const results = await Promise.all([task1, task2, task3]);
    console.log('  - Promise.all 结果:', results);

    return 'test2-ok';
  },

  /**
   * 测试 3: 错误处理
   */
  async testErrorHandling() {
    try {
      // 故意抛出错误
      throw new Error('测试错误');
    } catch (error) {
      console.log('  - 成功捕获错误:', error.message);
      // 错误被正确捕获
      return 'test3-ok';
    }
  },

  /**
   * 手动重新测试
   */
  onRetry() {
    this.setData({
      testResult: '重新测试中...',
      status: 'pending',
    });
    this.runTests();
  },
});
