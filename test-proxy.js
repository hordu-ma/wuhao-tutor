// 测试前端代理配置
const axios = require('axios')

async function testProxy() {
  console.log('Testing frontend proxy...')

  try {
    // 测试直接后端API
    console.log('\n1. Testing direct backend API:')
    const backendResponse = await axios.get('http://localhost:8000/api/v1/user/stats')
    console.log('✅ Backend API Status:', backendResponse.status)
    console.log('✅ Backend API Data:', JSON.stringify(backendResponse.data, null, 2))

    // 测试前端代理
    console.log('\n2. Testing frontend proxy:')
    const proxyResponse = await axios.get('http://localhost:5173/api/v1/user/stats')
    console.log('✅ Proxy Status:', proxyResponse.status)
    console.log('✅ Proxy Data:', JSON.stringify(proxyResponse.data, null, 2))
  } catch (error) {
    console.error('❌ Error:', error.message)
    if (error.response) {
      console.error('❌ Response Status:', error.response.status)
      console.error('❌ Response Data:', error.response.data)
    }
  }
}

testProxy()
