/**
 * Markdown格式化工具测试
 */

const { parseMarkdown, parseInlineStyles } = require('../utils/markdown-formatter.js');

// 测试用例
const testCases = [
  {
    name: '粗体测试',
    input: '这是**粗体文字**的测试',
    expected: '包含粗体样式',
  },
  {
    name: '斜体测试',
    input: '这是*斜体文字*的测试',
    expected: '包含斜体样式',
  },
  {
    name: '行内代码测试',
    input: '使用`console.log()`输出',
    expected: '包含代码样式',
  },
  {
    name: '混合样式测试',
    input: '**粗体**和*斜体*以及`代码`混合',
    expected: '包含多种样式',
  },
  {
    name: '代码块测试',
    input: '```\nfunction test() {\n  return true;\n}\n```',
    expected: '包含代码块',
  },
  {
    name: '标题测试',
    input: '## 二级标题\n这是内容',
    expected: '包含标题',
  },
  {
    name: '列表测试',
    input: '- 项目1\n- 项目2\n- 项目3',
    expected: '包含列表',
  },
  {
    name: '复杂混合测试',
    input:
      '# 主标题\n\n这是一个包含**粗体**、*斜体*和`代码`的段落。\n\n## 子标题\n\n- 列表项1\n- 列表项2\n\n```javascript\nconst x = 1;\n```',
    expected: '包含多种元素',
  },
];

console.log('========== Markdown格式化工具测试 ==========\n');

testCases.forEach((testCase, index) => {
  console.log(`测试 ${index + 1}: ${testCase.name}`);
  console.log('输入:', testCase.input);

  const result = parseMarkdown(testCase.input);
  console.log('输出:', JSON.stringify(result, null, 2));
  console.log('---\n');
});

// 测试行内样式解析
console.log('========== 行内样式解析测试 ==========\n');

const inlineTests = [
  '**粗体**测试',
  '*斜体*测试',
  '`代码`测试',
  '**粗体***和斜体*混合',
  '普通文字',
];

inlineTests.forEach((text, index) => {
  console.log(`行内测试 ${index + 1}:`, text);
  const result = parseInlineStyles(text);
  console.log('结果:', JSON.stringify(result, null, 2));
  console.log('---\n');
});

console.log('========== 测试完成 ==========');
