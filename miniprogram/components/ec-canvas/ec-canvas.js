// ECharts Canvas 组件
import * as echarts from './echarts.min';

let ctx;

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

Component({
  properties: {
    canvasId: {
      type: String,
      value: 'ec-canvas',
    },

    ec: {
      type: Object,
    },

    forceUseOldCanvas: {
      type: Boolean,
      value: false,
    },

    disableScroll: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    isUseNewCanvas: false,
  },

  ready: function () {
    // 微信 7.0.0 以上使用新版 Canvas 2D
    if (
      !this.data.forceUseOldCanvas &&
      compareVersion(wx.getSystemInfoSync().SDKVersion, '2.9.0') >= 0
    ) {
      this.setData({ isUseNewCanvas: true });
      this.initByNewWay();
    } else {
      this.initByOldWay();
    }
  },

  methods: {
    init: function (callback) {
      const version = wx.getSystemInfoSync().SDKVersion;

      const canUseNewCanvas = compareVersion(version, '2.9.0') >= 0;
      const forceUseOldCanvas = this.data.forceUseOldCanvas;
      const isUseNewCanvas = canUseNewCanvas && !forceUseOldCanvas;

      this.setData({ isUseNewCanvas });

      if (forceUseOldCanvas && canUseNewCanvas) {
        console.warn('开发者强制使用旧canvas,建议关闭');
      }

      if (isUseNewCanvas) {
        // console.log('微信基础库版本 >= 2.9.0，使用新canvas')
        this.initByNewWay(callback);
      } else {
        // console.log('微信基础库版本 < 2.9.0，使用旧canvas')
        this.initByOldWay(callback);
      }
    },

    initByOldWay(callback) {
      ctx = wx.createCanvasContext(this.data.canvasId, this);
      const canvas = new WxCanvas(ctx, this.data.canvasId, false);

      echarts.setCanvasCreator(() => {
        return canvas;
      });

      if (typeof callback === 'function') {
        this.chart = callback(
          canvas,
          echarts.init(canvas, null, {
            width: canvas.width,
            height: canvas.height,
            devicePixelRatio: wx.getSystemInfoSync().pixelRatio,
          }),
        );
      } else if (this.data.ec && typeof this.data.ec.onInit === 'function') {
        this.chart = this.data.ec.onInit(
          canvas,
          echarts.init(canvas, null, {
            width: canvas.width,
            height: canvas.height,
            devicePixelRatio: wx.getSystemInfoSync().pixelRatio,
          }),
        );
      }
    },

    initByNewWay(callback) {
      const query = wx.createSelectorQuery().in(this);
      query
        .select('.ec-canvas')
        .fields({ node: true, size: true })
        .exec(res => {
          if (res && res[0]) {
            const canvasNode = res[0].node;
            ctx = canvasNode.getContext('2d');

            const canvas = new WxCanvas(ctx, this.data.canvasId, true, canvasNode);

            echarts.setCanvasCreator(() => {
              return canvas;
            });

            if (typeof callback === 'function') {
              this.chart = callback(
                canvas,
                echarts.init(canvas, null, {
                  width: res[0].width,
                  height: res[0].height,
                  devicePixelRatio: wx.getSystemInfoSync().pixelRatio,
                }),
              );
            } else if (this.data.ec && typeof this.data.ec.onInit === 'function') {
              this.chart = this.data.ec.onInit(
                canvas,
                echarts.init(canvas, null, {
                  width: res[0].width,
                  height: res[0].height,
                  devicePixelRatio: wx.getSystemInfoSync().pixelRatio,
                }),
              );
            }
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
            if (res && res[0]) {
              const canvasNode = res[0].node;
              opt.canvas = canvasNode;
              wx.canvasToTempFilePath(opt);
            }
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
  },
});

// Canvas 适配器
class WxCanvas {
  constructor(ctx, canvasId, isNew, canvasNode) {
    this.ctx = ctx;
    this.canvasId = canvasId;
    this.chart = null;
    this.isNew = isNew;

    if (isNew) {
      this.canvasNode = canvasNode;
    } else {
      this._initStyle(ctx);
    }

    this._initCanvas(ctx, canvasId);
  }

  getContext(contextType) {
    if (contextType === '2d') {
      return this.ctx;
    }
  }

  setChart(chart) {
    this.chart = chart;
  }

  attachEvent() {
    // noop
  }

  detachEvent() {
    // noop
  }

  _initCanvas(ctx, canvasId) {
    ctx.createRadialGradient = () => {
      return ctx.createCircularGradient(arguments);
    };
  }

  _initStyle(ctx) {
    const styles = [
      'fillStyle',
      'strokeStyle',
      'globalAlpha',
      'textAlign',
      'textBaseLine',
      'shadow',
      'lineWidth',
      'lineCap',
      'lineJoin',
      'lineDash',
      'miterLimit',
    ];

    styles.forEach(style => {
      Object.defineProperty(ctx, style, {
        set: value => {
          if (
            (style !== 'fillStyle' && style !== 'strokeStyle') ||
            (value !== 'none' && value !== null)
          ) {
            ctx['set' + style.charAt(0).toUpperCase() + style.slice(1)](value);
          }
        },
      });
    });

    ctx.createRadialGradient = () => {
      return ctx.createCircularGradient(arguments);
    };
  }
}

export { echarts, ctx, WxCanvas };
