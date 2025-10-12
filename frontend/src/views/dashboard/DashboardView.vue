<template>
  <div class="dashboard-container">
    <!-- 学习统计横幅 -->
    <div class="stats-banner">
      <div class="stats-content">
        <div class="banner-text">
          <h2>学习概览</h2>
          <p>今天是学习的好日子，让我们一起进步吧</p>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <el-icon class="stat-icon"><Trophy /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.totalPoints }}</div>
              <div class="stat-label">学习积分</div>
            </div>
          </div>
          <div class="stat-item">
            <el-icon class="stat-icon"><Calendar /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ userStats.studyDays }}</div>
              <div class="stat-label">学习天数</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能卡片区域 -->
    <div class="feature-cards">
      <el-row :gutter="24">
        <!-- 作业问答 -->
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="feature-card learning-card" @click="navigateTo('/learning')">
            <div class="card-content">
              <el-icon class="card-icon"><ChatLineSquare /></el-icon>
              <h3>作业问答</h3>
              <p>AI智能答疑，解决学习难题</p>
            </div>
            <div class="card-stats">
              <span>今日提问: {{ todayStats.questions }}</span>
            </div>
          </el-card>
        </el-col>

        <!-- 错题手册 -->
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="feature-card homework-card" @click="navigateTo('/mistakes')">
            <div class="card-content">
              <el-icon class="card-icon"><Collection /></el-icon>
              <h3>错题手册</h3>
              <p>记录错题，智能复习</p>
            </div>
            <div class="card-stats">
              <span>待复习: {{ todayStats.pendingHomework }}</span>
            </div>
          </el-card>
        </el-col>

        <!-- 学习进度 -->
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="feature-card progress-card" @click="navigateTo('/progress')">
            <div class="card-content">
              <el-icon class="card-icon"><TrendCharts /></el-icon>
              <h3>学习进度</h3>
              <p>追踪学习轨迹，查看成长</p>
            </div>
            <div class="card-stats">
              <span>本周进度: {{ weekProgress }}%</span>
            </div>
          </el-card>
        </el-col>

        <!-- 个人中心 -->
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="feature-card profile-card" @click="navigateTo('/profile')">
            <div class="card-content">
              <el-icon class="card-icon"><User /></el-icon>
              <h3>个人中心</h3>
              <p>管理个人信息和设置</p>
            </div>
            <div class="card-stats">
              <span>等级: {{ userLevel }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 最近活动和今日目标 -->
    <el-row :gutter="24" class="bottom-section">
      <!-- 最近活动 -->
      <el-col :xs="24" :lg="16">
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <h3>最近活动</h3>
              <el-button
                type="primary"
                size="small"
                class="view-all-btn"
                @click="viewAllActivities"
              >
                查看全部
              </el-button>
            </div>
          </template>
          <div class="activity-list">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <div class="activity-icon">
                <el-icon>
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-info">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ formatTime(activity.time) }}</div>
              </div>
              <div class="activity-status">
                <el-tag :type="getStatusType(activity.status)">
                  {{ activity.status }}
                </el-tag>
              </div>
            </div>
          </div>
          <div v-if="recentActivities.length === 0" class="empty-state">
            <el-empty description="暂无最近活动" />
          </div>
        </el-card>
      </el-col>

      <!-- 今日目标 -->
      <el-col :xs="24" :lg="8">
        <el-card class="goals-card">
          <template #header>
            <h3>今日目标</h3>
          </template>
          <div class="goals-list">
            <div v-for="goal in todayGoals" :key="goal.id" class="goal-item">
              <el-checkbox v-model="goal.completed" @change="updateGoalStatus(goal)">
                {{ goal.title }}
              </el-checkbox>
              <div class="goal-progress">
                <el-progress :percentage="goal.progress" :show-text="false" size="small" />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Trophy,
  Calendar,
  ChatLineSquare,
  Collection,
  TrendCharts,
  User,
  QuestionFilled,
  DocumentChecked,
  DataAnalysis,
} from '@element-plus/icons-vue'
import { userAPI, type UserActivity, type UserStats } from '@/api/user'
import { goalAPI, type DailyGoal } from '@/api/goals'

const router = useRouter()

// 响应式数据
const userStats = ref<UserStats>({
  totalPoints: 1250,
  studyDays: 45,
  questions: 3,
  pendingHomework: 2,
})

const todayStats = ref({
  questions: 3,
  pendingHomework: 2,
})

const weekProgress = ref(75)
const userLevel = ref('中级')

const recentActivities = ref<UserActivity[]>([])

const todayGoals = ref<DailyGoal[]>([])

// 方法
const navigateTo = (path: string) => {
  router.push(path)
}

const getActivityIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    question: QuestionFilled,
    homework: DocumentChecked,
    study: DataAnalysis,
  }
  return iconMap[type] || QuestionFilled
}

const getStatusType = (status: string): 'success' | 'warning' | 'danger' | 'info' => {
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    已解答: 'success',
    已批改: 'success',
    已完成: 'success',
    进行中: 'info',
    待处理: 'warning',
  }
  return statusMap[status] || 'info'
}

const formatTime = (time: string | Date) => {
  const now = new Date()
  const timeObj = typeof time === 'string' ? new Date(time) : time
  const diff = now.getTime() - timeObj.getTime()

  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return `${days}天前`
  }
}

const viewAllActivities = () => {
  router.push('/activities')
}

const updateGoalStatus = (goal: DailyGoal) => {
  if (goal.completed) {
    ElMessage.success(`🎉 恭喜完成目标：${goal.title}`)
  }
  // 后续可以在这里调用 API 更新目标进度到后端
}

// 数据获取函数
const fetchUserStats = async () => {
  try {
    const stats = await userAPI.getStats()
    userStats.value = stats
    todayStats.value = {
      questions: stats.questions,
      pendingHomework: stats.pendingHomework,
    }
  } catch (error) {
    console.error('获取用户统计失败:', error)
    ElMessage.error('获取用户统计失败')
  }
}

const fetchRecentActivities = async () => {
  try {
    const activities = await userAPI.getActivities(10)
    recentActivities.value = activities
  } catch (error) {
    console.error('获取最近活动失败:', error)
    ElMessage.error('获取最近活动失败')
  }
}

const fetchDailyGoals = async () => {
  try {
    const goals = await goalAPI.getDailyGoals()
    todayGoals.value = goals
  } catch (error) {
    console.error('获取每日目标失败:', error)
    ElMessage.error('获取每日目标失败')
  }
}

// 组件挂载时获取数据
onMounted(async () => {
  await Promise.all([fetchUserStats(), fetchRecentActivities(), fetchDailyGoals()])
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
  min-height: calc(100vh - 64px);
  background-color: var(--el-bg-color-page);
}

.stats-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  color: white;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    pointer-events: none;
  }

  .stats-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    z-index: 1;

    .banner-text {
      h2 {
        font-size: 28px;
        font-weight: 600;
        margin: 0 0 8px 0;
      }

      p {
        font-size: 16px;
        opacity: 0.9;
        margin: 0;
      }
    }

    .stats-grid {
      display: flex;
      gap: 32px;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 12px;

        .stat-icon {
          font-size: 32px;
          opacity: 0.8;
        }

        .stat-info {
          .stat-number {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 14px;
            opacity: 0.8;
          }
        }
      }
    }
  }
}

.feature-cards {
  margin-bottom: 24px;

  .feature-card {
    cursor: pointer;
    transition: all 0.3s ease;
    height: 160px;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    :deep(.el-card__body) {
      padding: 24px;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .card-content {
      text-align: center;

      .card-icon {
        font-size: 36px;
        margin-bottom: 12px;
        color: var(--el-color-primary);
      }

      h3 {
        font-size: 18px;

        font-weight: 600;
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }

      p {
        font-size: 14px;
        color: var(--el-text-color-regular);
        margin: 0;
      }
    }

    .card-stats {
      text-align: center;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      padding-top: 12px;
      border-top: 1px solid var(--el-border-color-light);
    }
  }

  .learning-card .card-icon {
    color: #409eff;
  }
  .homework-card .card-icon {
    color: #67c23a;
  }
  .progress-card .card-icon {
    color: #e6a23c;
  }
  .profile-card .card-icon {
    color: #909399;
  }
}

.bottom-section {
  margin-top: 24px;
}

.activity-card,
.quick-actions-card,
.goals-card {
  :deep(.el-card__header) {
    padding: 20px 24px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-card__body) {
    padding: 20px 24px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .el-button--text.el-button--primary {
      color: var(--el-color-primary) !important;
      background-color: var(--el-color-primary-light-9);
      border: 1px solid var(--el-color-primary-light-5);
      border-radius: 4px;
      padding: 6px 12px;
      font-weight: 500;
      font-size: 14px;
      min-height: 32px;
      display: inline-flex;
      align-items: center;
      justify-content: center;

      &:hover {
        color: white !important;
        background-color: var(--el-color-primary);
        border-color: var(--el-color-primary);
      }

      &:active {
        color: white !important;
        background-color: var(--el-color-primary-dark-2);
        border-color: var(--el-color-primary-dark-2);
      }

      &:focus {
        color: var(--el-color-primary) !important;
        background-color: var(--el-color-primary-light-9);
        border-color: var(--el-color-primary);
      }
    }

    .view-all-btn {
      font-size: 14px !important;
      height: 32px !important;
      padding: 8px 16px !important;
      border-radius: 4px !important;
      background-color: var(--el-color-primary) !important;
      border-color: var(--el-color-primary) !important;
      color: white !important;

      &:hover {
        background-color: var(--el-color-primary-light-3) !important;
        border-color: var(--el-color-primary-light-3) !important;
      }

      &:active {
        background-color: var(--el-color-primary-dark-2) !important;
        border-color: var(--el-color-primary-dark-2) !important;
      }
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    .activity-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: var(--el-color-primary-light-9);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;

      .el-icon {
        font-size: 18px;
        color: var(--el-color-primary);
      }
    }

    .activity-info {
      flex: 1;

      .activity-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .activity-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }

    .activity-status {
      margin-left: 16px;
    }
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;

  .action-button {
    height: 48px;
    border-radius: 8px;
    font-weight: 500;
  }
}

.goals-list {
  .goal-item {
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    .goal-progress {
      margin-top: 8px;
    }
  }
}

.empty-state {
  padding: 40px 0;
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }

  .stats-banner {
    padding: 20px;

    .stats-content {
      flex-direction: column;
      text-align: center;
      gap: 20px;

      .stats-grid {
        gap: 20px;
      }
    }
  }

  .feature-cards .feature-card {
    margin-bottom: 16px;
  }

  .bottom-section {
    .el-col {
      margin-bottom: 16px;
    }
  }
}

@media (max-width: 480px) {
  .stats-grid {
    flex-direction: column;
    gap: 16px !important;
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
