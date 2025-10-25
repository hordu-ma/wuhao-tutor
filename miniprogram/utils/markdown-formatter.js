/**
 * 简单的Markdown格式化工具
 * 使用正则替换实现基础格式：粗体、斜体、代码等
 */

/**
 * 将Markdown文本解析为富文本段落数组
 * @param {string} text - 原始Markdown文本
 * @returns {Array} 富文本段落数组，每个段落包含多个行内元素
 */
function parseMarkdown(text) {
  if (!text) return [];

  // 按行分割文本
  const lines = text.split('\n');
  const blocks = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 空行跳过
    if (!line.trim()) {
      continue;
    }

    // 代码块检测（```）
    if (line.trim().startsWith('```')) {
      const codeLines = [];
      i++; // 跳过开始标记
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({
        type: 'code',
        content: codeLines.join('\n'),
      });
      continue;
    }

    // 标题检测
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        content: parseInlineStyles(headingMatch[2]),
      });
      continue;
    }

    // 列表检测
    const listMatch = line.match(/^(\s*)([-*+]|\d+\.)\s+(.+)$/);
    if (listMatch) {
      blocks.push({
        type: 'list',
        indent: listMatch[1].length,
        ordered: /^\d+\./.test(listMatch[2]),
        content: parseInlineStyles(listMatch[3]),
      });
      continue;
    }

    // 普通段落
    blocks.push({
      type: 'paragraph',
      content: parseInlineStyles(line),
    });
  }

  return blocks;
}

/**
 * 解析行内样式（粗体、斜体、代码、链接等）
 * @param {string} text - 文本内容
 * @returns {Array} 行内元素数组
 */
function parseInlineStyles(text) {
  const parts = [];
  let currentPos = 0;

  // 正则模式优先级：代码 > 粗体 > 斜体 > 链接
  const patterns = [
    // 行内代码: `code`
    {
      regex: /`([^`]+)`/g,
      type: 'code',
      getValue: match => match[1],
    },
    // 粗体: **bold** 或 __bold__
    {
      regex: /(\*\*|__)(.+?)\1/g,
      type: 'bold',
      getValue: match => match[2],
    },
    // 斜体: *italic* 或 _italic_
    {
      regex: /(\*|_)(.+?)\1/g,
      type: 'italic',
      getValue: match => match[2],
    },
    // 链接: [text](url)
    {
      regex: /\[([^\]]+)\]\(([^)]+)\)/g,
      type: 'link',
      getValue: match => ({ text: match[1], url: match[2] }),
    },
  ];

  // 查找所有匹配项并排序
  const matches = [];
  patterns.forEach(pattern => {
    let match;
    const regex = new RegExp(pattern.regex.source, 'g');
    while ((match = regex.exec(text)) !== null) {
      matches.push({
        type: pattern.type,
        start: match.index,
        end: regex.lastIndex,
        value: pattern.getValue(match),
        raw: match[0],
      });
    }
  });

  // 按位置排序
  matches.sort((a, b) => a.start - b.start);

  // 处理重叠（优先保留先出现的）
  const validMatches = [];
  let lastEnd = 0;
  matches.forEach(match => {
    if (match.start >= lastEnd) {
      validMatches.push(match);
      lastEnd = match.end;
    }
  });

  // 构建结果数组
  validMatches.forEach((match, index) => {
    // 添加匹配前的普通文本
    if (match.start > currentPos) {
      const plainText = text.substring(currentPos, match.start);
      if (plainText) {
        parts.push({ type: 'text', value: plainText });
      }
    }

    // 添加样式文本
    parts.push({ type: match.type, value: match.value });
    currentPos = match.end;
  });

  // 添加剩余的普通文本
  if (currentPos < text.length) {
    const plainText = text.substring(currentPos);
    if (plainText) {
      parts.push({ type: 'text', value: plainText });
    }
  }

  // 如果没有任何匹配，返回整个文本
  if (parts.length === 0 && text) {
    parts.push({ type: 'text', value: text });
  }

  return parts;
}

/**
 * 简化版本：只解析行内样式，不分段落
 * @param {string} text - 文本内容
 * @returns {Array} 行内元素数组
 */
function parseInlineOnly(text) {
  if (!text) return [{ type: 'text', value: '' }];

  // 将多行文本合并为一行处理
  const singleLine = text.replace(/\n/g, ' ');
  return parseInlineStyles(singleLine);
}

module.exports = {
  parseMarkdown,
  parseInlineStyles,
  parseInlineOnly,
};
