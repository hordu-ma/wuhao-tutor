// 公式图片加载调试工具
// 在小程序中添加此代码来调试图片加载问题

const FormulaDebugger = {
  // 检查图片URL是否可访问
  async checkImageUrl(imageUrl) {
    return new Promise(resolve => {
      wx.getImageInfo({
        src: imageUrl,
        success: res => {
          console.log('✅ 图片加载成功:', imageUrl, res);
          resolve({ success: true, info: res });
        },
        fail: err => {
          console.error('❌ 图片加载失败:', imageUrl, err);
          resolve({ success: false, error: err });
        },
      });
    });
  },

  // 批量检查公式图片
  async checkFormulaImages(content) {
    const imgRegex = /<img[^>]+src="([^"]+)"[^>]*>/g;
    const images = [];
    let match;

    while ((match = imgRegex.exec(content)) !== null) {
      images.push(match[1]);
    }

    console.log('🔍 发现公式图片:', images);

    for (const imageUrl of images) {
      const result = await this.checkImageUrl(imageUrl);
      if (!result.success) {
        console.error('🚨 图片加载失败详情:', {
          url: imageUrl,
          error: result.error,
        });
      }
    }
  },

  // 网络状态检查
  checkNetworkStatus() {
    wx.getNetworkType({
      success: res => {
        console.log('📶 网络状态:', res.networkType);
        if (res.networkType === 'none') {
          console.warn('⚠️ 无网络连接');
        }
      },
    });
  },
};

// 导出调试器
module.exports = FormulaDebugger;
