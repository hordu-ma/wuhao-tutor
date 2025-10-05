Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 空状态类型
    type: {
      type: String,
      value: 'default', // default | search | network | error
    },
    // 空状态图片
    image: {
      type: String,
      value: '',
    },
    // 空状态文本
    text: {
      type: String,
      value: '暂无数据',
    },
    // 空状态描述
    description: {
      type: String,
      value: '',
    },
    // 按钮文本
    buttonText: {
      type: String,
      value: '',
    },
    // 是否显示
    show: {
      type: Boolean,
      value: true,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {
    defaultImages: {
      default: 'https://img.yzcdn.cn/vant/empty-image-default.png',
      search: 'https://img.yzcdn.cn/vant/empty-image-search.png',
      network: 'https://img.yzcdn.cn/vant/empty-image-network.png',
      error: 'https://img.yzcdn.cn/vant/empty-image-error.png',
    },
  },

  /**
   * 组件的方法列表
   */
  methods: {
    onButtonClick() {
      this.triggerEvent('buttonclick');
    },
  },
});
