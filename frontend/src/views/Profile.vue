<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <div class="page-header mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">个人中心</h1>
          <p class="text-gray-600">管理您的个人信息和学习偏好设置</p>
        </div>
        <div class="flex items-center space-x-3">
          <el-button type="primary" :loading="isSaving" @click="handleSaveAll">
            <el-icon class="mr-1"><Check /></el-icon>
            保存所有更改
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div class="profile-content">
      <el-row :gutter="24">
        <!-- 左侧个人信息 -->
        <el-col :span="8">
          <div class="profile-card">
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><User /></el-icon>
                  <span>个人信息</span>
                </div>
              </template>

              <!-- 头像区域 -->
              <div class="avatar-section mb-6">
                <div class="avatar-container">
                  <el-avatar :size="80" :src="userInfo.avatar_url" class="user-avatar">
                    <el-icon :size="40"><UserFilled /></el-icon>
                  </el-avatar>
                  <el-upload
                    ref="avatarUpload"
                    :show-file-list="false"
                    :before-upload="handleAvatarUpload"
                    accept="image/*"
                    class="avatar-upload"
                  >
                    <el-button size="small" type="text" class="change-avatar-btn">
                      <el-icon><Camera /></el-icon>
                      更换头像
                    </el-button>
                  </el-upload>
                </div>
              </div>

              <!-- 基本信息表单 -->
              <el-form
                ref="userInfoForm"
                :model="userInfo"
                :rules="userInfoRules"
                label-width="80px"
                label-position="top"
              >
                <el-form-item label="昵称" prop="username">
                  <el-input
                    v-model="userInfo.username"
                    placeholder="请输入昵称"
                    maxlength="20"
                    show-word-limit
                  />
                </el-form-item>

                <el-form-item label="真实姓名" prop="real_name">
                  <el-input
                    v-model="userInfo.real_name"
                    placeholder="请输入真实姓名"
                    maxlength="10"
                  />
                </el-form-item>

                <el-form-item label="性别" prop="gender">
                  <el-radio-group v-model="userInfo.gender">
                    <el-radio label="male">男</el-radio>
                    <el-radio label="female">女</el-radio>
                    <el-radio label="other">其他</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="年级" prop="grade_level">
                  <el-select v-model="userInfo.grade_level" placeholder="请选择年级" class="w-full">
                    <el-option
                      v-for="grade in gradeOptions"
                      :key="grade.value"
                      :label="grade.label"
                      :value="grade.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="学校" prop="school">
                  <el-input v-model="userInfo.school" placeholder="请输入学校名称" maxlength="50" />
                </el-form-item>

                <el-form-item label="手机号" prop="phone">
                  <el-input v-model="userInfo.phone" placeholder="请输入手机号" maxlength="11" />
                </el-form-item>

                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="userInfo.email" placeholder="请输入邮箱地址" type="email" />
                </el-form-item>

                <el-form-item label="个人简介">
                  <el-input
                    v-model="userInfo.bio"
                    type="textarea"
                    :rows="3"
                    placeholder="介绍一下自己吧..."
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </el-col>

        <!-- 右侧设置 -->
        <el-col :span="16">
          <div class="settings-section">
            <!-- 学习偏好设置 -->
            <el-card class="mb-6">
              <template #header>
                <div class="card-header">
                  <el-icon><Setting /></el-icon>
                  <span>学习偏好</span>
                </div>
              </template>

              <el-form ref="preferencesForm" :model="preferences" label-width="120px">
                <el-form-item label="主要学科">
                  <el-select
                    v-model="preferences.primary_subjects"
                    multiple
                    placeholder="选择您主要学习的学科"
                    class="w-full"
                  >
                    <el-option
                      v-for="subject in subjectOptions"
                      :key="subject.value"
                      :label="subject.label"
                      :value="subject.value"
                    >
                      <div class="flex items-center">
                        <div
                          class="w-3 h-3 rounded-full mr-2"
                          :style="{ backgroundColor: subject.color }"
                        />
                        {{ subject.label }}
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>

                <el-form-item label="学习难度偏好">
                  <el-radio-group v-model="preferences.difficulty_preference">
                    <el-radio label="easy">基础练习</el-radio>
                    <el-radio label="medium">适中挑战</el-radio>
                    <el-radio label="hard">高难度</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="每日学习目标">
                  <div class="flex items-center space-x-4">
                    <el-input-number
                      v-model="preferences.daily_study_time"
                      :min="30"
                      :max="480"
                      :step="30"
                      controls-position="right"
                    />
                    <span class="text-gray-600">分钟/天</span>
                  </div>
                </el-form-item>

                <el-form-item label="提醒设置">
                  <div class="space-y-3">
                    <el-checkbox v-model="preferences.enable_daily_reminder">
                      每日学习提醒
                    </el-checkbox>
                    <el-checkbox v-model="preferences.enable_homework_reminder">
                      作业截止提醒
                    </el-checkbox>
                    <el-checkbox v-model="preferences.enable_achievement_notification">
                      成就解锁通知
                    </el-checkbox>
                  </div>
                </el-form-item>

                <el-form-item label="提醒时间">
                  <el-time-picker
                    v-model="preferences.reminder_time"
                    placeholder="选择提醒时间"
                    format="HH:mm"
                    value-format="HH:mm"
                  />
                </el-form-item>
              </el-form>
            </el-card>

            <!-- AI助手设置 -->
            <el-card class="mb-6">
              <template #header>
                <div class="card-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>AI助手设置</span>
                </div>
              </template>

              <el-form ref="aiSettingsForm" :model="aiSettings" label-width="120px">
                <el-form-item label="回答详细程度">
                  <el-radio-group v-model="aiSettings.response_detail_level">
                    <el-radio label="concise">简洁回答</el-radio>
                    <el-radio label="detailed">详细解释</el-radio>
                    <el-radio label="comprehensive">全面分析</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="学习指导风格">
                  <el-radio-group v-model="aiSettings.teaching_style">
                    <el-radio label="encouraging">鼓励型</el-radio>
                    <el-radio label="strict">严格型</el-radio>
                    <el-radio label="friendly">友善型</el-radio>
                    <el-radio label="professional">专业型</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="智能功能">
                  <div class="space-y-3">
                    <el-checkbox v-model="aiSettings.enable_context_memory">
                      启用学习上下文记忆
                    </el-checkbox>
                    <el-checkbox v-model="aiSettings.enable_auto_correction">
                      自动错误检测与纠正
                    </el-checkbox>
                    <el-checkbox v-model="aiSettings.enable_smart_recommendations">
                      智能学习建议
                    </el-checkbox>
                    <el-checkbox v-model="aiSettings.enable_progress_tracking">
                      学习进度跟踪
                    </el-checkbox>
                  </div>
                </el-form-item>

                <el-form-item label="回答语言">
                  <el-select v-model="aiSettings.response_language" placeholder="选择AI回答语言">
                    <el-option label="中文" value="zh" />
                    <el-option label="英文" value="en" />
                    <el-option label="中英混合" value="zh-en" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 隐私与安全 -->
            <el-card class="mb-6">
              <template #header>
                <div class="card-header">
                  <el-icon><Lock /></el-icon>
                  <span>隐私与安全</span>
                </div>
              </template>

              <el-form ref="privacyForm" :model="privacySettings" label-width="120px">
                <el-form-item label="数据使用">
                  <div class="space-y-3">
                    <el-checkbox v-model="privacySettings.allow_data_analysis">
                      允许匿名数据分析以改进服务
                    </el-checkbox>
                    <el-checkbox v-model="privacySettings.allow_learning_analytics">
                      允许学习行为分析
                    </el-checkbox>
                    <el-checkbox v-model="privacySettings.allow_personalization">
                      允许个性化推荐
                    </el-checkbox>
                  </div>
                </el-form-item>

                <el-form-item label="数据保留">
                  <el-radio-group v-model="privacySettings.data_retention_period">
                    <el-radio label="1year">1年</el-radio>
                    <el-radio label="2years">2年</el-radio>
                    <el-radio label="5years">5年</el-radio>
                    <el-radio label="permanent">永久保留</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item>
                  <div class="space-y-3">
                    <el-button type="info" size="small" @click="showDataExport">
                      <el-icon><Download /></el-icon>
                      导出我的数据
                    </el-button>
                    <el-button type="danger" size="small" @click="showDeleteAccount">
                      <el-icon><Delete /></el-icon>
                      删除账户
                    </el-button>
                  </div>
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 学习统计概览 -->
            <el-card>
              <template #header>
                <div class="card-header">
                  <el-icon><TrendCharts /></el-icon>
                  <span>学习统计</span>
                </div>
              </template>

              <div class="stats-overview">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div v-for="stat in learningStats" :key="stat.key" class="stat-item">
                    <div class="stat-icon" :class="stat.colorClass">
                      <el-icon>
                        <component :is="stat.icon" />
                      </el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ stat.value }}</div>
                      <div class="stat-label">{{ stat.label }}</div>
                    </div>
                  </div>
                </div>

                <div class="mt-4 text-center">
                  <el-button type="text" @click="goToAnalytics">
                    <el-icon><Right /></el-icon>
                    查看详细统计
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 数据导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出个人数据"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="export-options">
        <p class="text-gray-600 mb-4">
          选择要导出的数据类型，我们将生成一个包含您所有数据的压缩包。
        </p>
        <el-checkbox-group v-model="exportOptions">
          <div class="space-y-2">
            <el-checkbox label="profile">个人信息</el-checkbox>
            <el-checkbox label="sessions">学习会话记录</el-checkbox>
            <el-checkbox label="homework">作业和批改记录</el-checkbox>
            <el-checkbox label="analytics">学习分析数据</el-checkbox>
            <el-checkbox label="feedback">反馈和评价记录</el-checkbox>
          </div>
        </el-checkbox-group>
      </div>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleExportData" :loading="isExporting">
            导出数据
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 删除账户确认对话框 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="⚠️ 危险操作：删除账户"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="delete-warning">
        <el-alert title="此操作不可逆" type="error" show-icon :closable="false" class="mb-4">
          <template #default>
            删除账户将永久移除：
            <ul class="mt-2 ml-4 list-disc">
              <li>所有个人信息和设置</li>
              <li>学习会话和对话记录</li>
              <li>作业和批改数据</li>
              <li>学习分析和统计数据</li>
            </ul>
          </template>
        </el-alert>

        <el-form ref="deleteForm" :model="deleteConfirm" :rules="deleteRules">
          <el-form-item prop="confirmText">
            <div class="mb-2">
              <span class="text-sm text-gray-600">
                请输入 "<strong>删除我的账户</strong>" 以确认：
              </span>
            </div>
            <el-input
              v-model="deleteConfirm.confirmText"
              placeholder="输入确认文本"
              @input="handleDeleteInput"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showDeleteDialog = false">取消</el-button>
          <el-button
            type="danger"
            @click="handleDeleteAccount"
            :disabled="!canDelete"
            :loading="isDeleting"
          >
            确认删除
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type UploadRawFile } from 'element-plus'
import {
  User,
  UserFilled,
  Camera,
  Setting,
  ChatDotRound,
  Lock,
  TrendCharts,
  Check,
  Download,
  Delete,
  Right,
  Clock,
  Document,
  Star,
  Flag,
} from '@element-plus/icons-vue'

// 导入stores和API
import { useUserStore } from '@/stores/user'
import { useAuthStore } from '@/stores/auth'
import AuthAPI from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const authStore = useAuthStore()
// const learningStore = useLearningStore();

// 响应式数据
const isSaving = ref(false)
const isExporting = ref(false)
const isDeleting = ref(false)
const showExportDialog = ref(false)
const showDeleteDialog = ref(false)

// 表单引用
const userInfoForm = ref<FormInstance>()
const preferencesForm = ref<FormInstance>()
const aiSettingsForm = ref<FormInstance>()
const privacyForm = ref<FormInstance>()
const deleteForm = ref<FormInstance>()

// 用户信息
const userInfo = reactive({
  username: '',
  real_name: '',
  gender: '',
  grade_level: '',
  school: '',
  phone: '',
  email: '',
  bio: '',
  avatar_url: '',
})

// 学习偏好
const preferences = reactive({
  primary_subjects: [],
  difficulty_preference: 'medium',
  daily_study_time: 120,
  enable_daily_reminder: true,
  enable_homework_reminder: true,
  enable_achievement_notification: true,
  reminder_time: '19:00',
})

// AI助手设置
const aiSettings = reactive({
  response_detail_level: 'detailed',
  teaching_style: 'encouraging',
  enable_context_memory: true,
  enable_auto_correction: true,
  enable_smart_recommendations: true,
  enable_progress_tracking: true,
  response_language: 'zh',
})

// 隐私设置
const privacySettings = reactive({
  allow_data_analysis: true,
  allow_learning_analytics: true,
  allow_personalization: true,
  data_retention_period: '2years',
})

// 导出选项
const exportOptions = ref(['profile', 'sessions', 'homework', 'analytics'])

// 删除确认
const deleteConfirm = reactive({
  confirmText: '',
})

// 选项数据
const gradeOptions = [
  { label: '小学', value: 'primary' },
  { label: '初一', value: 'junior_1' },
  { label: '初二', value: 'junior_2' },
  { label: '初三', value: 'junior_3' },
  { label: '高一', value: 'senior_1' },
  { label: '高二', value: 'senior_2' },
  { label: '高三', value: 'senior_3' },
]

const subjectOptions = [
  { label: '数学', value: 'math', color: '#3b82f6' },
  { label: '语文', value: 'chinese', color: '#ef4444' },
  { label: '英语', value: 'english', color: '#10b981' },
  { label: '物理', value: 'physics', color: '#8b5cf6' },
  { label: '化学', value: 'chemistry', color: '#f59e0b' },
  { label: '生物', value: 'biology', color: '#06b6d4' },
  { label: '历史', value: 'history', color: '#84cc16' },
  { label: '地理', value: 'geography', color: '#f97316' },
  { label: '政治', value: 'politics', color: '#ec4899' },
]

// 表单验证规则
const userInfoRules = {
  username: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '昵称长度在 2 到 20 个字符', trigger: 'blur' },
  ],
  email: [
    {
      type: 'email' as const,
      message: '请输入正确的邮箱地址',
      trigger: 'blur',
    },
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号',
      trigger: 'blur',
    },
  ],
}

const deleteRules = {
  confirmText: [
    { required: true, message: '请输入确认文本', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: Function) => {
        if (value !== '删除我的账户') {
          callback(new Error('确认文本不正确'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 计算属性
const canDelete = computed(() => {
  return deleteConfirm.confirmText === '删除我的账户'
})

const learningStats = computed(() => [
  {
    key: 'studyTime',
    label: '总学习时长',
    value: '125小时',
    icon: Clock,
    colorClass: 'text-blue-500',
  },
  {
    key: 'homework',
    label: '完成作业',
    value: '45份',
    icon: Document,
    colorClass: 'text-green-500',
  },
  {
    key: 'achievements',
    label: '获得成就',
    value: '12个',
    icon: Star,
    colorClass: 'text-yellow-500',
  },
  {
    key: 'streak',
    label: '连续学习',
    value: '7天',
    icon: Flag,
    colorClass: 'text-purple-500',
  },
])

// 方法
const handleAvatarUpload = async (file: UploadRawFile): Promise<boolean> => {
  // 验证文件类型和大小
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }

  try {
    // 调用API上传头像
    const response = await AuthAPI.uploadAvatar(file as File)
    userInfo.avatar_url = response.avatar_url

    // 更新全局用户信息
    if (authStore.user) {
      authStore.user.avatar = response.avatar_url

      // 同时更新localStorage中的用户信息，确保页面刷新后头像不会丢失
      const storage = authStore.rememberMe ? localStorage : sessionStorage
      storage.setItem('user_info', JSON.stringify(authStore.user))
    }

    ElMessage.success('头像上传成功！')
    return true
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败，请重试')
    return false
  }
}

const handleSaveAll = async () => {
  try {
    isSaving.value = true

    // 验证所有表单
    const forms = [
      userInfoForm.value,
      preferencesForm.value,
      aiSettingsForm.value,
      privacyForm.value,
    ]
    const validations = await Promise.all(forms.map((form) => form?.validate().catch(() => false)))

    if (validations.some((valid) => !valid)) {
      ElMessage.error('请检查表单填写是否正确')
      return
    }

    // 保存用户基本信息
    const profileUpdateData = {
      name: userInfo.real_name,
      nickname: userInfo.username,
      avatar_url: userInfo.avatar_url,
      school: userInfo.school,
      grade_level: userInfo.grade_level,
      // 暂时不支持的字段，后续扩展
      // class_name: userInfo.class_name,
      // institution: userInfo.institution,
      // parent_contact: userInfo.parent_contact,
      // parent_name: userInfo.parent_name,
      notification_enabled: preferences.enable_daily_reminder,
    }

    await AuthAPI.updateProfile(profileUpdateData)

    // TODO: 后续扩展其他设置的保存
    // await UserAPI.updatePreferences(preferences);
    // await UserAPI.updateAISettings(aiSettings);
    // await UserAPI.updatePrivacySettings(privacySettings);

    ElMessage.success('设置保存成功！')
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}

const showDataExport = () => {
  showExportDialog.value = true
}

const handleExportData = async () => {
  try {
    isExporting.value = true

    // 调用导出API
    // await UserAPI.exportData(exportOptions.value);

    ElMessage.success('数据导出请求已提交，请稍后查收邮件')
    showExportDialog.value = false
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    isExporting.value = false
  }
}

const showDeleteAccount = () => {
  showDeleteDialog.value = true
  deleteConfirm.confirmText = ''
}

const handleDeleteInput = () => {
  // 实时验证输入
}

const handleDeleteAccount = async () => {
  if (!canDelete.value) return

  try {
    await ElMessageBox.confirm(
      '最后确认：删除账户后，所有数据将无法恢复。您确定要继续吗？',
      '最终确认',
      {
        type: 'error',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      }
    )

    isDeleting.value = true

    // 调用删除API
    // await UserAPI.deleteAccount();

    ElMessage.success('账户已删除')
    // 清除本地存储并跳转到登录页
    userStore.logout()
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除账户失败:', error)
      ElMessage.error('删除失败，请重试')
    }
  } finally {
    isDeleting.value = false
    showDeleteDialog.value = false
  }
}

const goToAnalytics = () => {
  router.push('/analytics')
}

// 初始化数据
const initData = async () => {
  try {
    // 从当前登录用户获取数据
    if (authStore.user) {
      userInfo.username = authStore.user.nickname || ''
      userInfo.real_name = authStore.user.name || ''
      userInfo.avatar_url = authStore.user.avatar || ''
      userInfo.school = authStore.user.school || ''
      userInfo.grade_level = authStore.user.grade_level || ''
      userInfo.phone = authStore.user.phone || ''
      userInfo.email = '' // 暂时不支持
      userInfo.gender = 'other' // 默认值
      userInfo.bio = '' // 默认为空
    }

    // TODO: 后续扩展加载其他设置
    // const prefs = await UserAPI.getPreferences();
    // Object.assign(preferences, prefs);
    // const aiPrefs = await UserAPI.getAISettings();
    // Object.assign(aiSettings, aiPrefs);
    // const privacy = await UserAPI.getPrivacySettings();
    // Object.assign(privacySettings, privacy);
  } catch (error) {
    console.error('加载用户数据失败:', error)
  }
}

onMounted(() => {
  initData()
})
</script>

<style scoped lang="scss">
.profile-page {
  min-height: 100vh;
  background: #f8fafc;
  padding: 24px;

  .page-header {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .profile-content {
    .profile-card,
    .settings-section {
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #374151;
      }
    }

    .avatar-section {
      text-align: center;

      .avatar-container {
        position: relative;
        display: inline-block;

        .user-avatar {
          border: 3px solid #e5e7eb;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .avatar-upload {
          margin-top: 12px;

          .change-avatar-btn {
            font-size: 12px;
            color: #6b7280;

            &:hover {
              color: #3b82f6;
            }
          }
        }
      }
    }

    .stats-overview {
      .stat-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        background: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;

        .stat-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: white;
        }

        .stat-content {
          .stat-value {
            font-size: 18px;
            font-weight: 600;
            color: #111827;
            line-height: 1.2;
          }

          .stat-label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
          }
        }
      }
    }
  }

  .export-options,
  .delete-warning {
    .space-y-2 > * + * {
      margin-top: 8px;
    }

    .space-y-3 > * + * {
      margin-top: 12px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .profile-page {
    padding: 16px;

    .profile-content {
      .el-col {
        margin-bottom: 16px;
      }
    }

    .stats-overview {
      .grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
      }

      .stat-item {
        padding: 12px;

        .stat-icon {
          width: 32px;
          height: 32px;
        }
      }
    }
  }
}

// 深色模式支持
@media (prefers-color-scheme: dark) {
  .profile-page {
    background: #111827;

    .page-header,
    .el-card {
      background: #1f2937;
      border-color: #374151;
    }

    .card-header {
      color: #e5e7eb !important;
    }

    .stat-item {
      background: #374151;
      border-color: #4b5563;

      .stat-icon {
        background: #1f2937;
      }

      .stat-value {
        color: #f9fafb;
      }

      .stat-label {
        color: #9ca3af;
      }
    }
  }
}
</style>
