const api = require('../../api/index.js');

Page({
  data: {
    id: null,
    plan: null,
    loading: true,
    downloading: false,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: options.id });
      this.fetchDetail(options.id);
    }
  },

  async fetchDetail(id) {
    this.setData({ loading: true });
    try {
      const plan = await api.revisions.getRevisionPlanDetail(id);
      
      // Format date
      if (plan.created_at) {
        plan.created_at_formatted = plan.created_at.substring(0, 10);
      }

      this.setData({
        plan,
        loading: false,
      });
    } catch (err) {
      console.error(err);
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none',
      });
    }
  },

  async onDownloadTap() {
    if (this.data.downloading) return;
    
    this.setData({ downloading: true });
    try {
      const res = await api.revisions.downloadRevisionPlan(this.data.id);
      const url = res.url;
      
      if (!url) {
        throw new Error('下载链接无效');
      }

      // Download file
      wx.downloadFile({
        url: url,
        success: (downloadRes) => {
          if (downloadRes.statusCode === 200) {
            const filePath = downloadRes.tempFilePath;
            wx.openDocument({
              filePath: filePath,
              showMenu: true,
              success: function () {
                console.log('打开文档成功');
              },
              fail: function(e) {
                console.error('打开文档失败', e);
                wx.showToast({
                  title: '打开文档失败',
                  icon: 'none',
                });
              }
            });
          } else {
            wx.showToast({
              title: '下载失败',
              icon: 'none',
            });
          }
        },
        fail: (e) => {
          console.error('下载失败', e);
          wx.showToast({
            title: '下载失败',
            icon: 'none',
          });
        },
        complete: () => {
          this.setData({ downloading: false });
        }
      });

    } catch (err) {
      console.error(err);
      this.setData({ downloading: false });
      wx.showToast({
        title: '获取下载链接失败',
        icon: 'none',
      });
    }
  },

  async onDeleteTap() {
    wx.showModal({
      title: '提示',
      content: '确定要删除这个复习计划吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.revisions.deleteRevisionPlan(this.data.id);
            wx.showToast({
              title: '删除成功',
              icon: 'success',
            });
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          } catch (err) {
            console.error(err);
            wx.showToast({
              title: '删除失败',
              icon: 'none',
            });
          }
        }
      }
    });
  },
});
