/**
 * LaTeX 到 Unicode 转换工具
 * 将常见的 LaTeX 数学符号转换为 Unicode 字符
 * 用于小程序端快速渲染数学公式
 */

/**
 * LaTeX 符号到 Unicode 的映射表
 */
const LATEX_TO_UNICODE = {
  // 希腊字母
  '\\alpha': 'α',
  '\\beta': 'β',
  '\\gamma': 'γ',
  '\\delta': 'δ',
  '\\epsilon': 'ε',
  '\\zeta': 'ζ',
  '\\eta': 'η',
  '\\theta': 'θ',
  '\\iota': 'ι',
  '\\kappa': 'κ',
  '\\lambda': 'λ',
  '\\mu': 'μ',
  '\\nu': 'ν',
  '\\xi': 'ξ',
  '\\pi': 'π',
  '\\rho': 'ρ',
  '\\sigma': 'σ',
  '\\tau': 'τ',
  '\\upsilon': 'υ',
  '\\phi': 'φ',
  '\\chi': 'χ',
  '\\psi': 'ψ',
  '\\omega': 'ω',

  // 大写希腊字母
  '\\Alpha': 'Α',
  '\\Beta': 'Β',
  '\\Gamma': 'Γ',
  '\\Delta': 'Δ',
  '\\Epsilon': 'Ε',
  '\\Zeta': 'Ζ',
  '\\Eta': 'Η',
  '\\Theta': 'Θ',
  '\\Iota': 'Ι',
  '\\Kappa': 'Κ',
  '\\Lambda': 'Λ',
  '\\Mu': 'Μ',
  '\\Nu': 'Ν',
  '\\Xi': 'Ξ',
  '\\Pi': 'Π',
  '\\Rho': 'Ρ',
  '\\Sigma': 'Σ',
  '\\Tau': 'Τ',
  '\\Upsilon': 'Υ',
  '\\Phi': 'Φ',
  '\\Chi': 'Χ',
  '\\Psi': 'Ψ',
  '\\Omega': 'Ω',

  // 数学运算符
  '\\times': '×',
  '\\div': '÷',
  '\\pm': '±',
  '\\mp': '∓',
  '\\cdot': '·',
  '\\ast': '∗',
  '\\star': '⋆',
  '\\circ': '∘',
  '\\bullet': '•',
  '\\oplus': '⊕',
  '\\ominus': '⊖',
  '\\otimes': '⊗',
  '\\oslash': '⊘',

  // 关系符号
  '\\leq': '≤',
  '\\geq': '≥',
  '\\le': '≤',
  '\\ge': '≥',
  '\\neq': '≠',
  '\\ne': '≠',
  '\\approx': '≈',
  '\\equiv': '≡',
  '\\sim': '∼',
  '\\simeq': '≃',
  '\\cong': '≅',
  '\\propto': '∝',
  '\\ll': '≪',
  '\\gg': '≫',
  '\\subset': '⊂',
  '\\supset': '⊃',
  '\\subseteq': '⊆',
  '\\supseteq': '⊇',
  '\\in': '∈',
  '\\notin': '∉',
  '\\ni': '∋',
  '\\not\\in': '∉',

  // 箭头
  '\\leftarrow': '←',
  '\\rightarrow': '→',
  '\\leftrightarrow': '↔',
  '\\Leftarrow': '⇐',
  '\\Rightarrow': '⇒',
  '\\Leftrightarrow': '⇔',
  '\\uparrow': '↑',
  '\\downarrow': '↓',
  '\\updownarrow': '↕',
  '\\to': '→',

  // 逻辑符号
  '\\forall': '∀',
  '\\exists': '∃',
  '\\neg': '¬',
  '\\land': '∧',
  '\\lor': '∨',
  '\\wedge': '∧',
  '\\vee': '∨',
  '\\cap': '∩',
  '\\cup': '∪',
  '\\emptyset': '∅',
  '\\varnothing': '∅',

  // 其他符号
  '\\infty': '∞',
  '\\partial': '∂',
  '\\nabla': '∇',
  '\\int': '∫',
  '\\iint': '∬',
  '\\iiint': '∭',
  '\\oint': '∮',
  '\\sum': '∑',
  '\\prod': '∏',
  '\\coprod': '∐',
  '\\sqrt': '√',
  '\\angle': '∠',
  '\\perp': '⊥',
  '\\parallel': '∥',
  '\\degree': '°',
  '\\prime': '′',
  '\\hbar': 'ℏ',
  '\\ell': 'ℓ',
  '\\Re': 'ℜ',
  '\\Im': 'ℑ',
  '\\aleph': 'ℵ',
  '\\wp': '℘',

  // 特殊文本
  '\\text{底}': '底',
  '\\text{侧}': '侧',
  '\\text{高}': '高',
  '\\text{长}': '长',
  '\\text{宽}': '宽',
  '\\text{体积}': '体积',
  '\\text{面积}': '面积',
  '\\text{周长}': '周长',
};

/**
 * 上标数字映射 (⁰¹²³⁴⁵⁶⁷⁸⁹)
 */
const SUPERSCRIPT_DIGITS = {
  '0': '⁰',
  '1': '¹',
  '2': '²',
  '3': '³',
  '4': '⁴',
  '5': '⁵',
  '6': '⁶',
  '7': '⁷',
  '8': '⁸',
  '9': '⁹',
  '-': '⁻',
  '+': '⁺',
  '=': '⁼',
  '(': '⁽',
  ')': '⁾',
  'n': 'ⁿ',
};

/**
 * 下标数字映射 (₀₁₂₃₄₅₆₇₈₉)
 */
const SUBSCRIPT_DIGITS = {
  '0': '₀',
  '1': '₁',
  '2': '₂',
  '3': '₃',
  '4': '₄',
  '5': '₅',
  '6': '₆',
  '7': '₇',
  '8': '₈',
  '9': '₉',
  '-': '₋',
  '+': '₊',
  '=': '₌',
  '(': '₍',
  ')': '₎',
};

/**
 * 转换 LaTeX 公式为 Unicode
 * @param {string} text - 包含 LaTeX 公式的文本
 * @returns {string} - 转换后的文本
 */
function convertLatexToUnicode(text) {
  if (!text || typeof text !== 'string') {
    return text || '';
  }

  let result = text;

  // 1. 处理 \text{...} 命令
  result = result.replace(/\\text\{([^}]+)\}/g, '$1');

  // 2. 处理分数 \frac{a}{b} → (a)/(b)
  result = result.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)');

  // 3. 处理根号 \sqrt{x} → √(x) 或 \sqrt[n]{x} → ⁿ√(x)
  result = result.replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, (match, n, content) => {
    const superN = convertToSuperscript(n);
    return `${superN}√(${content})`;
  });
  result = result.replace(/\\sqrt\{([^}]+)\}/g, '√($1)');

  // 4. 替换所有 LaTeX 符号
  for (const [latex, unicode] of Object.entries(LATEX_TO_UNICODE)) {
    // 使用全局替换，转义反斜杠
    const escapedLatex = latex.replace(/\\/g, '\\\\');
    const regex = new RegExp(escapedLatex, 'g');
    result = result.replace(regex, unicode);
  }

  // 5. 处理上标 x^2 → x² 或 x^{10} → x¹⁰
  // 先处理花括号形式 x^{...}
  result = result.replace(/([a-zA-Z0-9\u03B1-\u03C9\u0391-\u03A9πΠ])\^\{([^}]+)\}/g, (match, base, exp) => {
    return base + convertToSuperscript(exp);
  });
  // 再处理简单形式 x^2
  result = result.replace(/([a-zA-Z0-9\u03B1-\u03C9\u0391-\u03A9πΠ])\^([0-9])/g, (match, base, exp) => {
    return base + (SUPERSCRIPT_DIGITS[exp] || exp);
  });

  // 6. 处理下标 x_1 → x₁ 或 x_{10} → x₁₀
  // 先处理花括号形式 x_{...}
  result = result.replace(/([a-zA-Z0-9\u03B1-\u03C9\u0391-\u03A9πΠ])_\{([^}]+)\}/g, (match, base, sub) => {
    return base + convertToSubscript(sub);
  });
  // 再处理简单形式 x_1
  result = result.replace(/([a-zA-Z0-9\u03B1-\u03C9\u0391-\u03A9πΠ])_([0-9])/g, (match, base, sub) => {
    return base + (SUBSCRIPT_DIGITS[sub] || sub);
  });

  // 7. 移除美元符号标记
  result = result.replace(/\$\$/g, ''); // 块级公式标记
  result = result.replace(/\$/g, ''); // 行内公式标记

  // 8. 清理多余的花括号和反斜杠
  result = result.replace(/\\{/g, '{');
  result = result.replace(/\\}/g, '}');
  result = result.replace(/\\\\/g, '\\');

  // 9. 处理常见的数学表达式优化
  // 例如: (4)/(3) → 4/3 (如果分子分母都是简单数字)
  result = result.replace(/\((\d+)\)\/\((\d+)\)/g, '$1/$2');

  return result;
}

/**
 * 将文本转换为上标
 * @param {string} text - 要转换的文本
 * @returns {string} - 上标文本
 */
function convertToSuperscript(text) {
  let result = '';
  for (const char of text) {
    result += SUPERSCRIPT_DIGITS[char] || char;
  }
  return result;
}

/**
 * 将文本转换为下标
 * @param {string} text - 要转换的文本
 * @returns {string} - 下标文本
 */
function convertToSubscript(text) {
  let result = '';
  for (const char of text) {
    result += SUBSCRIPT_DIGITS[char] || char;
  }
  return result;
}

/**
 * 检测文本中是否包含 LaTeX 公式
 * @param {string} text - 文本
 * @returns {boolean} - 是否包含公式
 */
function hasLatexFormula(text) {
  if (!text || typeof text !== 'string') {
    return false;
  }

  // 检测 $ 或 $$ 标记
  if (text.includes('$')) {
    return true;
  }

  // 检测常见 LaTeX 命令
  const latexPatterns = [
    /\\frac\{/,
    /\\sqrt\{/,
    /\\sum/,
    /\\int/,
    /\\pi/,
    /\\alpha/,
    /\\beta/,
    /\\theta/,
    /\\times/,
    /\\div/,
    /\\leq/,
    /\\geq/,
  ];

  return latexPatterns.some(pattern => pattern.test(text));
}

/**
 * 批量转换消息列表中的 LaTeX
 * @param {Array} messages - 消息列表
 * @returns {Array} - 转换后的消息列表
 */
function convertMessagesLatex(messages) {
  if (!Array.isArray(messages)) {
    return messages;
  }

  return messages.map(msg => {
    if (msg.content && hasLatexFormula(msg.content)) {
      return {
        ...msg,
        content: convertLatexToUnicode(msg.content),
      };
    }
    return msg;
  });
}

module.exports = {
  convertLatexToUnicode,
  hasLatexFormula,
  convertMessagesLatex,
  convertToSuperscript,
  convertToSubscript,
};
