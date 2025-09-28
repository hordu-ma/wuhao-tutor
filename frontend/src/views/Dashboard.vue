<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="dashboard-header mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">仪表板</h1>
          <p class="text-gray-600">欢迎回来，查看您的学习概览</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="refreshData" :loading="loading">
            <el-icon class="mr-2">
              <Refresh />
            </el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid mb-8">
      <div
        v-for="stat in statsData"
        :key="stat.key"
        class="stat-card"
        :class="stat.colorClass"
      >
        <div class="stat-icon">
          <el-icon :size="32">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-change" :class="stat.changeClass">
            <el-icon :size="12">
              <component :is="stat.changeIcon" />
            </el-icon>
            <span>{{ stat.change }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="dashboard-content grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左侧内容 -->
      <div class="lg:col-span-2 space-y-6">
        <!-- 学习进度卡片 -->
        <el-card class="progress-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">学习进度</h3>
              <el-select
                v-model="progressTimeRange"
                size="small"
                @change="updateProgressData"
              >
                <el-option label="本周" value="week" />
                <el-option label="本月" value="month" />
                <el-option label="本学期" value="semester" />
              </el-select>
            </div>
          </template>

          <div class="progress-content">
            <div
              class="progress-item"
              v-for="subject in subjectProgress"
              :key="subject.name"
            >
              <div class="progress-info">
                <span class="subject-name">{{ subject.name }}</span>
                <span class="progress-percentage"
                  >{{ subject.percentage }}%</span
                >
              </div>
              <el-progress
                :percentage="subject.percentage"
                :status="subject.status"
                :stroke-width="8"
                class="progress-bar"
              />
              <div class="progress-details">
                <span class="completed">已完成: {{ subject.completed }}</span>
                <span class="total">总计: {{ subject.total }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 最近作业卡片 -->
        <el-card class="homework-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">最近作业</h3>
              <router-link to="/homework">
                <el-button type="text" size="small">查看全部</el-button>
              </router-link>
            </div>
          </template>

          <div class="homework-list">
            <div
              v-for="homework in recentHomework"
              :key="homework.id"
              class="homework-item"
            >
              <div class="homework-info">
                <h4 class="homework-title">{{ homework.title }}</h4>
                <p class="homework-subject">{{ homework.subject }}</p>
              </div>
              <div class="homework-meta">
                <el-tag :type="homework.statusType" size="small">
                  {{ homework.status }}
                </el-tag>
                <span class="homework-date">{{
                  formatDate(homework.date)
                }}</span>
              </div>
              <div class="homework-score" v-if="homework.score">
                <span class="score-value">{{ homework.score }}</span>
                <span class="score-total">/100</span>
              </div>
            </div>

            <div v-if="recentHomework.length === 0" class="empty-state">
              <el-empty description="暂无作业记录" :image-size="120" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧边栏 -->
      <div class="space-y-6">
        <!-- 快捷操作 -->
        <el-card class="quick-actions-card">
          <template #header>
            <h3 class="card-title">快捷操作</h3>
          </template>

          <div class="quick-actions">
            <router-link
              v-for="action in quickActions"
              :key="action.key"
              :to="action.path"
              class="quick-action-item"
            >
              <div class="action-icon" :class="action.colorClass">
                <el-icon :size="24">
                  <component :is="action.icon" />
                </el-icon>
              </div>
              <div class="action-content">
                <div class="action-title">{{ action.title }}</div>
                <div class="action-desc">{{ action.description }}</div>
              </div>
              <el-icon class="action-arrow">
                <ArrowRight />
              </el-icon>
            </router-link>
          </div>
        </el-card>

        <!-- 学习建议 -->
        <el-card class="suggestions-card">
          <template #header>
            <h3 class="card-title">学习建议</h3>
          </template>

          <div class="suggestions-list">
            <div
              v-for="suggestion in learningSuggestions"
              :key="suggestion.id"
              class="suggestion-item"
            >
              <div class="suggestion-icon">
                <el-icon :size="16" :color="suggestion.iconColor">
                  <component :is="suggestion.icon" />
                </el-icon>
              </div>
              <div class="suggestion-content">
                <div class="suggestion-title">{{ suggestion.title }}</div>
                <div class="suggestion-desc">{{ suggestion.description }}</div>
              </div>
            </div>

            <div
              v-if="learningSuggestions.length === 0"
              class="empty-suggestions"
            >
              <p class="text-gray-500 text-sm">暂无学习建议</p>
            </div>
          </div>
        </el-card>

        <!-- 日历 -->
        <el-card class="calendar-card">
          <template #header>
            <h3 class="card-title">学习日历</h3>
          </template>

          <el-calendar v-model="calendarValue" class="dashboard-calendar">
            <template #date-cell="{ data }">
              <div class="calendar-day">
                <span class="day-number">{{
                  data.day.split("-").slice(-1)[0]
                }}</span>
                <div class="day-indicators">
                  <span
                    v-if="hasHomework(data.day)"
                    class="indicator homework-indicator"
                  />
                  <span
                    v-if="hasExam(data.day)"
                    class="indicator exam-indicator"
                  />
                </div>
              </div>
            </template>
          </el-calendar>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

// 响应式数据
const loading = ref(false);
const progressTimeRange = ref("month");
const calendarValue = ref(new Date());

// 统计数据
const statsData = ref([
  {
    key: "homework",
    label: "已完成作业",
    value: "24",
    change: "+12.5%",
    changeIcon: "ArrowUp",
    changeClass: "text-green-600",
    icon: "Document",
    colorClass: "stat-card--blue",
  },
  {
    key: "questions",
    label: "问答次数",
    value: "156",
    change: "+8.3%",
    changeIcon: "ArrowUp",
    changeClass: "text-green-600",
    icon: "ChatSquare",
    colorClass: "stat-card--green",
  },
  {
    key: "score",
    label: "平均分数",
    value: "87.5",
    change: "+2.1%",
    changeIcon: "ArrowUp",
    changeClass: "text-green-600",
    icon: "TrendCharts",
    colorClass: "stat-card--purple",
  },
  {
    key: "time",
    label: "学习时长(小时)",
    value: "48.5",
    change: "-5.2%",
    changeIcon: "ArrowDown",
    changeClass: "text-red-600",
    icon: "Clock",
    colorClass: "stat-card--orange",
  },
]);

// 学科进度数据
const subjectProgress = ref([
  {
    name: "数学",
    percentage: 85,
    status: undefined,
    completed: 17,
    total: 20,
  },
  {
    name: "语文",
    percentage: 92,
    status: "success" as const,
    completed: 23,
    total: 25,
  },
  {
    name: "英语",
    percentage: 78,
    status: undefined,
    completed: 15,
    total: 19,
  },
  {
    name: "物理",
    percentage: 65,
    status: "warning" as const,
    completed: 13,
    total: 20,
  },
]);

// 最近作业数据
const recentHomework = ref([
  {
    id: 1,
    title: "微积分练习题",
    subject: "数学",
    status: "已批改",
    statusType: "success" as const,
    score: 92,
    date: new Date(2025, 0, 25),
  },
  {
    id: 2,
    title: "古诗词背诵",
    subject: "语文",
    status: "待批改",
    statusType: "warning" as const,
    score: null,
    date: new Date(2025, 0, 24),
  },
  {
    id: 3,
    title: "英语作文",
    subject: "英语",
    status: "已批改",
    statusType: "success" as const,
    score: 88,
    date: new Date(2025, 0, 23),
  },
]);

// 快捷操作
const quickActions = ref([
  {
    key: "upload",
    title: "上传作业",
    description: "提交新的作业图片",
    path: "/homework",
    icon: "Upload",
    colorClass: "action-icon--blue",
  },
  {
    key: "chat",
    title: "学习问答",
    description: "智能AI学习助手",
    path: "/learning",
    icon: "ChatSquare",
    colorClass: "action-icon--green",
  },
  {
    key: "analytics",
    title: "学情分析",
    description: "查看学习报告",
    path: "/analytics",
    icon: "DataAnalysis",
    colorClass: "action-icon--purple",
  },
]);

// 学习建议
const learningSuggestions = ref([
  {
    id: 1,
    title: "加强数学练习",
    description: "建议多做微积分相关题目",
    icon: "Warning",
    iconColor: "#f59e0b",
  },
  {
    id: 2,
    title: "保持语文优势",
    description: "继续保持良好的学习状态",
    icon: "Check",
    iconColor: "#10b981",
  },
  {
    id: 3,
    title: "英语口语练习",
    description: "可以多进行口语对话练习",
    icon: "Clock",
    iconColor: "#3b82f6",
  },
]);

// 方法
const refreshData = async () => {
  loading.value = true;
  try {
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1000));
    // 这里可以调用实际的API获取数据
  } finally {
    loading.value = false;
  }
};

const updateProgressData = () => {
  // 根据时间范围更新进度数据
  console.log("更新进度数据:", progressTimeRange.value);
};

const formatDate = (date: Date) => {
  return date.toLocaleDateString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
  });
};

const hasHomework = (dateStr: string) => {
  // 简单的模拟逻辑
  const date = new Date(dateStr);
  return date.getDate() % 3 === 0;
};

const hasExam = (dateStr: string) => {
  // 简单的模拟逻辑
  const date = new Date(dateStr);
  return date.getDate() % 7 === 0;
};

// 生命周期
onMounted(() => {
  refreshData();
});
</script>

<style scoped lang="scss">
.dashboard {
  padding: 24px;
  background-color: #f8fafc;
  min-height: 100vh;

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.dashboard-header {
  .header-actions {
    @media (max-width: 768px) {
      margin-top: 16px;
    }
  }
}

// 统计卡片
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  @media (max-width: 768px) {
    padding: 16px;
    gap: 12px;
  }

  &--blue {
    border-left: 4px solid #3b82f6;

    .stat-icon {
      color: #3b82f6;
      background-color: #eff6ff;
    }
  }

  &--green {
    border-left: 4px solid #10b981;

    .stat-icon {
      color: #10b981;
      background-color: #ecfdf5;
    }
  }

  &--purple {
    border-left: 4px solid #8b5cf6;

    .stat-icon {
      color: #8b5cf6;
      background-color: #f3e8ff;
    }
  }

  &--orange {
    border-left: 4px solid #f59e0b;

    .stat-icon {
      color: #f59e0b;
      background-color: #fffbeb;
    }
  }
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  @media (max-width: 768px) {
    width: 40px;
    height: 40px;
  }
}

.stat-content {
  flex: 1;

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
    line-height: 1;
    margin-bottom: 4px;

    @media (max-width: 768px) {
      font-size: 20px;
    }
  }

  .stat-label {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 8px;

    @media (max-width: 768px) {
      font-size: 12px;
    }
  }

  .stat-change {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 500;

    @media (max-width: 768px) {
      font-size: 11px;
    }
  }
}

// 卡片样式
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }
}

// 进度卡片
.progress-content {
  .progress-item {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }

    .progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .subject-name {
        font-weight: 500;
        color: #374151;
      }

      .progress-percentage {
        font-weight: 600;
        color: #111827;
      }
    }

    .progress-bar {
      margin-bottom: 8px;
    }

    .progress-details {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #6b7280;
    }
  }
}

// 作业列表
.homework-list {
  .homework-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    @media (max-width: 768px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .homework-info {
      flex: 1;

      .homework-title {
        font-size: 16px;
        font-weight: 500;
        color: #111827;
        margin: 0 0 4px 0;

        @media (max-width: 768px) {
          font-size: 14px;
        }
      }

      .homework-subject {
        font-size: 14px;
        color: #6b7280;
        margin: 0;

        @media (max-width: 768px) {
          font-size: 12px;
        }
      }
    }

    .homework-meta {
      display: flex;
      align-items: center;
      gap: 12px;

      @media (max-width: 768px) {
        width: 100%;
        justify-content: space-between;
      }

      .homework-date {
        font-size: 12px;
        color: #9ca3af;
      }
    }

    .homework-score {
      text-align: right;
      min-width: 60px;

      .score-value {
        font-size: 18px;
        font-weight: 600;
        color: #10b981;
      }

      .score-total {
        font-size: 14px;
        color: #6b7280;
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: 32px 0;
  }
}

// 快捷操作
.quick-actions {
  .quick-action-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border-radius: 8px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s ease;
    margin-bottom: 8px;

    &:hover {
      background-color: #f9fafb;
      transform: translateX(4px);
    }

    &:last-child {
      margin-bottom: 0;
    }

    .action-icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      &--blue {
        background-color: #eff6ff;
        color: #3b82f6;
      }

      &--green {
        background-color: #ecfdf5;
        color: #10b981;
      }

      &--purple {
        background-color: #f3e8ff;
        color: #8b5cf6;
      }
    }

    .action-content {
      flex: 1;

      .action-title {
        font-weight: 500;
        color: #111827;
        margin-bottom: 2px;
      }

      .action-desc {
        font-size: 12px;
        color: #6b7280;
      }
    }

    .action-arrow {
      color: #d1d5db;
      transition: color 0.2s ease;
    }

    &:hover .action-arrow {
      color: #9ca3af;
    }
  }
}

// 学习建议
.suggestions-list {
  .suggestion-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f9fafb;

    &:last-child {
      border-bottom: none;
    }

    .suggestion-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .suggestion-content {
      flex: 1;

      .suggestion-title {
        font-size: 14px;
        font-weight: 500;
        color: #111827;
        margin-bottom: 4px;
      }

      .suggestion-desc {
        font-size: 12px;
        color: #6b7280;
        line-height: 1.4;
      }
    }
  }

  .empty-suggestions {
    text-align: center;
    padding: 24px 0;
  }
}

// 日历
.dashboard-calendar {
  :deep(.el-calendar-table) {
    .el-calendar-day {
      padding: 0;
    }
  }
}

.calendar-day {
  width: 100%;
  height: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;

  .day-number {
    font-size: 14px;
    line-height: 1;
  }

  .day-indicators {
    display: flex;
    gap: 2px;
    margin-top: 2px;

    .indicator {
      width: 4px;
      height: 4px;
      border-radius: 50%;

      &.homework-indicator {
        background-color: #3b82f6;
      }

      &.exam-indicator {
        background-color: #f59e0b;
      }
    }
  }
}
</style>
