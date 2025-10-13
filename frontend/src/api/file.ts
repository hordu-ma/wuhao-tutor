/**
 * 文件上传相关的API接口
 */

import http from './http'
import { compressImage, getRecommendedOptions, isMobileDevice } from '@/utils/imageCompression'

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

    const response = await http.upload<ImageUploadResponse>(
      `${this.API_PREFIX}/upload-image-for-learning`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    // http.upload 已经解析过 data 字段，直接返回
    return response
  }

  /**
   * 上传图片供AI分析（新的推荐方法）
   * 自动压缩图片以优化移动端上传速度
   * @param file 图片文件
   * @param enableCompression 是否启用压缩（默认自动检测：移动端强制压缩）
   * @param onCompressionProgress 压缩进度回调
   * @returns AI可访问的图片URL和文件信息
   */
  static async uploadImageForAI(
    file: File,
    enableCompression: boolean = true,
    onCompressionProgress?: (progress: string) => void
  ): Promise<AIImageUploadResponse> {
    let fileToUpload = file

    // 自动压缩图片（移动端强制启用）
    if (enableCompression) {
      const mobile = isMobileDevice()
      const shouldCompress = mobile || file.size > 2 * 1024 * 1024 // 移动端或文件>2MB

      if (shouldCompress) {
        try {
          if (onCompressionProgress) {
            onCompressionProgress('正在压缩图片...')
          }

          console.log(`🔄 开始压缩图片: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`)
          const compressionOptions = getRecommendedOptions()
          const result = await compressImage(file, compressionOptions)

          if (result.wasCompressed) {
            fileToUpload = result.file
            const savedMB = ((result.originalSize - result.compressedSize) / 1024 / 1024).toFixed(2)
            console.log(
              `✅ 压缩完成: 减少 ${result.compressionRatio.toFixed(1)}% (节省 ${savedMB}MB)`
            )

            if (onCompressionProgress) {
              onCompressionProgress(
                `压缩完成，节省 ${savedMB}MB (${result.compressionRatio.toFixed(0)}%)`
              )
            }
          } else {
            console.log('ℹ️ 图片无需压缩')
          }
        } catch (error) {
          console.warn('⚠️ 图片压缩失败，使用原图上传:', error)
          // 压缩失败时使用原文件
          fileToUpload = file
        }
      }
    }

    const formData = new FormData()
    formData.append('file', fileToUpload)

    const response = await http.upload<AIImageUploadResponse>(
      `${this.API_PREFIX}/upload-for-ai`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    // http.upload 已经解析过 data 字段，直接返回
    return response
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
