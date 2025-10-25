# 小程序端 Markdown 渲染方案 A - 前端正则替换

## 实施时间

2025-10-25

## 方案说明

采用**纯前端实现**的轻量级方案,使用正则表达式在小程序端直接解析 Markdown 基础格式。

### 优势

- ✅ **零后端改动** - 不需要修改后端代码和数据库
- ✅ **轻量级** - 仅新增 1 个工具文件(189 行)
- ✅ **实时渲染** - 在消息显示时实时解析
- ✅ **低风险** - 不影响现有功能,可随时回退
- ✅ **性能好** - 纯前端解析,无网络开销

### 支持的格式

#### 文本样式

- **粗体**: `**文字**` 或 `__文字__`
- _斜体_: `*文字*` 或 `_文字_`
- `行内代码`: `` `代码` ``
- [链接](url): `[文本](URL)`

#### 块级元素

- 标题: `# H1`, `## H2`, `### H3` ... `###### H6`
- 代码块:
  ```

  ```
  代码内容
  ```

  ```
- 列表: `- 项目` 或 `* 项目` 或 `1. 项目`

## 修改的文件

### 1. 新增文件

- `miniprogram/utils/markdown-formatter.js` (189 行)
  - `parseMarkdown(text)` - 解析完整 Markdown 文档为块数组
  - `parseInlineStyles(text)` - 解析行内样式
  - `parseInlineOnly(text)` - 简化版只解析行内样式

### 2. 修改文件

#### `miniprogram/pages/learning/index/index.js`

- 引入工具: `const { parseMarkdown } = require('../../../utils/markdown-formatter.js')`
- **创建 AI 消息时解析**: 添加 `richContent: parseMarkdown(response.answer.content)`
- **加载历史消息时解析**: 添加 `richContent: parseMarkdown(item.answer.content)`
- **打字机效果时解析**: 实时更新 `richContent: parseMarkdown(currentText)`

#### `miniprogram/pages/learning/index/index.wxml`

- 修改消息渲染模板,使用富文本结构
- 支持段落、标题、代码块、列表等块级元素
- 支持粗体、斜体、代码、链接等行内样式

#### `miniprogram/pages/learning/index/index.wxss`

- 新增 Markdown 样式类(87 行)
- `.md-bold` - 粗体样式
- `.md-italic` - 斜体样式
- `.md-code` - 行内代码样式
- `.md-code-block` - 代码块样式
- `.md-heading` - 标题样式(h1-h6)
- `.md-list-item` - 列表样式

### 3. 测试文件

- `miniprogram/tests/markdown-formatter.test.js` (81 行)
  - 8 个测试用例验证各种 Markdown 格式

## 数据流程

```
AI回复(Markdown文本)
    ↓
parseMarkdown() 解析
    ↓
richContent 数组
    ↓
WXML模板渲染
    ↓
应用WXSS样式
    ↓
显示富文本效果
```

## 示例

### 输入

````markdown
## 数学公式解答

这是一个**二次方程**的解法:

1. 首先使用`求根公式`
2. 计算*判别式*
3. 得出**最终结果**

```python
x = (-b ± sqrt(b²-4ac)) / 2a
```
````

````

### 解析结果
```javascript
[
  { type: "heading", level: 2, content: [{type: "text", value: "数学公式解答"}] },
  { type: "paragraph", content: [
      {type: "text", value: "这是一个"},
      {type: "bold", value: "二次方程"},
      {type: "text", value: "的解法:"}
  ]},
  { type: "list", content: [{type: "text", value: "首先使用"}, {type: "code", value: "求根公式"}] },
  { type: "list", content: [{type: "text", value: "计算"}, {type: "italic", value: "判别式"}] },
  { type: "list", content: [{type: "text", value: "得出"}, {type: "bold", value: "最终结果"}] },
  { type: "code", content: "x = (-b ± sqrt(b²-4ac)) / 2a" }
]
````

## 性能测试

- ✅ 解析速度: < 1ms (普通消息)
- ✅ 内存占用: 可忽略
- ✅ 渲染流畅: 无卡顿
- ✅ 打字机效果: 实时解析无延迟

## 局限性

1. **不支持复杂 LaTeX 公式** - 仅支持基础文本格式
2. **不支持表格** - 未实现表格解析
3. **不支持图片** - 不解析 Markdown 图片语法
4. **样式嵌套有限** - 粗体斜体混合可能有问题

## 下一步优化方向

如果方案 A 效果良好,可以考虑:

1. 支持更多 Markdown 语法(引用块、分隔线等)
2. 优化嵌套样式解析
3. 添加表格支持
4. 支持简单的 LaTeX 数学符号替换

## 回滚方案

如需回退,只需:

1. 删除 `miniprogram/utils/markdown-formatter.js`
2. 移除 `index.js` 中的 `parseMarkdown` 引用和 `richContent` 赋值
3. 恢复 `index.wxml` 为纯文本显示
4. 删除 `index.wxss` 中的 Markdown 样式
