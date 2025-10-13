/**
 * 图片压缩工具
 * 用于在上传前压缩图片，减少上传时间和带宽消耗
 * 特别针对移动端网络环境优化
 */

import imageCompression from 'browser-image-compression'

/**
 * 压缩配置选项
 */
export interface CompressionOptions {
  /** 最大文件大小（MB），默认 1.5MB */
  maxSizeMB?: number
  /** 最大宽度或高度（px），默认 1920px（保持AI识别质量） */
  maxWidthOrHeight?: number
  /** 使用 WebWorker 进行异步压缩，默认 true */
  useWebWorker?: boolean
  /** 图片质量（0-1），默认 0.8 */
  initialQuality?: number
  /** 文件类型，默认保持原格式 */
  fileType?: string
}

/**
 * 压缩结果
 */
export interface CompressionResult {
  /** 压缩后的文件 */
  file: File
  /** 原始大小（字节） */
  originalSize: number
  /** 压缩后大小（字节） */
  compressedSize: number
  /** 压缩率（百分比） */
  compressionRatio: number
  /** 是否进行了压缩 */
  wasCompressed: boolean
}

/**
 * 默认压缩配置
 */
const DEFAULT_OPTIONS: Required<Omit<CompressionOptions, 'fileType'>> = {
  maxSizeMB: 1.5, // 压缩到 1.5MB，适合移动网络上传
  maxWidthOrHeight: 1920, // 保持足够分辨率供AI分析
  useWebWorker: true, // 使用 WebWorker 避免阻塞UI
  initialQuality: 0.8, // 高质量压缩
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

/**
 * 检测是否为移动设备
 */
export function isMobileDevice(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * 检查文件是否需要压缩
 */
function needsCompression(file: File, maxSizeMB: number): boolean {
  const maxBytes = maxSizeMB * 1024 * 1024
  return file.size > maxBytes
}

/**
 * 压缩图片文件
 *
 * @param file 原始图片文件
 * @param options 压缩配置选项
 * @returns 压缩结果
 *
 * @example
 * ```typescript
 * const result = await compressImage(file, { maxSizeMB: 2 })
 * console.log(`压缩率: ${result.compressionRatio}%`)
 * console.log(`原始: ${formatFileSize(result.originalSize)}`)
 * console.log(`压缩后: ${formatFileSize(result.compressedSize)}`)
 * ```
 */
export async function compressImage(
  file: File,
  options: CompressionOptions = {}
): Promise<CompressionResult> {
  const originalSize = file.size
  const config = { ...DEFAULT_OPTIONS, ...options }

  // 如果文件已经小于目标大小，直接返回
  if (!needsCompression(file, config.maxSizeMB)) {
    console.log(`✅ 图片无需压缩: ${file.name} (${formatFileSize(originalSize)})`)
    return {
      file,
      originalSize,
      compressedSize: originalSize,
      compressionRatio: 0,
      wasCompressed: false,
    }
  }

  try {
    console.log(`🔄 开始压缩图片: ${file.name} (${formatFileSize(originalSize)})`)
    const startTime = Date.now()

    // 执行压缩
    const compressedBlob = await imageCompression(file, {
      maxSizeMB: config.maxSizeMB,
      maxWidthOrHeight: config.maxWidthOrHeight,
      useWebWorker: config.useWebWorker,
      initialQuality: config.initialQuality,
      fileType: options.fileType,
    })

    // 转换为 File 对象（保持原文件名）
    const compressedFile = new File([compressedBlob], file.name, {
      type: compressedBlob.type,
      lastModified: Date.now(),
    })

    const compressedSize = compressedFile.size
    const compressionRatio = ((originalSize - compressedSize) / originalSize) * 100
    const duration = Date.now() - startTime

    console.log(
      `✅ 压缩完成: ${formatFileSize(originalSize)} → ${formatFileSize(compressedSize)} ` +
        `(减少 ${compressionRatio.toFixed(1)}%, 耗时 ${duration}ms)`
    )

    return {
      file: compressedFile,
      originalSize,
      compressedSize,
      compressionRatio,
      wasCompressed: true,
    }
  } catch (error) {
    console.error('❌ 图片压缩失败:', error)
    // 压缩失败时返回原文件
    return {
      file,
      originalSize,
      compressedSize: originalSize,
      compressionRatio: 0,
      wasCompressed: false,
    }
  }
}

/**
 * 批量压缩图片
 *
 * @param files 图片文件数组
 * @param options 压缩配置选项
 * @param onProgress 进度回调（可选）
 * @returns 压缩结果数组
 */
export async function compressImages(
  files: File[],
  options: CompressionOptions = {},
  onProgress?: (current: number, total: number) => void
): Promise<CompressionResult[]> {
  console.log(`📦 开始批量压缩 ${files.length} 张图片...`)
  const results: CompressionResult[] = []

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const result = await compressImage(file, options)
    results.push(result)

    // 触发进度回调
    if (onProgress) {
      onProgress(i + 1, files.length)
    }
  }

  // 统计信息
  const totalOriginal = results.reduce((sum, r) => sum + r.originalSize, 0)
  const totalCompressed = results.reduce((sum, r) => sum + r.compressedSize, 0)
  const totalRatio = ((totalOriginal - totalCompressed) / totalOriginal) * 100

  console.log(
    `✅ 批量压缩完成: ${formatFileSize(totalOriginal)} → ${formatFileSize(totalCompressed)} ` +
      `(总减少 ${totalRatio.toFixed(1)}%)`
  )

  return results
}

/**
 * 获取推荐的压缩配置
 * 根据设备类型和网络环境返回最优配置
 */
export function getRecommendedOptions(): CompressionOptions {
  const mobile = isMobileDevice()

  // 移动设备使用更激进的压缩
  if (mobile) {
    return {
      maxSizeMB: 1.0, // 移动端压缩到 1MB
      maxWidthOrHeight: 1920,
      initialQuality: 0.75,
      useWebWorker: true,
    }
  }

  // 桌面设备使用标准压缩
  return {
    maxSizeMB: 1.5,
    maxWidthOrHeight: 1920,
    initialQuality: 0.8,
    useWebWorker: true,
  }
}

export { formatFileSize }
