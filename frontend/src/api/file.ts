/**
 * 文件上传相关的API接口
 */

import http from './http'

export interface ImageUploadResponse {
  id: string
  original_filename: string
  stored_filename: string
  content_type: string
  size: number
  size_formatted: string
  category: string
  image_url: string // 供AI使用的完整URL
  preview_url: string
  uploaded_at: string
  success: boolean
}

export interface AIImageUploadResponse {
  ai_accessible_url: string // AI服务可直接访问的公开URL
  object_name: string
  file_size: number
  content_type: string
  upload_time: string
  storage_type: string
  warning?: string // 如果是本地存储会有警告
}

class FileAPI {
  private static readonly API_PREFIX = '/files'

  /**
   * 上传学习问答图片
   * @param file 图片文件
   * @returns 上传结果，包含图片URL
   */
  static async uploadLearningImage(file: File): Promise<ImageUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await http.upload<{ data: ImageUploadResponse }>(
      `${this.API_PREFIX}/upload-image-for-learning`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return response.data
  }

  /**
   * 上传图片供AI分析（新的推荐方法）
   * @param file 图片文件
   * @returns AI可访问的图片URL和文件信息
   */
  static async uploadImageForAI(file: File): Promise<AIImageUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await http.upload<{ data: AIImageUploadResponse }>(
      `${this.API_PREFIX}/upload-for-ai`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return response.data
  }

  /**
   * 批量上传学习问答图片
   * @param files 图片文件数组
   * @returns 上传结果数组
   */
  static async uploadLearningImages(files: File[]): Promise<ImageUploadResponse[]> {
    const uploadPromises = files.map((file) => this.uploadLearningImage(file))
    return Promise.all(uploadPromises)
  }
}

export default FileAPI
