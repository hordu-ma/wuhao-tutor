/**
 * 测试 Analytics API 错误处理修复
 * 验证所有 API 方法都能正确返回而不是抛出异常
 */

import * as analyticsApi from '../src/api/analytics'

// 测试所有可能导致 Promise.reject 的 API 方法
const testApiMethods = async () => {
  console.log('🧪 开始测试 Analytics API 错误处理...')

  const testCases = [
    // 学习目标相关
    {
      name: 'createLearningGoal',
      fn: () =>
        analyticsApi.createLearningGoal({
          title: 'Test Goal',
          description: 'Test',
          type: 'study_time',
          targetValue: 100,
          deadline: '2024-12-31',
        }),
    },
    {
      name: 'updateLearningGoal',
      fn: () => analyticsApi.updateLearningGoal('test-id', { title: 'Updated Goal' }),
    },
    { name: 'deleteLearningGoal', fn: () => analyticsApi.deleteLearningGoal('test-id') },

    // 报告相关
    {
      name: 'generateLearningReport',
      fn: () => analyticsApi.generateLearningReport('weekly', '2024-01-01', '2024-01-07'),
    },
    { name: 'exportLearningData', fn: () => analyticsApi.exportLearningData('csv', '30d') },

    // 提醒相关
    {
      name: 'setStudyReminder',
      fn: () =>
        analyticsApi.setStudyReminder({
          type: 'daily',
          time: '09:00',
          message: 'Test reminder',
          enabled: true,
        }),
    },
    {
      name: 'updateStudyReminder',
      fn: () => analyticsApi.updateStudyReminder('test-id', { enabled: false }),
    },
    { name: 'deleteStudyReminder', fn: () => analyticsApi.deleteStudyReminder('test-id') },

    // 其他返回空数据的API
    {
      name: 'getLearningProgress',
      fn: () => analyticsApi.getLearningProgress('2024-01-01', '2024-01-31'),
    },
    { name: 'getSubjectStats', fn: () => analyticsApi.getSubjectStats('30d') },
    { name: 'getLearningRecommendations', fn: () => analyticsApi.getLearningRecommendations(10) },
    { name: 'getLearningGoals', fn: () => analyticsApi.getLearningGoals() },
    { name: 'getErrorAnalysis', fn: () => analyticsApi.getErrorAnalysis('math') },
    { name: 'getLearningReport', fn: () => analyticsApi.getLearningReport('daily', '2024-01-01') },
    { name: 'getTimeDistribution', fn: () => analyticsApi.getTimeDistribution('7d') },
    { name: 'getStudyHeatmap', fn: () => analyticsApi.getStudyHeatmap(2024) },
    { name: 'getKnowledgeNetwork', fn: () => analyticsApi.getKnowledgeNetwork('math') },
    { name: 'getEfficiencyAnalysis', fn: () => analyticsApi.getEfficiencyAnalysis('30d') },
    { name: 'getAchievements', fn: () => analyticsApi.getAchievements('study') },
    { name: 'getStudyPatternAnalysis', fn: () => analyticsApi.getStudyPatternAnalysis('30d') },
    { name: 'getLeaderboard', fn: () => analyticsApi.getLeaderboard('study_time', 'week') },
    { name: 'getPersonalInsights', fn: () => analyticsApi.getPersonalInsights() },
    { name: 'getStudyCalendar', fn: () => analyticsApi.getStudyCalendar(2024, 1) },
    { name: 'getStudyReminders', fn: () => analyticsApi.getStudyReminders() },
  ]

  let passedCount = 0
  let failedCount = 0

  for (const testCase of testCases) {
    try {
      console.log(`  测试 ${testCase.name}...`)
      const result = await testCase.fn()

      // 验证返回结果格式
      if (
        result &&
        typeof result === 'object' &&
        'code' in result &&
        'success' in result &&
        'data' in result
      ) {
        console.log(`  ✅ ${testCase.name}: 成功返回标准格式`)
        passedCount++
      } else {
        console.log(`  ❌ ${testCase.name}: 返回格式不正确`, result)
        failedCount++
      }
    } catch (error) {
      console.log(`  💥 ${testCase.name}: 抛出异常`, error.message)
      failedCount++
    }
  }

  console.log('\n📊 测试结果总结:')
  console.log(`  ✅ 通过: ${passedCount}`)
  console.log(`  ❌ 失败: ${failedCount}`)
  console.log(`  📈 成功率: ${Math.round((passedCount / (passedCount + failedCount)) * 100)}%`)

  if (failedCount === 0) {
    console.log('\n🎉 所有 API 方法都正确处理了错误情况，不会导致页面崩溃！')
    return true
  } else {
    console.log('\n⚠️  仍有 API 方法存在问题，需要进一步修复')
    return false
  }
}

// 仅在 Node.js 环境中运行
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { testApiMethods }

  // 如果直接运行此文件
  if (require.main === module) {
    testApiMethods().then((success) => {
      process.exit(success ? 0 : 1)
    })
  }
}
