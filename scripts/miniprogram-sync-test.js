/**
 * 小程序同步错误修复验证脚本
 *
 * 使用方法：
 * 1. 在小程序开发工具的控制台（Console）中
 * 2. 复制粘贴此脚本
 * 3. 按 Enter 执行
 * 4. 观察输出结果
 */

console.log('========================================')
console.log('🔍 开始验证同步错误修复')
console.log('========================================\n')

// 验证 1: 检查 storage 模块
console.log('📦 验证 1: 检查 Storage 模块')
try {
  const storageModule = require('./utils/storage.js')
  const storage = storageModule.storage

  if (!storage) {
    console.error('❌ storage 未正确导出')
  } else {
    console.log('✅ storage 模块加载成功')

    // 检查 memoryCache
    if (!storage.memoryCache) {
      console.warn('⚠️  memoryCache 未初始化（首次运行正常）')
    } else {
      console.log('✅ memoryCache 已初始化')
    }
  }
} catch (error) {
  console.error('❌ Storage 模块验证失败:', error)
}

console.log('')

// 验证 2: 检查 authManager
console.log('🔐 验证 2: 检查 AuthManager 模块')
try {
  const authModule = require('./utils/auth.js')
  const authManager = authModule.authManager

  if (!authManager) {
    console.error('❌ authManager 未正确导出')
  } else {
    console.log('✅ authManager 模块加载成功')

    // 检查 getDefaultUserInfo 方法
    if (typeof authManager.getDefaultUserInfo === 'function') {
      console.log('✅ getDefaultUserInfo 方法存在')

      // 测试调用
      const defaultUser = authManager.getDefaultUserInfo()
      console.log('📝 默认用户信息:', JSON.stringify(defaultUser, null, 2))
    } else {
      console.error('❌ getDefaultUserInfo 方法不存在')
    }
  }
} catch (error) {
  console.error('❌ AuthManager 模块验证失败:', error)
}

console.log('')

// 验证 3: 检查 syncManager
console.log('🔄 验证 3: 检查 SyncManager 模块')
try {
  const syncModule = require('./utils/sync-manager.js')
  const syncManager = syncModule.syncManager

  if (!syncManager) {
    console.error('❌ syncManager 未正确导出')
  } else {
    console.log('✅ syncManager 模块加载成功')

    // 检查同步间隔
    const intervalMinutes = syncManager.syncInterval / (60 * 1000)
    console.log(`⏱️  自动同步间隔: ${intervalMinutes} 分钟`)

    if (intervalMinutes === 30) {
      console.log('✅ 同步间隔已更新为 30 分钟')
    } else {
      console.warn(`⚠️  同步间隔未更新，当前为 ${intervalMinutes} 分钟`)
    }
  }
} catch (error) {
  console.error('❌ SyncManager 模块验证失败:', error)
}

console.log('')

// 验证 4: 模拟 getUserInfo 调用
console.log('👤 验证 4: 模拟 getUserInfo 调用')
;(async () => {
  try {
    const authModule = require('./utils/auth.js')
    const authManager = authModule.authManager

    console.log('📞 调用 authManager.getUserInfo()...')
    const userInfo = await authManager.getUserInfo()

    if (userInfo) {
      console.log('✅ getUserInfo 返回成功')
      console.log('📝 用户信息:', JSON.stringify(userInfo, null, 2))

      // 检查是否是默认用户信息
      if (userInfo.nickName === '游客') {
        console.log('ℹ️  当前使用默认用户信息（未登录状态）')
      } else {
        console.log('✅ 当前使用真实用户信息')
      }
    } else {
      console.error('❌ getUserInfo 返回 null')
    }
  } catch (error) {
    console.error('❌ getUserInfo 调用失败:', error)
  }

  console.log('')
  console.log('========================================')
  console.log('✨ 验证完成！')
  console.log('========================================')
  console.log('')
  console.log('📋 验证结果说明：')
  console.log('✅ = 通过')
  console.log('⚠️  = 警告（通常可以忽略）')
  console.log('❌ = 错误（需要修复）')
  console.log('')
  console.log('🔍 如果看到 ❌ 错误标记，请检查对应模块的代码。')
  console.log('📱 接下来请在小程序中测试作业问答功能，观察控制台是否还有报错。')
})()
