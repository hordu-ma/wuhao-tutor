/**
 * 作业相关API接口
 */

import http from './http'
import type {
  HomeworkSubmitRequest,
  HomeworkRecord,
  HomeworkQueryParams,
  HomeworkListResponse,
  HomeworkCorrectionResult,
} from '@/types/homework'

/**
 * 作业API类
 */
export class HomeworkAPI {
  // API基础路径
  private readonly baseURL = '/homework'

  /**
   * 上传作业
   */
  async submitHomework(data: HomeworkSubmitRequest): Promise<HomeworkRecord> {
    const formData = new FormData()

    // 添加基本信息
    formData.append('subject', data.subject)
    formData.append('grade_level', data.grade_level.toString())
    if (data.title) formData.append('title', data.title)
    if (data.description) formData.append('description', data.description)

    // 添加图片文件
    data.images.forEach((file) => {
      formData.append('images', file)
    })

    const response = await http.post<HomeworkRecord>(`${this.baseURL}/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      showLoading: true,
      loadingText: '正在上传作业...',
    })

    return response
  }

  /**
   * 获取作业详情
   */
  async getHomework(homeworkId: string): Promise<HomeworkRecord> {
    const response = await http.get<HomeworkRecord>(`${this.baseURL}/${homeworkId}`)
    return response
  }

  /**
   * 获取作业列表
   */
  async getHomeworkList(params: HomeworkQueryParams = {}): Promise<HomeworkListResponse> {
    const response = await http.get<HomeworkListResponse>(`${this.baseURL}/list`, {
      params,
    })
    return response
  }

  /**
   * 批改作业
   */
  async correctHomework(homeworkId: string): Promise<HomeworkCorrectionResult> {
    const response = await http.post<HomeworkCorrectionResult>(
      `${this.baseURL}/${homeworkId}/correct`,
      {},
      {
        showLoading: true,
        loadingText: '正在批改作业，请稍候...',
      }
    )

    return response
  }

  /**
   * 删除作业
   */
  async deleteHomework(homeworkId: string): Promise<void> {
    await http.delete(`${this.baseURL}/${homeworkId}`, {
      showLoading: true,
      loadingText: '正在删除作业...',
    })
  }

  /**
   * 批量删除作业
   */
  async batchDeleteHomework(homeworkIds: string[]): Promise<void> {
    await http.post(
      `${this.baseURL}/batch-delete`,
      { homework_ids: homeworkIds },
      {
        showLoading: true,
        loadingText: '正在批量删除作业...',
      }
    )
  }

  /**
   * 获取作业统计信息
   */
  async getHomeworkStats(): Promise<{
    total: number
    completed: number
    processing: number
    failed: number
    by_subject: Record<string, number>
    by_grade: Record<string, number>
  }> {
    const response = await http.get(`${this.baseURL}/stats`)
    return response
  }

  /**
   * 重新批改作业
   */
  async retryCorrection(homeworkId: string): Promise<HomeworkCorrectionResult> {
    const response = await http.post<HomeworkCorrectionResult>(
      `${this.baseURL}/${homeworkId}/retry`,
      {},
      {
        showLoading: true,
        loadingText: '正在重新批改作业...',
      }
    )

    return response
  }

  /**
   * 更新作业信息
   */
  async updateHomework(
    homeworkId: string,
    data: Partial<Pick<HomeworkRecord, 'title' | 'description'>>
  ): Promise<HomeworkRecord> {
    const response = await http.put<HomeworkRecord>(`${this.baseURL}/${homeworkId}`, data)
    return response
  }

  /**
   * 获取OCR识别结果
   */
  async getOCRResult(homeworkId: string): Promise<{
    ocr_text: string
    confidence: number
    processing_time: number
  }> {
    const response = await http.get(`${this.baseURL}/${homeworkId}/ocr`)
    return response
  }

  /**
   * 导出作业数据
   */
  async exportHomework(params: HomeworkQueryParams = {}): Promise<Blob> {
    const response = await http.get(`${this.baseURL}/export`, {
      params,
      responseType: 'blob',
      showLoading: true,
      loadingText: '正在导出数据...',
    })
    return response
  }
}

// 导出单例实例
export const homeworkAPI = new HomeworkAPI()
