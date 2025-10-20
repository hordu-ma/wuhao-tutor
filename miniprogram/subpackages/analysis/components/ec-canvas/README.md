# ECharts for WeChat Miniprogram

## 安装说明

由于 ECharts 库文件较大(约 1MB),需要手动下载并放置到此目录。

### 下载步骤

1. 访问 ECharts 官网: https://echarts.apache.org/zh/download.html
2. 下载**微信小程序版本** (echarts.min.js)
3. 或者访问 GitHub: https://github.com/ecomfe/echarts-for-weixin
4. 下载 `ec-canvas/echarts.min.js` 文件
5. 将文件放置到当前目录: `miniprogram/components/ec-canvas/echarts.min.js`

### 快速下载命令

```bash
# 使用 curl 下载 (从 CDN)
cd miniprogram/components/ec-canvas/
curl -o echarts.min.js https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js

# 或使用 wget
wget -O echarts.min.js https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js
```

### 使用说明

组件已配置完成,在页面 json 中引入:

```json
{
  "usingComponents": {
    "ec-canvas": "/components/ec-canvas/ec-canvas"
  }
}
```

在页面 wxml 中使用:

```xml
<ec-canvas id="mychart" canvas-id="mychart" ec="{{ ec }}"></ec-canvas>
```

在页面 js 中初始化:

```javascript
import * as echarts from '../../components/ec-canvas/echarts.min';

Page({
  data: {
    ec: {
      onInit: function (canvas, width, height, dpr) {
        const chart = echarts.init(canvas, null, {
          width: width,
          height: height,
          devicePixelRatio: dpr,
        });

        const option = {
          // ECharts 配置项
        };

        chart.setOption(option);
        return chart;
      },
    },
  },
});
```

## 文件说明

- `ec-canvas.wxml` - 组件模板
- `ec-canvas.wxss` - 组件样式
- `ec-canvas.js` - 组件逻辑(Canvas 适配器)
- `ec-canvas.json` - 组件配置
- `echarts.min.js` - ECharts 核心库 **(需手动下载)**

## 注意事项

1. ECharts 文件约 1MB,会占用小程序包体积
2. 建议使用分包加载优化
3. 支持微信基础库 2.9.0+ 的新版 Canvas 2D
4. 自动兼容旧版 Canvas API
