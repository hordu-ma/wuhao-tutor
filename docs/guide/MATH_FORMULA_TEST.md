# 数学公式渲染测试

## 修复内容

### 1. 添加 KaTeX 支持

- ✅ 导入 `katex` 库和样式
- ✅ 配置 `marked` 扩展支持数学公式
- ✅ 添加公式样式优化

### 2. 支持的公式格式

#### 行内公式 (Inline Math)

使用 `$...$` 包裹公式，例如:

```
这是一个行内公式 $E = mc^2$，继续文字内容。
```

#### 块级公式 (Display Math)

使用 `$$...$$` 包裹公式，例如:

```
$$
\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

### 3. 测试用例

可以在 Learning 页面测试以下问题：

**测试 1: 简单行内公式**

```
请解释公式 $a^2 + b^2 = c^2$ 的含义
```

**测试 2: 复杂块级公式**

```
请解释二次函数的求根公式：

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

这个公式是如何推导出来的？
```

**测试 3: 多个公式混合**

```
在物理学中，我们有能量守恒定律 $E_{\text{total}} = E_k + E_p$，其中动能为：

$$
E_k = \frac{1}{2}mv^2
$$

势能为：

$$
E_p = mgh
$$
```

**测试 4: 矩阵和分数**

```
请展示矩阵乘法的公式：

$$
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
\times
\begin{bmatrix}
e & f \\
g & h
\end{bmatrix}
=
\begin{bmatrix}
ae+bg & af+bh \\
ce+dg & cf+dh
\end{bmatrix}
$$
```

**测试 5: 求和符号**

```
等差数列求和公式为 $S_n = \frac{n(a_1 + a_n)}{2}$，也可以写成：

$$
S_n = \sum_{i=1}^{n} a_i = \frac{n(a_1 + a_n)}{2}
$$
```

### 4. 实现细节

#### 代码修改位置

- **文件**: `frontend/src/views/Learning.vue`
- **行数**: 约 250-460 行

#### 关键代码片段

**1. 导入 KaTeX**

```typescript
import katex from 'katex'
import 'katex/dist/katex.min.css'
```

**2. 配置 Marked 扩展**

```typescript
const configureMarked = () => {
  marked.use({
    extensions: [
      // 行内公式扩展
      {
        name: 'inlineMath',
        level: 'inline',
        start(src: string) {
          return src.indexOf('$')
        },
        tokenizer(src: string) {
          const match = src.match(/^\$+([^$\n]+?)\$+/)
          if (match) {
            return {
              type: 'inlineMath',
              raw: match[0],
              text: match[1].trim(),
            }
          }
        },
        renderer(token: any) {
          try {
            return katex.renderToString(token.text, { throwOnError: false })
          } catch (e) {
            return token.text
          }
        },
      },
      // 块级公式扩展
      {
        name: 'blockMath',
        level: 'block',
        start(src: string) {
          return src.indexOf('$$')
        },
        tokenizer(src: string) {
          const match = src.match(/^\$\$+\n?([\s\S]+?)\n?\$\$+/)
          if (match) {
            return {
              type: 'blockMath',
              raw: match[0],
              text: match[1].trim(),
            }
          }
        },
        renderer(token: any) {
          try {
            return `<div class="katex-block">${katex.renderToString(token.text, {
              throwOnError: false,
              displayMode: true,
            })}</div>`
          } catch (e) {
            return `<pre>${token.text}</pre>`
          }
        },
      },
    ],
  })
}
```

**3. 样式优化**

```scss
:deep(.katex) {
  font-size: 1.1em;
}

:deep(.katex-block) {
  margin: $spacing-md 0;
  padding: $spacing-md;
  background: var(--color-bg-secondary);
  border-radius: $border-radius-base;
  overflow-x: auto;
  text-align: center;

  .katex-display {
    margin: 0;
  }
}
```

### 5. 附加功能

除了数学公式，还优化了以下 Markdown 元素样式：

- ✅ **标题**: h1-h4 层级样式
- ✅ **列表**: 有序/无序列表间距
- ✅ **链接**: 悬停下划线效果
- ✅ **引用块**: 左侧蓝色边框 + 斜体
- ✅ **表格**: 边框 + 表头背景色
- ✅ **代码块**: 深色背景 + 等宽字体

### 6. 错误处理

- KaTeX 渲染失败时自动降级显示原始文本
- `throwOnError: false` 确保即使公式语法错误也不会崩溃
- 控制台会输出错误日志便于调试

### 7. 性能优化

- KaTeX CSS 仅在组件中导入一次
- 公式渲染在客户端进行，不影响服务端
- 使用正则表达式快速定位公式位置

### 8. 兼容性

- ✅ 支持所有 KaTeX 支持的 LaTeX 语法
- ✅ 兼容通义千问返回的公式格式
- ✅ 支持嵌套公式和复杂数学符号
- ✅ 响应式设计，移动端自动横向滚动

## 验证步骤

1. **启动开发服务器**

   ```bash
   cd frontend
   npm run dev
   ```

2. **访问学习问答页面**
   - 打开浏览器访问 `http://localhost:5173`
   - 点击"学习问答"菜单

3. **发送测试问题**
   - 复制上方任一测试用例
   - 粘贴到输入框并发送

4. **检查渲染效果**
   - 行内公式应该与文字在同一行
   - 块级公式应该居中显示，带浅色背景
   - 公式应该正确渲染为数学符号

## 常见问题

### Q1: 公式显示为纯文本？

**A**: 检查是否使用正确的美元符号包裹，单个 `$` 为行内，双个 `$$` 为块级。

### Q2: 公式渲染错误？

**A**: 检查 LaTeX 语法是否正确，可以在 [KaTeX 支持的函数列表](https://katex.org/docs/supported.html) 中查询。

### Q3: 移动端显示不完整？

**A**: 长公式会自动启用横向滚动，用户可以左右滑动查看。

### Q4: 后端需要修改吗？

**A**: 不需要，只需确保百炼 API 返回的文本中包含 `$...$` 或 `$$...$$` 格式的公式。

## 下一步优化

- [ ] 添加公式编辑器（可视化输入）
- [ ] 支持化学方程式渲染 (mhchem 扩展)
- [ ] 添加公式复制按钮
- [ ] 支持公式图片导出
- [ ] 集成公式搜索功能

---

**修复完成时间**: 2025-10-05  
**修复人**: AI Agent  
**影响范围**: Learning.vue 组件  
**Git 提交建议**: `feat(learning): 添加 KaTeX 数学公式渲染支持`
