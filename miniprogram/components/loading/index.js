Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 加载文本
    text: {
      type: String,
      value: '加载中...',
    },
    // 是否显示
    show: {
      type: Boolean,
      value: false,
    },
    // 加载动画类型
    type: {
      type: String,
      value: 'spinner', // spinner | circular
    },
    // 加载动画大小
    size: {
      type: String,
      value: '40px',
    },
    // 是否全屏显示
    fullscreen: {
      type: Boolean,
      value: false,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {},

  /**
   * 组件的方法列表
   */
  methods: {},
});
