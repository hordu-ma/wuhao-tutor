/**
 * Towxml Markdown 渲染适配器
 * 用于将 AI 返回的 Markdown（含数学公式图片）渲染为小程序富文本
 */

/**
 * 初始化 Towxml 实例
 */
class TowxmlAdapter {
  constructor() {
    // 延迟初始化，避免小程序启动时加载
    this._towxml = null;
    this._initialized = false;
  }

  /**
   * 懒加载初始化 Towxml
   */
  _ensureInitialized() {
    if (!this._initialized) {
      try {
        const Towxml = require('../miniprogram_npm/towxml/index');
        this._towxml = Towxml;
        this._initialized = true;
        console.log('[TowxmlAdapter] Towxml 初始化成功');
      } catch (error) {
        console.error('[TowxmlAdapter] Towxml 初始化失败:', error);
        this._initialized = false;
      }
    }
    return this._initialized;
  }

  /**
   * 将 Markdown 文本转换为 Towxml 可渲染的数据结构
   * @param {string} markdown - Markdown 文本（可能包含 HTML img 标签）
   * @param {object} options - 配置选项
   * @returns {object} Towxml 数据结构
   */
  parse(markdown, options = {}) {
    if (!this._ensureInitialized()) {
      // 降级：返回 null，使用旧渲染器
      console.warn('[TowxmlAdapter] Towxml 未初始化，降级到旧渲染器');
      return null;
    }

    try {
      // 使用 Towxml 解析 Markdown
      // Towxml 导出的是一个函数，直接调用
      const result = this._towxml(markdown, 'markdown', {
        base: options.base || '',
        theme: options.theme || 'light',
        highlight: false, // 禁用代码高亮，避免加载 languages 模块
      });

      console.log('[TowxmlAdapter] 解析成功');
      return result;
    } catch (error) {
      console.error('[TowxmlAdapter] 解析失败:', error);
      // 降级：返回 null
      return null;
    }
  }

  /**
   * 检查 Towxml 是否可用
   * @returns {boolean}
   */
  isAvailable() {
    return this._ensureInitialized();
  }

  /**
   * 预处理 Markdown（优化数学公式图片）
   * @param {string} markdown - 原始 Markdown
   * @returns {string} 处理后的 Markdown
   */
  preprocess(markdown) {
    if (!markdown) return '';

    // 1. 确保数学公式图片有正确的样式类
    let processed = markdown;

    // 2. 将块级公式容器转换为独立段落
    processed = processed.replace(
      /<div\s+class="math-formula-block"[^>]*>(.*?)<\/div>/g,
      '\n\n$1\n\n',
    );

    // 3. 优化图片标签，确保 Towxml 能正确识别
    processed = processed.replace(
      /<img\s+class="math-formula-(block|inline)"[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*\/?>/g,
      (match, type, src, alt) => {
        // 保持原样，Towxml 会处理 HTML img 标签
        return match;
      },
    );

    return processed;
  }
}

// 导出单例
let adapterInstance = null;

function getTowxmlAdapter() {
  if (!adapterInstance) {
    adapterInstance = new TowxmlAdapter();
  }
  return adapterInstance;
}

module.exports = {
  TowxmlAdapter,
  getTowxmlAdapter,
};
