// components/ec-canvas/ec-canvas.js
// 直接使用完整的ECharts包(更稳定)
const echarts = require('echarts');

if (!echarts) {
  console.error('ECharts加载失败');
  throw new Error('ECharts加载失败，请确保已构建npm包');
}

let ctx;

Component({
  properties: {
    canvasId: {
      type: String,
      value: 'ec-canvas',
    },
    ec: {
      type: Object,
    },
  },

  data: {
    isUseNewCanvas: true,
  },

  ready() {
    if (!this.data.ec) {
      console.warn('组件需绑定 ec 变量');
      return;
    }

    if (!this.data.ec.lazyLoad) {
      this.init();
    }
  },

  methods: {
    init(callback) {
      const version = wx.getSystemInfoSync().SDKVersion;

      const canUseNewCanvas = compareVersion(version, '2.9.0') >= 0;
      const forceUseOldCanvas = this.data.ec.forceUseOldCanvas;
      const isUseNewCanvas = canUseNewCanvas && !forceUseOldCanvas;
      this.setData({ isUseNewCanvas });

      if (forceUseOldCanvas && canUseNewCanvas) {
        console.warn('开发者强制使用旧canvas,建议关闭');
      }

      if (isUseNewCanvas) {
        // 新版使用 type=2d
        this.initByNewWay(callback);
      } else {
        // 旧版使用 context
        const ctx = wx.createCanvasContext(this.data.canvasId, this);
        const canvas = new WxCanvas(ctx, this.data.canvasId, false);

        echarts.setCanvasCreator(() => canvas);

        const query = wx.createSelectorQuery().in(this);
        query
          .select('.ec-canvas')
          .boundingClientRect(res => {
            if (typeof callback === 'function') {
              this.chart = callback(canvas, res.width, res.height, echarts);
            } else if (this.data.ec && typeof this.data.ec.onInit === 'function') {
              this.chart = this.data.ec.onInit(canvas, res.width, res.height, echarts);
            } else {
              this.triggerEvent('init', {
                canvas,
                width: res.width,
                height: res.height,
                echarts,
              });
            }
          })
          .exec();
      }
    },

    initByNewWay(callback) {
      const query = wx.createSelectorQuery().in(this);
      query
        .select('.ec-canvas')
        .fields({ node: true, size: true })
        .exec(res => {
          const canvasNode = res[0].node;
          const canvasContext = canvasNode.getContext('2d');

          const dpr = wx.getSystemInfoSync().pixelRatio;
          canvasNode.width = res[0].width * dpr;
          canvasNode.height = res[0].height * dpr;
          canvasContext.scale(dpr, dpr);

          echarts.setCanvasCreator(() => canvasNode);

          if (typeof callback === 'function') {
            this.chart = callback(canvasNode, res[0].width, res[0].height, echarts);
          } else if (this.data.ec && typeof this.data.ec.onInit === 'function') {
            this.chart = this.data.ec.onInit(canvasNode, res[0].width, res[0].height, echarts);
          } else {
            this.triggerEvent('init', {
              canvas: canvasNode,
              width: res[0].width,
              height: res[0].height,
              echarts,
              dpr,
            });
          }
        });
    },

    canvasToTempFilePath(opt) {
      if (this.data.isUseNewCanvas) {
        const query = wx.createSelectorQuery().in(this);
        query
          .select('.ec-canvas')
          .fields({ node: true, size: true })
          .exec(res => {
            const canvasNode = res[0].node;
            opt.canvas = canvasNode;
            wx.canvasToTempFilePath(opt);
          });
      } else {
        if (!opt.canvasId) {
          opt.canvasId = this.data.canvasId;
        }
        ctx.draw(true, () => {
          wx.canvasToTempFilePath(opt, this);
        });
      }
    },

    touchStart(e) {
      if (this.chart && e.touches.length > 0) {
        const touch = e.touches[0];
        const handler = this.chart.getZr().handler;
        handler.dispatch('mousedown', {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
        handler.dispatch('mousemove', {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
        handler.processGesture(wrapTouch(e), 'start');
      }
    },

    touchMove(e) {
      if (this.chart && e.touches.length > 0) {
        const touch = e.touches[0];
        const handler = this.chart.getZr().handler;
        handler.dispatch('mousemove', {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
        handler.processGesture(wrapTouch(e), 'change');
      }
    },

    touchEnd(e) {
      if (this.chart) {
        const touch = e.changedTouches ? e.changedTouches[0] : {};
        const handler = this.chart.getZr().handler;
        handler.dispatch('mouseup', {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
        handler.dispatch('click', {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
        handler.processGesture(wrapTouch(e), 'end');
      }
    },
  },
});

function wrapTouch(event) {
  for (let i = 0; i < event.touches.length; ++i) {
    const touch = event.touches[i];
    touch.offsetX = touch.x;
    touch.offsetY = touch.y;
  }
  return event;
}

function compareVersion(v1, v2) {
  v1 = v1.split('.');
  v2 = v2.split('.');
  const len = Math.max(v1.length, v2.length);

  while (v1.length < len) {
    v1.push('0');
  }
  while (v2.length < len) {
    v2.push('0');
  }

  for (let i = 0; i < len; i++) {
    const num1 = parseInt(v1[i]);
    const num2 = parseInt(v2[i]);

    if (num1 > num2) {
      return 1;
    } else if (num1 < num2) {
      return -1;
    }
  }

  return 0;
}

// 旧版 Canvas 适配器
function WxCanvas(ctx, canvasId, isNew) {
  this.ctx = ctx;
  this.canvasId = canvasId;
  this.chart = null;
  this.isNew = isNew || false;

  if (isNew) {
    this.ctx.scale(1, 1);
  }
}

WxCanvas.prototype.getContext = function (contextType) {
  return contextType === '2d' ? this.ctx : null;
};

WxCanvas.prototype.setChart = function (chart) {
  this.chart = chart;
};
