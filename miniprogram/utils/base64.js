/**
 * 微信小程序 Base64 编码/解码工具
 * 替代浏览器的 btoa/atob API
 */

const BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';

/**
 * Base64 编码
 * @param {string} str - 要编码的字符串
 * @returns {string} Base64 编码后的字符串
 */
function btoa(str) {
  let output = '';
  let chr1, chr2, chr3;
  let enc1, enc2, enc3, enc4;
  let i = 0;

  // 转换为 UTF-8
  const utf8Str = unescape(encodeURIComponent(str));

  while (i < utf8Str.length) {
    chr1 = utf8Str.charCodeAt(i++);
    chr2 = utf8Str.charCodeAt(i++);
    chr3 = utf8Str.charCodeAt(i++);

    enc1 = chr1 >> 2;
    enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
    enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
    enc4 = chr3 & 63;

    if (isNaN(chr2)) {
      enc3 = enc4 = 64;
    } else if (isNaN(chr3)) {
      enc4 = 64;
    }

    output +=
      BASE64_CHARS.charAt(enc1) +
      BASE64_CHARS.charAt(enc2) +
      BASE64_CHARS.charAt(enc3) +
      BASE64_CHARS.charAt(enc4);
  }

  return output;
}

/**
 * Base64 解码
 * @param {string} str - Base64 编码的字符串
 * @returns {string} 解码后的字符串
 */
function atob(str) {
  let output = '';
  let chr1, chr2, chr3;
  let enc1, enc2, enc3, enc4;
  let i = 0;

  // 移除非 Base64 字符
  str = str.replace(/[^A-Za-z0-9\+\/\=]/g, '');

  while (i < str.length) {
    enc1 = BASE64_CHARS.indexOf(str.charAt(i++));
    enc2 = BASE64_CHARS.indexOf(str.charAt(i++));
    enc3 = BASE64_CHARS.indexOf(str.charAt(i++));
    enc4 = BASE64_CHARS.indexOf(str.charAt(i++));

    chr1 = (enc1 << 2) | (enc2 >> 4);
    chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
    chr3 = ((enc3 & 3) << 6) | enc4;

    output += String.fromCharCode(chr1);

    if (enc3 !== 64) {
      output += String.fromCharCode(chr2);
    }
    if (enc4 !== 64) {
      output += String.fromCharCode(chr3);
    }
  }

  // 从 UTF-8 转换回来
  try {
    output = decodeURIComponent(escape(output));
  } catch (e) {
    console.error('Base64 解码失败', e);
  }

  return output;
}

module.exports = {
  btoa,
  atob,
};
