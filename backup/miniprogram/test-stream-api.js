/**
 * 微信小程序 SSE 流式 API 测试
 * @description 测试 askQuestionStream 流式响应功能
 */

const api = require('../api/index.js');

/**
 * 测试流式问答
 */
async function testStreamAPI() {
  console.log('========== 开始测试流式 API ==========');

  const params = {
    content: '1+1等于几？',
    session_id: undefined, // 自动创建新会话
    subject: 'math',
  };

  let chunkCount = 0;
  let fullContent = '';

  try {
    const response = await api.learning.askQuestionStream(params, chunk => {
      chunkCount++;
      console.log(`[Chunk ${chunkCount}]`, {
        type: chunk.type,
        content: chunk.content,
        contentLength: chunk.content?.length || 0,
        fullContentLength: chunk.full_content?.length || 0,
      });

      // 累积内容
      if (chunk.content) {
        fullContent += chunk.content;
      }
    });

    console.log('========== 流式测试完成 ==========');
    console.log('总块数:', chunkCount);
    console.log('累积内容长度:', fullContent.length);
    console.log('最终响应:', response);

    return {
      success: true,
      chunks: chunkCount,
      content: fullContent,
      response,
    };
  } catch (error) {
    console.error('========== 流式测试失败 ==========');
    console.error('错误:', error);

    return {
      success: false,
      error: error.message || error,
    };
  }
}

/**
 * 测试带图片的流式问答
 */
async function testStreamAPIWithImage() {
  console.log('========== 开始测试流式 API (带图片) ==========');

  // 注意：这里使用测试图片 URL，实际使用需要先上传图片
  const params = {
    content: '请分析这张图片',
    image_urls: [
      'https://example.com/test-image.jpg', // 替换为真实图片 URL
    ],
    session_id: undefined,
    subject: 'all',
  };

  let chunkCount = 0;

  try {
    const response = await api.learning.askQuestionStream(params, chunk => {
      chunkCount++;
      console.log(`[Image Chunk ${chunkCount}]`, chunk.type, chunk.content?.substring(0, 50));
    });

    console.log('========== 流式测试完成 (带图片) ==========');
    console.log('总块数:', chunkCount);
    console.log('最终响应:', response);

    return {
      success: true,
      chunks: chunkCount,
      response,
    };
  } catch (error) {
    console.error('========== 流式测试失败 (带图片) ==========');
    console.error('错误:', error);

    return {
      success: false,
      error: error.message || error,
    };
  }
}

module.exports = {
  testStreamAPI,
  testStreamAPIWithImage,
};
