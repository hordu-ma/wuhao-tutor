/**
 * 角色标识组件
 * 用于标识用户角色（学生、家长、老师）
 */
Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 角色类型：student-学生, parent-家长, teacher-老师
    role: {
      type: String,
      value: 'student'
    },
    // 尺寸：small-小, medium-中, large-大
    size: {
      type: String,
      value: 'medium'
    },
    // 显示样式：badge-徽章, tag-标签, avatar-头像
    type: {
      type: String,
      value: 'badge'
    },
    // 是否显示图标
    showIcon: {
      type: Boolean,
      value: true
    },
    // 是否显示文字
    showText: {
      type: Boolean,
      value: true
    },
    // 自定义文字（如果不设置则使用默认角色名称）
    customText: {
      type: String,
      value: ''
    },
    // 是否可点击
    clickable: {
      type: Boolean,
      value: false
    },
    // 自定义样式类名
    customClass: {
      type: String,
      value: ''
    },
    // 是否显示在线状态
    showOnline: {
      type: Boolean,
      value: false
    },
    // 在线状态
    online: {
      type: Boolean,
      value: false
    }
  },

  /**
   * 组件的初始数据
   */
  data: {
    roleConfig: {
      student: {
        text: '学生',
        icon: 'student',
        color: '#1890ff',
        bgColor: '#e6f7ff',
        lightColor: 'rgba(24, 144, 255, 0.1)'
      },
      parent: {
        text: '家长',
        icon: 'parent',
        color: '#52c41a',
        bgColor: '#f6ffed',
        lightColor: 'rgba(82, 196, 26, 0.1)'
      },
      teacher: {
        text: '老师',
        icon: 'teacher',
        color: '#faad14',
        bgColor: '#fffbe6',
        lightColor: 'rgba(250, 173, 20, 0.1)'
      }
    },
    sizeConfig: {
      small: {
        fontSize: '20rpx',
        padding: '4rpx 8rpx',
        iconSize: '24rpx',
        height: '32rpx',
        avatarSize: '48rpx'
      },
      medium: {
        fontSize: '24rpx',
        padding: '6rpx 12rpx',
        iconSize: '32rpx',
        height: '40rpx',
        avatarSize: '64rpx'
      },
      large: {
        fontSize: '28rpx',
        padding: '8rpx 16rpx',
        iconSize: '40rpx',
        height: '48rpx',
        avatarSize: '80rpx'
      }
    }
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 获取角色配置
     */
    getRoleConfig() {
      return this.data.roleConfig[this.data.role] || this.data.roleConfig.student;
    },

    /**
     * 获取尺寸配置
     */
    getSizeConfig() {
      return this.data.sizeConfig[this.data.size] || this.data.sizeConfig.medium;
    },

    /**
     * 获取显示文字
     */
    getDisplayText() {
      if (this.data.customText) {
        return this.data.customText;
      }
      return this.getRoleConfig().text;
    },

    /**
     * 获取图标名称
     */
    getIconName() {
      return this.getRoleConfig().icon;
    },

    /**
     * 获取角色颜色
     */
    getRoleColor() {
      return this.getRoleConfig().color;
    },

    /**
     * 获取背景颜色
     */
    getBgColor() {
      return this.getRoleConfig().bgColor;
    },

    /**
     * 获取浅色背景
     */
    getLightColor() {
      return this.getRoleConfig().lightColor;
    },

    /**
     * 点击事件
     */
    onTap(e) {
      if (!this.data.clickable) return;

      this.triggerEvent('tap', {
        role: this.data.role,
        text: this.getDisplayText(),
        type: this.data.type,
        size: this.data.size
      });
    },

    /**
     * 长按事件
     */
    onLongPress(e) {
      if (!this.data.clickable) return;

      this.triggerEvent('longpress', {
        role: this.data.role,
        text: this.getDisplayText(),
        type: this.data.type,
        size: this.data.size
      });
    }
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    /**
     * 组件实例刚刚被创建好时
     */
    created() {
      // 验证角色类型
      const validRoles = ['student', 'parent', 'teacher'];
      if (!validRoles.includes(this.data.role)) {
        console.warn(`Invalid role: ${this.data.role}. Using default: student`);
        this.setData({
          role: 'student'
        });
      }

      // 验证尺寸
      const validSizes = ['small', 'medium', 'large'];
      if (!validSizes.includes(this.data.size)) {
        console.warn(`Invalid size: ${this.data.size}. Using default: medium`);
        this.setData({
          size: 'medium'
        });
      }

      // 验证类型
      const validTypes = ['badge', 'tag', 'avatar'];
      if (!validTypes.includes(this.data.type)) {
        console.warn(`Invalid type: ${this.data.type}. Using default: badge`);
        this.setData({
          type: 'badge'
        });
      }
    },

    /**
     * 组件实例进入页面节点树时
     */
    attached() {
      // 组件初始化完成
    },

    /**
     * 组件在视图层布局完成后执行
     */
    ready() {
      // 组件布局完成
    },

    /**
     * 组件实例被移动到节点树另一个位置时
     */
    moved() {
      // 组件被移动
    },

    /**
     * 组件实例被从页面节点树移除时
     */
    detached() {
      // 组件被移除
    }
  },

  /**
   * 组件数据字段监听器
   */
  observers: {
    'role, size, type': function (role, size, type) {
      // 当关键属性变化时，重新验证并更新组件状态
      this.triggerEvent('change', {
        role,
        size,
        type,
        config: this.getRoleConfig()
      });
    }
  }
});
