/**
 * LaTeX 到 Unicode 转换测试
 * 用于验证转换功能是否正常工作
 */

const {
  convertLatexToUnicode,
  hasLatexFormula,
  convertToSuperscript,
  convertToSubscript,
} = require('../utils/latex-to-unicode.js');

/**
 * 测试用例
 */
const testCases = [
  // 基础希腊字母
  {
    name: '希腊字母 - pi',
    input: '圆周率 $\\pi$ 约等于 3.14',
    expected: '圆周率 π 约等于 3.14',
  },
  {
    name: '希腊字母 - alpha, beta',
    input: '$\\alpha + \\beta = \\gamma$',
    expected: 'α + β = γ',
  },

  // 上标和下标
  {
    name: '简单上标',
    input: '$x^2 + y^2 = z^2$',
    expected: 'x² + y² = z²',
  },
  {
    name: '复杂上标',
    input: '$a^{10} + b^{123}$',
    expected: 'a¹⁰ + b¹²³',
  },
  {
    name: '下标',
    input: '$x_1 + x_2 + x_{10}$',
    expected: 'x₁ + x₂ + x₁₀',
  },

  // 分数
  {
    name: '简单分数',
    input: '$\\frac{1}{2}$',
    expected: '(1)/(2)',
  },
  {
    name: '复杂分数',
    input: '$\\frac{a + b}{c - d}$',
    expected: '(a + b)/(c - d)',
  },
  {
    name: '分数优化 - 纯数字',
    input: '$\\frac{3}{4}$',
    expected: '3/4',
  },

  // 根号
  {
    name: '平方根',
    input: '$\\sqrt{2}$',
    expected: '√(2)',
  },
  {
    name: 'n次方根',
    input: '$\\sqrt[3]{8}$',
    expected: '³√(8)',
  },

  // 数学运算符
  {
    name: '基本运算符',
    input: '$a \\times b \\div c \\pm d$',
    expected: 'a × b ÷ c ± d',
  },
  {
    name: '关系符号',
    input: '$x \\leq y \\geq z \\neq w$',
    expected: 'x ≤ y ≥ z ≠ w',
  },
  {
    name: '约等于和相似',
    input: '$a \\approx b \\sim c$',
    expected: 'a ≈ b ∼ c',
  },

  // 特殊符号
  {
    name: '无穷大',
    input: '$\\lim_{x \\to \\infty}$',
    expected: 'lim_{x → ∞}',
  },
  {
    name: '求和符号',
    input: '$\\sum_{i=1}^{n}$',
    expected: '∑_{i=1}^{n}',
  },
  {
    name: '积分符号',
    input: '$\\int_{0}^{1} f(x) dx$',
    expected: '∫_{0}^{1} f(x) dx',
  },

  // 实际数学公式
  {
    name: '球的体积公式',
    input: '$V = \\frac{4}{3} \\pi r^3$',
    expected: 'V = 4/3 π r³',
  },
  {
    name: '圆的面积公式',
    input: '$S = \\pi r^2$',
    expected: 'S = π r²',
  },
  {
    name: '圆柱体积公式',
    input: '$V = \\pi r^2 h$',
    expected: 'V = π r² h',
  },
  {
    name: '二次方程求根公式',
    input: '$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$',
    expected: 'x = (-b ± √(b² - 4ac))/(2a)',
  },
  {
    name: '勾股定理',
    input: '$a^2 + b^2 = c^2$',
    expected: 'a² + b² = c²',
  },

  // 块级公式（去除$$）
  {
    name: '块级公式',
    input: '$$V = \\pi r^2 h$$',
    expected: 'V = π r² h',
  },

  // 混合文本
  {
    name: '文本中嵌入公式',
    input: '圆的面积公式是 $S = \\pi r^2$，其中 $r$ 是半径。',
    expected: '圆的面积公式是 S = π r²，其中 r 是半径。',
  },

  // \text{} 处理
  {
    name: 'text命令',
    input: '$S_{\\text{底}} = \\pi r^2$',
    expected: 'S_{底} = π r²',
  },

  // 边界情况
  {
    name: '空字符串',
    input: '',
    expected: '',
  },
  {
    name: '无公式文本',
    input: '这是普通文本',
    expected: '这是普通文本',
  },
];

/**
 * 运行单个测试用例
 */
function runTest(testCase) {
  const { name, input, expected } = testCase;
  const result = convertLatexToUnicode(input);
  const passed = result === expected;

  return {
    name,
    passed,
    input,
    expected,
    result,
  };
}

/**
 * 运行所有测试
 */
function runAllTests() {
  console.log('========================================');
  console.log('LaTeX 到 Unicode 转换测试');
  console.log('========================================\n');

  const results = testCases.map(runTest);
  const passedCount = results.filter(r => r.passed).length;
  const totalCount = results.length;

  // 显示测试结果
  results.forEach((result, index) => {
    const icon = result.passed ? '✅' : '❌';
    console.log(`${icon} 测试 ${index + 1}: ${result.name}`);

    if (!result.passed) {
      console.log(`   输入: "${result.input}"`);
      console.log(`   预期: "${result.expected}"`);
      console.log(`   实际: "${result.result}"`);
      console.log('');
    }
  });

  // 总结
  console.log('\n========================================');
  console.log(`测试结果: ${passedCount}/${totalCount} 通过`);
  console.log(`成功率: ${((passedCount / totalCount) * 100).toFixed(1)}%`);
  console.log('========================================');

  return {
    passed: passedCount,
    total: totalCount,
    allPassed: passedCount === totalCount,
  };
}

/**
 * 测试 hasLatexFormula 函数
 */
function testHasLatexFormula() {
  console.log('\n测试公式检测功能:\n');

  const testCases = [
    { text: '$x^2$', expected: true },
    { text: '$$a = b$$', expected: true },
    { text: '\\pi', expected: true },
    { text: '\\frac{1}{2}', expected: true },
    { text: '普通文本', expected: false },
    { text: '', expected: false },
    { text: null, expected: false },
  ];

  testCases.forEach(({ text, expected }) => {
    const result = hasLatexFormula(text);
    const passed = result === expected;
    const icon = passed ? '✅' : '❌';
    console.log(`${icon} hasLatexFormula("${text || '(null)'}"): ${result} (期望: ${expected})`);
  });
}

/**
 * 测试上标下标转换
 */
function testScriptConversion() {
  console.log('\n测试上标下标转换:\n');

  // 上标测试
  console.log('上标转换:');
  const superTests = [
    { input: '2', expected: '²' },
    { input: '10', expected: '¹⁰' },
    { input: 'n', expected: 'ⁿ' },
    { input: '-1', expected: '⁻¹' },
  ];

  superTests.forEach(({ input, expected }) => {
    const result = convertToSuperscript(input);
    const passed = result === expected;
    const icon = passed ? '✅' : '❌';
    console.log(`${icon} "${input}" → "${result}" (期望: "${expected}")`);
  });

  // 下标测试
  console.log('\n下标转换:');
  const subTests = [
    { input: '1', expected: '₁' },
    { input: '10', expected: '₁₀' },
    { input: '0', expected: '₀' },
  ];

  subTests.forEach(({ input, expected }) => {
    const result = convertToSubscript(input);
    const passed = result === expected;
    const icon = passed ? '✅' : '❌';
    console.log(`${icon} "${input}" → "${result}" (期望: "${expected}")`);
  });
}

// 运行所有测试
if (require.main === module) {
  const mainResult = runAllTests();
  testHasLatexFormula();
  testScriptConversion();

  console.log('\n🎉 测试完成!\n');

  // 返回退出代码
  process.exit(mainResult.allPassed ? 0 : 1);
}

module.exports = {
  runAllTests,
  runTest,
  testHasLatexFormula,
  testScriptConversion,
};
