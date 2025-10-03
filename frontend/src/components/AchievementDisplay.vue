<template>
  <div class="achievement-display">
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <!-- 头部信息 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <el-icon class="text-yellow-500 mr-2">
              <Trophy />
            </el-icon>
            学习成就
          </h3>
          <p class="text-sm text-gray-600 mt-1">
            已解锁 {{ unlockedCount }}/{{ totalAchievements }} 个成就
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <el-select
            v-model="selectedCategory"
            size="small"
            @change="handleCategoryChange"
          >
            <el-option label="全部类型" value="" />
            <el-option label="学习成就" value="study" />
            <el-option label="作业成就" value="homework" />
            <el-option label="连续成就" value="streak" />
            <el-option label="进步成就" value="improvement" />
            <el-option label="特殊成就" value="special" />
          </el-select>
          <el-button
            size="small"
            type="primary"
            :icon="Refresh"
            @click="refreshAchievements"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 进度统计 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div
          class="text-center p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg border border-yellow-200"
        >
          <div class="text-2xl font-bold text-yellow-600 mb-1">
            {{ progressStats.unlocked }}
          </div>
          <div class="text-xs text-yellow-700">已解锁</div>
        </div>
        <div
          class="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200"
        >
          <div class="text-2xl font-bold text-blue-600 mb-1">
            {{ progressStats.inProgress }}
          </div>
          <div class="text-xs text-blue-700">进行中</div>
        </div>
        <div
          class="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200"
        >
          <div class="text-2xl font-bold text-green-600 mb-1">
            {{ progressStats.completionRate }}%
          </div>
          <div class="text-xs text-green-700">完成率</div>
        </div>
        <div
          class="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200"
        >
          <div class="text-2xl font-bold text-purple-600 mb-1">
            {{ progressStats.points }}
          </div>
          <div class="text-xs text-purple-700">成就积分</div>
        </div>
      </div>

      <!-- 最近解锁的成就 -->
      <div v-if="recentUnlocked.length > 0" class="mb-6">
        <h4 class="text-md font-semibold text-gray-900 mb-3 flex items-center">
          <el-icon class="text-green-500 mr-2">
            <Star />
          </el-icon>
          最近解锁
        </h4>
        <div class="flex space-x-3 overflow-x-auto pb-2">
          <div
            v-for="achievement in recentUnlocked"
            :key="achievement.id"
            class="flex-shrink-0 w-32 p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200 text-center"
          >
            <div class="achievement-icon mb-2">
              <el-icon :size="32" class="text-green-500">
                <Trophy />
              </el-icon>
            </div>
            <div class="text-xs font-medium text-gray-900 mb-1">
              {{ achievement.name }}
            </div>
            <div class="text-xs text-gray-500">
              {{ formatTime(achievement.unlockedAt) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 成就网格展示 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-md font-semibold text-gray-900">成就列表</h4>
          <div class="flex items-center space-x-2">
            <el-button-group size="small">
              <el-button
                :type="viewMode === 'grid' ? 'primary' : 'default'"
                @click="viewMode = 'grid'"
              >
                <el-icon><Grid /></el-icon>
              </el-button>
              <el-button
                :type="viewMode === 'list' ? 'primary' : 'default'"
                @click="viewMode = 'list'"
              >
                <el-icon><List /></el-icon>
              </el-button>
            </el-button-group>
            <el-switch
              v-model="showOnlyUnlocked"
              active-text="仅显示已解锁"
              inactive-text="显示全部"
              size="small"
            />
          </div>
        </div>

        <!-- 网格视图 -->
        <div
          v-if="viewMode === 'grid'"
          class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4"
        >
          <div
            v-for="achievement in filteredAchievements"
            :key="achievement.id"
            class="achievement-item relative p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer"
            :class="getAchievementCardClass(achievement)"
            @click="showAchievementDetail(achievement)"
          >
            <!-- 稀有度边框效果 -->
            <div
              v-if="achievement.unlocked"
              class="absolute inset-0 rounded-lg"
              :class="getRarityBorderClass(achievement.rarity)"
            ></div>

            <div class="relative z-10">
              <!-- 成就图标 -->
              <div class="achievement-icon mb-3 text-center">
                <el-icon
                  :size="40"
                  :class="
                    achievement.unlocked
                      ? getAchievementIconClass(achievement)
                      : 'text-gray-400'
                  "
                >
                  <Trophy v-if="achievement.unlocked" />
                  <Lock v-else />
                </el-icon>
              </div>

              <!-- 成就名称 -->
              <div class="text-center">
                <div
                  class="text-sm font-medium mb-1"
                  :class="
                    achievement.unlocked ? 'text-gray-900' : 'text-gray-500'
                  "
                >
                  {{ achievement.name }}
                </div>

                <!-- 进度条 -->
                <div class="progress-container">
                  <el-progress
                    :percentage="Math.min(achievement.progress * 100, 100)"
                    :stroke-width="4"
                    :show-text="false"
                    :color="
                      achievement.unlocked
                        ? getProgressColor(achievement.rarity)
                        : '#d1d5db'
                    "
                  />
                  <div class="text-xs text-gray-500 mt-1">
                    {{ Math.round(achievement.progress * 100) }}%
                  </div>
                </div>
              </div>
            </div>

            <!-- 稀有度标识 -->
            <div
              v-if="achievement.unlocked"
              class="absolute top-1 right-1 z-20"
            >
              <el-tag
                :type="getRarityTagType(achievement.rarity) as any"
                size="small"
                class="text-xs"
              >
                {{ getRarityText(achievement.rarity) }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-else class="space-y-3">
          <div
            v-for="achievement in filteredAchievements"
            :key="achievement.id"
            class="achievement-list-item p-4 border rounded-lg hover:shadow-md transition-all duration-200 cursor-pointer"
            :class="
              achievement.unlocked
                ? 'bg-white border-gray-200'
                : 'bg-gray-50 border-gray-300'
            "
            @click="showAchievementDetail(achievement)"
          >
            <div class="flex items-center space-x-4">
              <!-- 图标 -->
              <div class="flex-shrink-0">
                <el-icon
                  :size="32"
                  :class="
                    achievement.unlocked
                      ? getAchievementIconClass(achievement)
                      : 'text-gray-400'
                  "
                >
                  <Trophy v-if="achievement.unlocked" />
                  <Lock v-else />
                </el-icon>
              </div>

              <!-- 信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-2">
                  <h5
                    class="text-md font-medium"
                    :class="
                      achievement.unlocked ? 'text-gray-900' : 'text-gray-500'
                    "
                  >
                    {{ achievement.name }}
                  </h5>
                  <div class="flex items-center space-x-2">
                    <el-tag
                      :type="getTypeTagType(achievement.type) as any"
                      size="small"
                    >
                      {{ getTypeText(achievement.type) }}
                    </el-tag>
                    <el-tag
                      v-if="achievement.unlocked"
                      :type="getRarityTagType(achievement.rarity) as any"
                      size="small"
                    >
                      {{ getRarityText(achievement.rarity) }}
                    </el-tag>
                  </div>
                </div>

                <p
                  class="text-sm mb-3"
                  :class="
                    achievement.unlocked ? 'text-gray-600' : 'text-gray-500'
                  "
                >
                  {{ achievement.description }}
                </p>

                <!-- 进度 -->
                <div class="flex items-center space-x-4">
                  <div class="flex-1">
                    <el-progress
                      :percentage="Math.min(achievement.progress * 100, 100)"
                      :stroke-width="6"
                      :color="
                        achievement.unlocked
                          ? getProgressColor(achievement.rarity)
                          : '#d1d5db'
                      "
                    />
                  </div>
                  <div class="text-sm text-gray-600 min-w-0">
                    {{ Math.round(achievement.progress * 100) }}%
                  </div>
                  <div
                    v-if="achievement.unlockedAt"
                    class="text-xs text-gray-500 min-w-0"
                  >
                    {{ formatTime(achievement.unlockedAt) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页或加载更多 -->
      <div v-if="hasMore" class="text-center">
        <el-button type="text" @click="loadMore" :loading="loadingMore">
          加载更多成就
        </el-button>
      </div>
    </div>

    <!-- 成就详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedAchievement?.name"
      width="500px"
      @close="selectedAchievement = null"
    >
      <div v-if="selectedAchievement" class="achievement-detail">
        <!-- 成就图标和基本信息 -->
        <div class="text-center mb-6">
          <div class="achievement-icon-large mb-4">
            <el-icon
              :size="80"
              :class="
                selectedAchievement.unlocked
                  ? getAchievementIconClass(selectedAchievement)
                  : 'text-gray-400'
              "
            >
              <Trophy v-if="selectedAchievement.unlocked" />
              <Lock v-else />
            </el-icon>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">
            {{ selectedAchievement.name }}
          </h3>
          <p class="text-gray-600 mb-4">
            {{ selectedAchievement.description }}
          </p>

          <!-- 标签 -->
          <div class="flex justify-center space-x-2 mb-4">
            <el-tag :type="getTypeTagType(selectedAchievement.type) as any">
              {{ getTypeText(selectedAchievement.type) }}
            </el-tag>
            <el-tag
              v-if="selectedAchievement.unlocked"
              :type="getRarityTagType(selectedAchievement.rarity) as any"
            >
              {{ getRarityText(selectedAchievement.rarity) }}
            </el-tag>
          </div>
        </div>

        <!-- 进度信息 -->
        <div class="progress-section mb-6">
          <h4 class="text-md font-semibold text-gray-900 mb-3">完成进度</h4>
          <div class="space-y-3">
            <el-progress
              :percentage="Math.min(selectedAchievement.progress * 100, 100)"
              :stroke-width="8"
              :color="
                selectedAchievement.unlocked
                  ? getProgressColor(selectedAchievement.rarity)
                  : '#d1d5db'
              "
            />
            <div class="flex justify-between text-sm text-gray-600">
              <span
                >当前进度:
                {{ Math.round(selectedAchievement.progress * 100) }}%</span
              >
              <span
                >目标: {{ selectedAchievement.condition.value }}
                {{ getConditionUnit(selectedAchievement.condition.type) }}</span
              >
            </div>
          </div>
        </div>

        <!-- 解锁信息 -->
        <div v-if="selectedAchievement.unlocked" class="unlock-info">
          <h4 class="text-md font-semibold text-gray-900 mb-3">解锁信息</h4>
          <div class="bg-green-50 rounded-lg p-4 border border-green-200">
            <div class="flex items-center space-x-2 text-green-600 mb-2">
              <el-icon><Check /></el-icon>
              <span class="font-medium">成就已解锁</span>
            </div>
            <div class="text-sm text-green-700">
              解锁时间: {{ formatDateTime(selectedAchievement.unlockedAt) }}
            </div>
          </div>
        </div>
        <div v-else class="condition-info">
          <h4 class="text-md font-semibold text-gray-900 mb-3">解锁条件</h4>
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div class="text-sm text-gray-700">
              {{ getConditionDescription(selectedAchievement.condition) }}
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button
            v-if="selectedAchievement?.unlocked"
            type="primary"
            @click="shareAchievement"
          >
            分享成就
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useAnalyticsStore } from "../stores/analytics";
import {
  Trophy,
  Lock,
  Star,
  Refresh,
  Grid,
  List,
  Check,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { Achievement } from "../types/analytics";
import dayjs from "dayjs";

interface Props {
  maxDisplay?: number;
  showCategories?: boolean;
  autoRefresh?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  maxDisplay: 12,
  showCategories: true,
  autoRefresh: false,
});

const analyticsStore = useAnalyticsStore();

// 状态
const loading = ref(false);
const loadingMore = ref(false);
const selectedCategory = ref("");
const viewMode = ref<"grid" | "list">("grid");
const showOnlyUnlocked = ref(false);
const showDetailDialog = ref(false);
const selectedAchievement = ref<Achievement | null>(null);
const displayCount = ref(props.maxDisplay);

// 计算属性
const achievements = computed(() => analyticsStore.achievements);
const unlockedCount = computed(
  () => analyticsStore.unlockedAchievements.length,
);
const totalAchievements = computed(() => achievements.value.length);

const progressStats = computed(() => {
  const total = achievements.value.length;
  const unlocked = unlockedCount.value;
  const inProgress = achievements.value.filter(
    (a) => !a.unlocked && a.progress > 0,
  ).length;
  const completionRate = total > 0 ? Math.round((unlocked / total) * 100) : 0;
  const points = achievements.value
    .filter((a) => a.unlocked)
    .reduce((sum, a) => {
      const rarityPoints = {
        common: 10,
        rare: 25,
        epic: 50,
        legendary: 100,
      };
      return sum + (rarityPoints[a.rarity] || 10);
    }, 0);

  return { unlocked, inProgress, completionRate, points };
});

const recentUnlocked = computed(() => {
  return achievements.value
    .filter((a) => a.unlocked && a.unlockedAt)
    .sort(
      (a, b) => dayjs(b.unlockedAt).valueOf() - dayjs(a.unlockedAt).valueOf(),
    )
    .slice(0, 5);
});

const filteredAchievements = computed(() => {
  let filtered = achievements.value;

  // 按类型过滤
  if (selectedCategory.value) {
    filtered = filtered.filter((a) => a.type === selectedCategory.value);
  }

  // 按解锁状态过滤
  if (showOnlyUnlocked.value) {
    filtered = filtered.filter((a) => a.unlocked);
  }

  // 按稀有度和解锁状态排序
  filtered.sort((a, b) => {
    // 已解锁的排在前面
    if (a.unlocked !== b.unlocked) {
      return a.unlocked ? -1 : 1;
    }

    // 相同解锁状态下，按稀有度排序
    const rarityOrder = { legendary: 4, epic: 3, rare: 2, common: 1 };
    return rarityOrder[b.rarity] - rarityOrder[a.rarity];
  });

  return filtered.slice(0, displayCount.value);
});

const hasMore = computed(() => {
  return displayCount.value < achievements.value.length;
});

// 样式相关方法
const getAchievementCardClass = (achievement: Achievement) => {
  if (achievement.unlocked) {
    return `bg-white border-${getRarityColor(achievement.rarity)}-200 hover:shadow-lg hover:border-${getRarityColor(achievement.rarity)}-300`;
  }
  return "bg-gray-50 border-gray-300 hover:bg-gray-100";
};

const getAchievementIconClass = (achievement: Achievement) => {
  const colorMap = {
    common: "text-gray-600",
    rare: "text-blue-500",
    epic: "text-purple-500",
    legendary: "text-yellow-500",
  };
  return colorMap[achievement.rarity] || "text-gray-600";
};

const getRarityBorderClass = (rarity: string) => {
  const borderMap = {
    common: "border-2 border-gray-300",
    rare: "border-2 border-blue-400 shadow-blue-200 shadow-lg",
    epic: "border-2 border-purple-400 shadow-purple-200 shadow-lg",
    legendary:
      "border-2 border-yellow-400 shadow-yellow-200 shadow-lg animate-pulse",
  };
  return borderMap[rarity as keyof typeof borderMap] || borderMap.common;
};

const getRarityColor = (rarity: string) => {
  const colorMap = {
    common: "gray",
    rare: "blue",
    epic: "purple",
    legendary: "yellow",
  };
  return colorMap[rarity as keyof typeof colorMap] || "gray";
};

const getRarityTagType = (rarity: string) => {
  const typeMap = {
    common: "info",
    rare: "primary",
    epic: "warning",
    legendary: "danger",
  };
  return typeMap[rarity as keyof typeof typeMap] || "info";
};

const getRarityText = (rarity: string) => {
  const textMap = {
    common: "普通",
    rare: "稀有",
    epic: "史诗",
    legendary: "传奇",
  };
  return textMap[rarity as keyof typeof textMap] || "普通";
};

const getTypeTagType = (type: string) => {
  const typeMap = {
    study: "success",
    homework: "primary",
    streak: "warning",
    improvement: "info",
    special: "danger",
  };
  return typeMap[type as keyof typeof typeMap] || "info";
};

const getTypeText = (type: string) => {
  const textMap = {
    study: "学习",
    homework: "作业",
    streak: "连续",
    improvement: "进步",
    special: "特殊",
  };
  return textMap[type as keyof typeof textMap] || "其他";
};

const getProgressColor = (rarity: string) => {
  const colorMap = {
    common: "#6b7280",
    rare: "#3b82f6",
    epic: "#8b5cf6",
    legendary: "#f59e0b",
  };
  return colorMap[rarity as keyof typeof colorMap] || "#6b7280";
};

const getConditionUnit = (type: string) => {
  const unitMap = {
    study_time: "分钟",
    homework_count: "份",
    streak_days: "天",
    avg_score: "分",
    questions: "个",
  };
  return unitMap[type as keyof typeof unitMap] || "";
};

const getConditionDescription = (condition: any) => {
  const { type, value } = condition;
  const descriptions = {
    study_time: `累计学习时长达到 ${value} 分钟`,
    homework_count: `完成 ${value} 份作业`,
    streak_days: `连续学习 ${value} 天`,
    avg_score: `平均分达到 ${value} 分`,
    questions: `提问 ${value} 个问题`,
  };
  return (
    descriptions[type as keyof typeof descriptions] || `完成条件: ${value}`
  );
};

// 时间格式化
const formatTime = (time: string | undefined) => {
  if (!time) return "";
  return dayjs(time).format("MM-DD");
};

const formatDateTime = (time: string | undefined) => {
  if (!time) return "";
  return dayjs(time).format("YYYY-MM-DD HH:mm");
};

// 事件处理
const handleCategoryChange = () => {
  displayCount.value = props.maxDisplay;
};

const refreshAchievements = async () => {
  loading.value = true;
  try {
    await analyticsStore.fetchAchievements();
    ElMessage.success("成就数据刷新成功");
  } catch (error) {
    ElMessage.error("刷新失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

const loadMore = () => {
  loadingMore.value = true;
  setTimeout(() => {
    displayCount.value += props.maxDisplay;
    loadingMore.value = false;
  }, 500);
};

const showAchievementDetail = (achievement: Achievement) => {
  selectedAchievement.value = achievement;
  showDetailDialog.value = true;
};

const shareAchievement = () => {
  if (!selectedAchievement.value) return;

  // 复制分享文本到剪贴板
  const shareText = `我在五好伴学中解锁了「${selectedAchievement.value.name}」成就！🏆 ${selectedAchievement.value.description}`;

  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareText).then(() => {
      ElMessage.success("成就信息已复制到剪贴板");
    });
  } else {
    ElMessage.info("分享功能暂不支持当前浏览器");
  }
};

// 监听数据变化
watch(
  () => analyticsStore.achievements,
  () => {
    // 成就数据更新时的处理
  },
  { deep: true },
);

onMounted(() => {
  // 初始化成就数据
  if (achievements.value.length === 0) {
    analyticsStore.fetchAchievements();
  }

  // 自动刷新
  if (props.autoRefresh) {
    const interval = setInterval(() => {
      analyticsStore.fetchAchievements();
    }, 300000); // 5分钟刷新一次

    // 组件卸载时清理定时器
    onUnmounted(() => {
      clearInterval(interval);
    });
  }
});
</script>

<style scoped>
.achievement-display {
  width: 100%;
}

.achievement-item {
  min-height: 140px;
}

.achievement-item:hover {
  transform: translateY(-2px);
}

.achievement-list-item:hover {
  transform: translateY(-1px);
}

.achievement-icon-large {
  position: relative;
}

.achievement-icon-large::before {
  content: "";
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: linear-gradient(
    45deg,
    transparent,
    rgba(59, 130, 246, 0.1),
    transparent
  );
  z-index: -1;
}

.progress-container {
  width: 100%;
}

.achievement-detail .progress-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

/* 稀有度特效 */
.achievement-item.legendary {
  animation: legendary-glow 2s ease-in-out infinite alternate;
}

@keyframes legendary-glow {
  0% {
    box-shadow: 0 0 5px rgba(245, 158, 11, 0.5);
  }
  100% {
    box-shadow:
      0 0 20px rgba(245, 158, 11, 0.8),
      0 0 30px rgba(245, 158, 11, 0.4);
  }
}

/* 响应式适配 */
@media (max-width: 768px) {
  .achievement-display :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto !important;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .achievement-item {
    min-height: 120px;
  }
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .achievement-display .bg-white {
    background-color: #1f2937;
    border-color: #374151;
  }

  .achievement-display .text-gray-900 {
    color: #f9fafb;
  }

  .achievement-display .text-gray-600 {
    color: #d1d5db;
  }

  .achievement-display .border-gray-200 {
    border-color: #374151;
  }
}
</style>
