/**
 * Towxml 自定义配置
 * 禁用代码高亮以避免加载 languages 模块
 */

module.exports = {
  // 数学公式解析API（使用默认的外部服务）
  latex: {
    api: 'http://towxml.vvadd.com/?tex',
  },

  // yuml图解析API
  yuml: {
    api: 'http://towxml.vvadd.com/?yuml',
  },

  // markdown解析配置
  markdown: [
    'sub', // 下标支持
    'sup', // 上标支持
    'ins', // 文本删除线支持
    'mark', // 文本高亮支持
    'emoji', // emoji表情支持
    'todo', // todo支持
  ],

  // 禁用代码高亮（避免加载 languages 模块）
  highlight: [],
};
