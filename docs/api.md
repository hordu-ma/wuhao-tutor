# 五好伴学 API 使用文档

## 概述

五好伴学（wuhao-tutor）后端API提供了完整的AI学习助手功能，包括作业批改、学习问答、文件管理等核心服务。

## 基本信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **编码**: UTF-8

## 认证

所有API请求（除健康检查外）都需要在请求头中包含JWT token：

```http
Authorization: Bearer <your_jwt_token>
```

### 获取Token

```bash
# 用户登录获取token（需要实现auth端点）
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

## API端点

### 1. 健康检查 (`/health`)

#### 系统健康检查

```bash
# 获取系统整体健康状态
curl -X GET "http://localhost:8000/api/v1/health"
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.32,
      "details": "PostgreSQL/SQLite connection test"
    },
    "ai_service": {
      "status": "healthy",
      "response_time_ms": 125.67,
      "details": "Bailian AI service availability check"
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 8.91,
      "details": "Redis/Memory cache read/write test"
    },
    "storage": {
      "status": "healthy",
      "details": "File storage directory: ./uploads",
      "writable": true
    }
  },
  "total_response_time_ms": 156.43
}
```

#### 就绪检查

```bash
# 检查服务是否准备好接收请求
curl -X GET "http://localhost:8000/api/v1/health/readiness"
```

#### 活性检查

```bash
# 最简单的存活检查
curl -X GET "http://localhost:8000/api/v1/health/liveness"
```

### 2. 作业批改 (`/homework`)

#### 创建作业模板

```bash
curl -X POST "http://localhost:8000/api/v1/homework/templates" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小学数学基础练习",
    "subject": "math",
    "description": "适用于小学1-3年级的数学基础题练习",
    "template_content": "请完成以下数学题目...",
    "correction_criteria": "按照计算准确性、解题步骤完整性评分",
    "max_score": 100
  }'
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "小学数学基础练习",
    "subject": "math",
    "description": "适用于小学1-3年级的数学基础题练习",
    "template_content": "请完成以下数学题目...",
    "correction_criteria": "按照计算准确性、解题步骤完整性评分",
    "max_score": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "模板创建成功"
}
```

#### 获取模板列表

```bash
curl -X GET "http://localhost:8000/api/v1/homework/templates?page=1&size=10&subject=math" \
  -H "Authorization: Bearer <token>"
```

#### 提交作业

```bash
curl -X POST "http://localhost:8000/api/v1/homework/submit" \
  -H "Authorization: Bearer <token>" \
  -F "template_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "student_name=张小明" \
  -F "homework_file=@homework_image.jpg" \
  -F "additional_info=第一次提交数学作业"
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "template_id": "550e8400-e29b-41d4-a716-446655440000",
    "student_name": "张小明",
    "file_url": "/api/v1/files/660e8400-e29b-41d4-a716-446655440002/preview",
    "status": "processing",
    "submitted_at": "2024-01-15T10:35:00Z",
    "additional_info": "第一次提交数学作业"
  },
  "message": "作业提交成功，正在进行AI批改..."
}
```

#### 查询批改结果

```bash
curl -X GET "http://localhost:8000/api/v1/homework/submissions/660e8400-e29b-41d4-a716-446655440001/correction" \
  -H "Authorization: Bearer <token>"
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "submission_id": "660e8400-e29b-41d4-a716-446655440001",
    "total_score": 85,
    "max_score": 100,
    "overall_comment": "整体完成得不错，计算能力较强，但需要注意解题步骤的完整性。",
    "detailed_feedback": [
      {
        "question_number": 1,
        "score": 10,
        "max_score": 10,
        "comment": "答案正确，计算准确。"
      },
      {
        "question_number": 2,
        "score": 7,
        "max_score": 10,
        "comment": "答案正确，但缺少解题步骤说明。"
      }
    ],
    "suggestions": [
      "建议在解题时写出完整的计算步骤",
      "可以多练习类似的应用题"
    ],
    "corrected_at": "2024-01-15T10:37:30Z"
  },
  "message": "获取批改结果成功"
}
```

### 3. 学习问答 (`/learning`)

#### 向AI助手提问

```bash
curl -X POST "http://localhost:8000/api/v1/learning/ask" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请解释一下什么是质数，并给出几个例子",
    "question_type": "concept",
    "subject": "math",
    "topic": "数论基础",
    "difficulty_level": 3,
    "use_context": true,
    "include_history": true
  }'
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "question_id": "770e8400-e29b-41d4-a716-446655440003",
    "answer": "质数是指大于1的自然数中，只能被1和自己整除的数。换句话说，质数只有两个因数：1和它本身。\n\n例如：\n- 2是最小的质数，也是唯一的偶质数\n- 3、5、7、11、13、17、19、23都是质数\n- 1不是质数（因为它只有一个因数）\n- 4不是质数（因为它可以被1、2、4整除）\n\n质数在数学中非常重要，是数论研究的基础。",
    "sources": ["数学基础知识库", "小学数学教材"],
    "confidence_score": 0.95,
    "session_id": "880e8400-e29b-41d4-a716-446655440004",
    "response_time_ms": 1250,
    "created_at": "2024-01-15T10:40:00Z"
  },
  "message": "问题回答成功"
}
```

#### 创建学习会话

```bash
curl -X POST "http://localhost:8000/api/v1/learning/sessions" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "数学复习-质数与合数",
    "subject": "math",
    "topic": "数论基础",
    "learning_goals": ["理解质数概念", "掌握质数判断方法"],
    "difficulty_level": 3
  }'
```

#### 获取学习会话历史

```bash
curl -X GET "http://localhost:8000/api/v1/learning/sessions/880e8400-e29b-41d4-a716-446655440004/history" \
  -H "Authorization: Bearer <token>"
```

### 4. 文件管理 (`/files`)

#### 上传文件

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "category=homework" \
  -F "description=学生作业文件"
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440005",
    "original_filename": "document.pdf",
    "stored_filename": "990e8400-e29b-41d4-a716-446655440005.pdf",
    "content_type": "application/pdf",
    "size": 2048576,
    "category": "homework",
    "description": "学生作业文件",
    "download_url": "/api/v1/files/990e8400-e29b-41d4-a716-446655440005/download",
    "preview_url": "/api/v1/files/990e8400-e29b-41d4-a716-446655440005/preview",
    "uploaded_at": "2024-01-15T10:45:00Z"
  },
  "message": "文件上传成功"
}
```

#### 获取文件列表

```bash
curl -X GET "http://localhost:8000/api/v1/files?page=1&size=20&category=homework&file_type=image" \
  -H "Authorization: Bearer <token>"
```

#### 下载文件

```bash
curl -X GET "http://localhost:8000/api/v1/files/990e8400-e29b-41d4-a716-446655440005/download" \
  -H "Authorization: Bearer <token>" \
  -o downloaded_file.pdf
```

#### 预览文件

```bash
curl -X GET "http://localhost:8000/api/v1/files/990e8400-e29b-41d4-a716-446655440005/preview" \
  -H "Authorization: Bearer <token>"
```

## 错误处理

API使用标准HTTP状态码和统一的错误响应格式：

### 常见状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或token无效
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `413 Payload Too Large`: 文件太大
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务暂时不可用

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "数据验证失败: 文件大小超过10MB限制",
    "details": {
      "field": "homework_file",
      "max_size": "10MB",
      "actual_size": "15MB"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 数据模型

### 作业模板 (HomeworkTemplate)

```json
{
  "id": "uuid",
  "name": "string",
  "subject": "string",
  "description": "string",
  "template_content": "string",
  "correction_criteria": "string",
  "max_score": "number",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 作业提交 (HomeworkSubmission)

```json
{
  "id": "uuid",
  "template_id": "uuid",
  "student_name": "string",
  "file_url": "string",
  "status": "pending|processing|completed|failed",
  "submitted_at": "datetime",
  "completed_at": "datetime|null",
  "additional_info": "string|null"
}
```

### 批改结果 (HomeworkCorrection)

```json
{
  "submission_id": "uuid",
  "total_score": "number",
  "max_score": "number",
  "overall_comment": "string",
  "detailed_feedback": [
    {
      "question_number": "number",
      "score": "number",
      "max_score": "number",
      "comment": "string"
    }
  ],
  "suggestions": ["string"],
  "corrected_at": "datetime"
}
```

### 文件信息 (FileInfo)

```json
{
  "id": "uuid",
  "original_filename": "string",
  "stored_filename": "string",
  "content_type": "string",
  "size": "number",
  "category": "string",
  "description": "string|null",
  "download_url": "string",
  "preview_url": "string|null",
  "uploaded_at": "datetime",
  "download_count": "number"
}
```

## 使用限制

### 文件上传限制

- **最大文件大小**: 10MB
- **支持的图片格式**: JPEG, PNG, WebP, GIF
- **支持的文档格式**: PDF, TXT, DOC
- **批量上传限制**: 最多10个文件

### API调用限制

- **请求频率**: 100次/分钟/用户
- **并发连接**: 10个/用户
- **会话超时**: 24小时

### 存储限制

- **用户存储空间**: 100MB/用户
- **文件保存期限**: 1年

## SDK和工具

### Python SDK示例

```python
import requests
import json

class WuHaoTutorAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def create_template(self, template_data):
        """创建作业模板"""
        response = requests.post(
            f'{self.base_url}/homework/templates',
            headers=self.headers,
            json=template_data
        )
        return response.json()

    def submit_homework(self, template_id, student_name, file_path):
        """提交作业"""
        with open(file_path, 'rb') as f:
            files = {'homework_file': f}
            data = {
                'template_id': template_id,
                'student_name': student_name
            }
            headers = {'Authorization': self.headers['Authorization']}
            response = requests.post(
                f'{self.base_url}/homework/submit',
                headers=headers,
                files=files,
                data=data
            )
        return response.json()

    def ask_question(self, question_data):
        """向AI助手提问"""
        response = requests.post(
            f'{self.base_url}/learning/ask',
            headers=self.headers,
            json=question_data
        )
        return response.json()

# 使用示例
api = WuHaoTutorAPI('http://localhost:8000/api/v1', 'your_token_here')

# 创建模板
template = api.create_template({
    'name': '数学练习题',
    'subject': 'math',
    'description': '基础数学练习',
    'max_score': 100
})

# 提交作业
submission = api.submit_homework(
    template['data']['id'],
    '张三',
    'homework.jpg'
)

# 提问
answer = api.ask_question({
    'content': '什么是质数？',
    'subject': 'math',
    'question_type': 'concept'
})
```

### JavaScript/Node.js示例

```javascript
const axios = require('axios');

class WuHaoTutorAPI {
    constructor(baseURL, token) {
        this.client = axios.create({
            baseURL,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
    }

    async createTemplate(templateData) {
        const response = await this.client.post('/homework/templates', templateData);
        return response.data;
    }

    async askQuestion(questionData) {
        const response = await this.client.post('/learning/ask', questionData);
        return response.data;
    }

    async uploadFile(file, category = 'general') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);

        const response = await this.client.post('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    }
}

// 使用示例
const api = new WuHaoTutorAPI('http://localhost:8000/api/v1', 'your_token_here');

async function example() {
    try {
        // 提问
        const answer = await api.askQuestion({
            content: '请解释勾股定理',
            subject: 'math',
            question_type: 'concept',
            difficulty_level: 4
        });
        console.log('AI回答:', answer.data.answer);

        // 创建模板
        const template = await api.createTemplate({
            name: '几何练习',
            subject: 'math',
            description: '基础几何题目练习',
            max_score: 100
        });
        console.log('模板创建成功:', template.data.id);

    } catch (error) {
        console.error('API调用失败:', error.response?.data || error.message);
    }
}
```

## 最佳实践

### 1. 错误处理

```python
def safe_api_call(func, *args, **kwargs):
    """安全的API调用包装器"""
    try:
        response = func(*args, **kwargs)
        if response.get('success'):
            return response['data']
        else:
            raise Exception(f"API Error: {response.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network Error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {str(e)}")
```

### 2. 批量操作

```python
def batch_submit_homework(api, template_id, homework_files):
    """批量提交作业"""
    results = []
    for student_name, file_path in homework_files:
        try:
            result = api.submit_homework(template_id, student_name, file_path)
            results.append({
                'student': student_name,
                'success': True,
                'submission_id': result['data']['id']
            })
        except Exception as e:
            results.append({
                'student': student_name,
                'success': False,
                'error': str(e)
            })
    return results
```

### 3. 异步处理

```python
import asyncio
import aiohttp

async def check_correction_status(api, submission_ids):
    """异步检查多个作业的批改状态"""
    async def check_single(submission_id):
        try:
            result = await api.get_submission(submission_id)
            return {
                'id': submission_id,
                'status': result['data']['status'],
                'completed': result['data']['status'] == 'completed'
            }
        except Exception as e:
            return {
                'id': submission_id,
                'error': str(e),
                'completed': False
            }

    tasks = [check_single(sid) for sid in submission_ids]
    return await asyncio.gather(*tasks)
```

## 更新日志

### v1.0.0 (2024-01-15)

- 初始版本发布
- 支持作业批改功能
- 支持AI学习问答
- 支持文件管理
- 提供完整的健康检查机制

### 计划更新

- [ ] 添加用户管理API
- [ ] 支持实时通知
- [ ] 添加学习分析报告
- [ ] 支持更多文件格式
- [ ] 添加API版本控制

## 支持和反馈

如有问题或建议，请联系开发团队或提交issue到项目仓库。

---

*文档最后更新: 2024-01-15*
*API版本: v1.0.0*
