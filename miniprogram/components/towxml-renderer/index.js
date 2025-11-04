/**
 * Towxml 渲染组件
 * 负责将 Markdown 渲染为富文本，支持数学公式图片
 */

const { getTowxmlAdapter } = require('../../utils/towxml-adapter');
const { parseMarkdown } = require('../../utils/markdown-formatter');
const config = require('../../config/index');

Component({
  properties: {
    // Markdown 原始内容
    content: {
      type: String,
      value: '',
      observer: 'onContentChange',
    },
    // 是否启用 Towxml
    useTowxml: {
      type: Boolean,
      value: config.markdown?.useTowxml || false,
    },
    // 是否启用降级
    enableFallback: {
      type: Boolean,
      value: config.markdown?.enableFallback !== false,
    },
  },

  data: {
    // Towxml 渲染数据
    towxmlData: null,
    // 旧版 Markdown 解析结果（降级用）
    richContent: null,
    // 是否使用 Towxml 渲染
    renderMode: 'unknown', // 'towxml' | 'fallback' | 'unknown'
  },

  lifetimes: {
    attached() {
      this.renderContent();
    },
  },

  methods: {
    /**
     * 内容变化时重新渲染
     */
    onContentChange(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.renderContent();
      }
    },

    /**
     * 渲染内容（支持 Towxml 和降级）
     */
    renderContent() {
      const { content, useTowxml, enableFallback } = this.data;

      if (!content) {
        this.setData({
          towxmlData: null,
          richContent: null,
          renderMode: 'unknown',
        });
        return;
      }

      // 尝试使用 Towxml 渲染
      if (useTowxml) {
        const success = this.tryTowxmlRender(content);
        if (success) {
          return; // Towxml 渲染成功，直接返回
        }

        // Towxml 失败，检查是否启用降级
        if (!enableFallback) {
          console.error('[TowxmlRenderer] Towxml 渲染失败且降级已禁用');
          this.setData({ renderMode: 'unknown' });
          return;
        }

        console.warn('[TowxmlRenderer] Towxml 渲染失败，降级到旧渲染器');
      }

      // 使用旧渲染器（降级或用户配置）
      this.useFallbackRender(content);
    },

    /**
     * 尝试使用 Towxml 渲染
     * @param {string} content - Markdown 内容
     * @returns {boolean} 是否成功
     */
    tryTowxmlRender(content) {
      try {
        const adapter = getTowxmlAdapter();

        if (!adapter.isAvailable()) {
          console.warn('[TowxmlRenderer] Towxml 不可用');
          return false;
        }

        // 预处理 Markdown（优化数学公式）
        const preprocessed = adapter.preprocess(content);

        // 解析 Markdown
        const towxmlData = adapter.parse(preprocessed, {
          theme: config.markdown?.towxmlTheme || 'light',
        });

        if (!towxmlData) {
          console.warn('[TowxmlRenderer] Towxml 解析返回空');
          return false;
        }

        this.setData({
          towxmlData,
          richContent: null,
          renderMode: 'towxml',
        });

        console.log('[TowxmlRenderer] Towxml 渲染成功');
        return true;
      } catch (error) {
        console.error('[TowxmlRenderer] Towxml 渲染异常:', error);
        return false;
      }
    },

    /**
     * 使用旧渲染器（降级）
     * @param {string} content - Markdown 内容
     */
    useFallbackRender(content) {
      try {
        const richContent = parseMarkdown(content);

        this.setData({
          towxmlData: null,
          richContent,
          renderMode: 'fallback',
        });

        console.log('[TowxmlRenderer] 降级渲染成功');
      } catch (error) {
        console.error('[TowxmlRenderer] 降级渲染失败:', error);
        this.setData({
          towxmlData: null,
          richContent: null,
          renderMode: 'unknown',
        });
      }
    },

    /**
     * 处理图片点击（公式图片预览）
     */
    onFormulaImageTap(e) {
      const { alt } = e.currentTarget.dataset;
      wx.showToast({
        title: alt || '数学公式',
        icon: 'none',
        duration: 2000,
      });
    },

    /**
     * 处理 Rich Text 点击
     */
    onRichTextTap(e) {
      console.log('[TowxmlRenderer] Rich Text 点击:', e);
    },
  },
});
