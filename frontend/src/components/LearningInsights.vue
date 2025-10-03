<template>
  <div class="learning-insights">
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <!-- 头部信息 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <el-icon class="text-purple-500 mr-2">
              <DataAnalysis />
            </el-icon>
            智能学习洞察
          </h3>
          <p class="text-sm text-gray-600 mt-1">
            基于AI分析的个性化学习建议和趋势预测
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <el-select
            v-model="selectedInsightType"
            size="small"
            @change="handleInsightTypeChange"
          >
            <el-option label="全面分析" value="comprehensive" />
            <el-option label="学习效率" value="efficiency" />
            <el-option label="知识掌握" value="knowledge" />
            <el-option label="进步趋势" value="progress" />
            <el-option label="风险预警" value="risk" />
          </el-select>
          <el-button
            size="small"
            type="primary"
            :icon="MagicStick"
            @click="generateInsights"
            :loading="generating"
          >
            生成洞察
          </el-button>
        </div>
      </div>

      <!-- 洞察生成状态 -->
      <div v-if="generating" class="generating-state mb-6">
        <div class="flex items-center justify-center py-8">
          <div class="text-center">
            <el-icon class="text-4xl text-purple-500 mb-4 animate-spin">
              <Loading />
            </el-icon>
            <p class="text-gray-600 mb-2">AI正在分析您的学习数据...</p>
            <div class="text-sm text-gray-500">
              {{ generatingProgress }}% 完成
            </div>
            <el-progress
              :percentage="generatingProgress"
              :stroke-width="6"
              color="#8b5cf6"
              class="mt-2"
            />
          </div>
        </div>
      </div>

      <!-- 智能洞察内容 -->
      <div v-else-if="insights" class="insights-content">
        <!-- 总体评分 -->
        <div class="overall-score mb-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div
              class="score-card text-center p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200"
            >
              <div class="score-circle mx-auto mb-3">
                <el-progress
                  type="circle"
                  :percentage="insights.overallScore"
                  :width="80"
                  :stroke-width="6"
                  :color="getScoreColor(insights.overallScore)"
                />
              </div>
              <h4 class="text-lg font-semibold text-gray-900 mb-1">综合评分</h4>
              <p class="text-sm text-gray-600">
                {{ getScoreDescription(insights.overallScore) }}
              </p>
            </div>

            <div
              class="efficiency-card text-center p-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200"
            >
              <div class="efficiency-meter mb-3">
                <el-icon class="text-4xl text-green-500">
                  <TrendCharts />
                </el-icon>
              </div>
              <h4 class="text-lg font-semibold text-gray-900 mb-1">学习效率</h4>
              <div class="text-2xl font-bold text-green-600 mb-1">
                {{ insights.efficiency }}%
              </div>
              <p class="text-sm text-gray-600">
                {{ getEfficiencyTrend(insights.efficiency) }}
              </p>
            </div>

            <div
              class="prediction-card text-center p-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200"
            >
              <div class="prediction-icon mb-3">
                <el-icon class="text-4xl text-purple-500">
                  <Opportunity />
                </el-icon>
              </div>
              <h4 class="text-lg font-semibold text-gray-900 mb-1">进步预测</h4>
              <div class="text-lg font-bold text-purple-600 mb-1">
                {{ insights.progressPrediction }}
              </div>
              <p class="text-sm text-gray-600">基于当前学习轨迹</p>
            </div>
          </div>
        </div>

        <!-- 关键洞察 -->
        <div class="key-insights mb-6">
          <h4
            class="text-md font-semibold text-gray-900 mb-4 flex items-center"
          >
            <el-icon class="text-yellow-500 mr-2">
              <Star />
            </el-icon>
            关键发现
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="insight in insights.keyFindings"
              :key="insight.id"
              class="insight-item p-4 rounded-lg border-l-4 transition-all duration-200 hover:shadow-md"
              :class="getInsightCardClass(insight.type)"
            >
              <div class="flex items-start space-x-3">
                <div class="insight-icon mt-1">
                  <el-icon :class="getInsightIconClass(insight.type)">
                    <component :is="getInsightIcon(insight.type)" />
                  </el-icon>
                </div>
                <div class="flex-1">
                  <h5 class="font-medium text-gray-900 mb-1">
                    {{ insight.title }}
                  </h5>
                  <p class="text-sm text-gray-600 mb-2">
                    {{ insight.description }}
                  </p>
                  <div
                    class="insight-meta flex items-center text-xs text-gray-500"
                  >
                    <span
                      class="confidence-badge px-2 py-1 rounded-full bg-gray-100"
                    >
                      置信度: {{ insight.confidence }}%
                    </span>

                    <span class="ml-2">{{ insight.category }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 学习模式分析 -->
        <div class="learning-patterns mb-6">
          <h4
            class="text-md font-semibold text-gray-900 mb-4 flex items-center"
          >
            <el-icon class="text-blue-500 mr-2">
              <DataLine />
            </el-icon>
            学习模式分析
          </h4>
          <div class="patterns-grid grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="pattern-card p-4 bg-gray-50 rounded-lg">
              <h5 class="font-medium text-gray-900 mb-3">时间偏好</h5>
              <div class="space-y-2">
                <div
                  v-for="(period, index) in insights.timePreferences"
                  :key="index"
                  class="flex items-center justify-between"
                >
                  <span class="text-sm text-gray-600">{{ period.period }}</span>
                  <div class="flex items-center space-x-2">
                    <div class="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        class="bg-blue-500 h-2 rounded-full"
                        :style="{ width: period.preference + '%' }"
                      ></div>
                    </div>
                    <span class="text-xs text-gray-500"
                      >{{ period.preference }}%</span
                    >
                  </div>
                </div>
              </div>
            </div>

            <div class="pattern-card p-4 bg-gray-50 rounded-lg">
              <h5 class="font-medium text-gray-900 mb-3">学科倾向</h5>
              <div class="space-y-2">
                <div
                  v-for="(subject, index) in insights.subjectPreferences"
                  :key="index"
                  class="flex items-center justify-between"
                >
                  <span class="text-sm text-gray-600">{{ subject.name }}</span>
                  <div class="flex items-center space-x-2">
                    <el-tag
                      :type="getSubjectTagType(subject.level) as any"
                      size="small"
                    >
                      {{ subject.level }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div class="pattern-card p-4 bg-gray-50 rounded-lg">
              <h5 class="font-medium text-gray-900 mb-3">学习风格</h5>
              <div class="learning-style-radar">
                <div ref="styleRadar" class="w-full h-32"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 改进建议 -->
        <div class="improvement-suggestions mb-6">
          <h4
            class="text-md font-semibold text-gray-900 mb-4 flex items-center"
          >
            <el-icon class="text-orange-500 mr-2">
              <Guide />
            </el-icon>
            改进建议
          </h4>
          <div class="suggestions-list space-y-3">
            <div
              v-for="suggestion in insights.suggestions"
              :key="suggestion.id"
              class="suggestion-item p-4 border border-gray-200 rounded-lg hover:border-orange-300 transition-colors"
            >
              <div class="flex items-start space-x-3">
                <div class="suggestion-priority">
                  <el-tag
                    :type="getPriorityTagType(suggestion.priority) as any"
                    size="small"
                  >
                    {{ getPriorityText(suggestion.priority) }}
                  </el-tag>
                </div>
                <div class="flex-1">
                  <h5 class="font-medium text-gray-900 mb-1">
                    {{ suggestion.title }}
                  </h5>
                  <p class="text-sm text-gray-600 mb-2">
                    {{ suggestion.description }}
                  </p>
                  <div class="suggestion-actions flex items-center space-x-2">
                    <el-button
                      size="small"
                      type="primary"
                      @click="applySuggestion(suggestion)"
                    >
                      应用建议
                    </el-button>
                    <el-button
                      size="small"
                      @click="dismissSuggestion(suggestion)"
                    >
                      忽略
                    </el-button>
                    <span class="text-xs text-gray-500 ml-auto">
                      预期提升: {{ suggestion.expectedImprovement }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 风险预警 -->
        <div
          v-if="insights.risks && insights.risks.length > 0"
          class="risk-alerts mb-6"
        >
          <h4
            class="text-md font-semibold text-gray-900 mb-4 flex items-center"
          >
            <el-icon class="text-red-500 mr-2">
              <Warning />
            </el-icon>
            风险预警
          </h4>
          <div class="alerts-list space-y-3">
            <el-alert
              v-for="risk in insights.risks"
              :key="risk.id"
              :title="risk.title"
              :type="getRiskAlertType(risk.level) as any"
              :description="risk.description"
              :closable="false"
              show-icon
            >
              <template #default>
                <div class="mt-2 text-sm">
                  <strong>建议措施:</strong> {{ risk.recommendation }}
                </div>
              </template>
            </el-alert>
          </div>
        </div>

        <!-- 学习路径推荐 -->
        <div class="learning-path mb-6">
          <h4
            class="text-md font-semibold text-gray-900 mb-4 flex items-center"
          >
            <el-icon class="text-indigo-500 mr-2">
              <Connection />
            </el-icon>
            智能学习路径
          </h4>
          <div class="path-visualization">
            <div
              ref="learningPath"
              class="w-full h-64 bg-gray-50 rounded-lg border"
            ></div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state text-center py-12">
        <el-icon class="text-6xl text-gray-400 mb-4">
          <DataAnalysis />
        </el-icon>
        <h4 class="text-lg font-medium text-gray-600 mb-2">
          还没有生成洞察报告
        </h4>
        <p class="text-gray-500 mb-4">
          点击"生成洞察"按钮，让AI为您分析学习数据
        </p>
        <el-button type="primary" :icon="MagicStick" @click="generateInsights">
          开始分析
        </el-button>
      </div>

      <!-- 底部操作 -->
      <div
        v-if="insights"
        class="insights-actions flex items-center justify-between pt-6 border-t"
      >
        <div class="flex items-center space-x-3">
          <el-button size="small" @click="exportInsights">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
          <el-button size="small" @click="shareInsights">
            <el-icon><Share /></el-icon>
            分享洞察
          </el-button>
        </div>
        <div class="flex items-center space-x-2 text-sm text-gray-500">
          <el-icon><Clock /></el-icon>
          <span>更新于 {{ formatTime(insights.generatedAt) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import * as echarts from "echarts";
import {
  DataAnalysis,
  MagicStick,
  Loading,
  TrendCharts,
  Opportunity,
  Star,
  DataLine,
  Guide,
  Warning,
  Connection,
  Download,
  Share,
  Clock,
  Check,
  Close,
  QuestionFilled,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { ECharts } from "echarts";
import dayjs from "dayjs";

interface InsightData {
  overallScore: number;
  efficiency: number;
  progressPrediction: string;
  keyFindings: Array<{
    id: string;
    type: "strength" | "weakness" | "opportunity" | "threat";
    title: string;
    description: string;
    confidence: number;
    category: string;
  }>;
  timePreferences: Array<{
    period: string;
    preference: number;
  }>;
  subjectPreferences: Array<{
    name: string;
    level: "excellent" | "good" | "average" | "needs_improvement";
  }>;
  suggestions: Array<{
    id: string;
    priority: "high" | "medium" | "low";
    title: string;
    description: string;
    expectedImprovement: string;
  }>;
  risks?: Array<{
    id: string;
    level: "high" | "medium" | "low";
    title: string;
    description: string;
    recommendation: string;
  }>;
  generatedAt: string;
}

// const analyticsStore = useAnalyticsStore();

// 图表实例
const styleRadar = ref<HTMLDivElement>();
const learningPath = ref<HTMLDivElement>();
let styleRadarInstance: ECharts | null = null;
let learningPathInstance: ECharts | null = null;

// 状态管理
const generating = ref(false);
const generatingProgress = ref(0);
const selectedInsightType = ref("comprehensive");
const insights = ref<InsightData | null>(null);

// 模拟洞察数据生成
const generateMockInsights = (): InsightData => {
  return {
    overallScore: 78,
    efficiency: 73,
    progressPrediction: "预计下月提升15%",
    keyFindings: [
      {
        id: "1",
        type: "strength",
        title: "数学学科表现优异",
        description: "在数学学科上表现出色，平均分达到89分，高于班级平均水平",
        confidence: 92,
        category: "学科表现",
      },
      {
        id: "2",
        type: "weakness",
        title: "英语听力需要加强",
        description: "英语听力部分得分较低，建议增加听力练习时间",
        confidence: 85,
        category: "技能提升",
      },
      {
        id: "3",
        type: "opportunity",
        title: "学习时间集中度高",
        description: "晚上7-9点学习效率最高，建议在此时间段安排重点学习",
        confidence: 88,
        category: "时间管理",
      },
      {
        id: "4",
        type: "threat",
        title: "作业完成时间不稳定",
        description: "作业完成时间波动较大，可能影响学习节奏",
        confidence: 76,
        category: "学习习惯",
      },
    ],
    timePreferences: [
      { period: "早上(6-12点)", preference: 45 },
      { period: "下午(12-18点)", preference: 65 },
      { period: "晚上(18-24点)", preference: 85 },
    ],
    subjectPreferences: [
      { name: "数学", level: "excellent" },
      { name: "物理", level: "good" },
      { name: "化学", level: "average" },
      { name: "英语", level: "needs_improvement" },
    ],
    suggestions: [
      {
        id: "s1",
        priority: "high",
        title: "增加英语听力练习",
        description: "每天安排30分钟英语听力练习，使用多样化的听力材料",
        expectedImprovement: "英语成绩提升10-15分",
      },
      {
        id: "s2",
        priority: "medium",
        title: "优化学习时间分配",
        description: "将更多的重难点学习安排在晚上7-9点的高效时段",
        expectedImprovement: "整体学习效率提升20%",
      },
      {
        id: "s3",
        priority: "low",
        title: "建立作业完成计划",
        description: "制定固定的作业完成时间表，保持学习节奏的稳定性",
        expectedImprovement: "作业质量提升",
      },
    ],
    risks: [
      {
        id: "r1",
        level: "medium",
        title: "学习疲劳风险",
        description: "连续学习时间过长，可能导致学习效率下降",
        recommendation: "增加适当的休息间隔，采用番茄工作法",
      },
    ],
    generatedAt: new Date().toISOString(),
  };
};

// 样式和工具函数
const getScoreColor = (score: number) => {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
};

const getScoreDescription = (score: number) => {
  if (score >= 80) return "表现优秀";
  if (score >= 60) return "表现良好";
  return "有待提升";
};

const getEfficiencyTrend = (efficiency: number) => {
  if (efficiency >= 75) return "效率很高";
  if (efficiency >= 50) return "效率中等";
  return "效率偏低";
};

const getInsightCardClass = (type: string) => {
  const classMap = {
    strength: "border-green-400 bg-green-50",
    weakness: "border-red-400 bg-red-50",
    opportunity: "border-blue-400 bg-blue-50",
    threat: "border-yellow-400 bg-yellow-50",
  };
  return (
    classMap[type as keyof typeof classMap] || "border-gray-400 bg-gray-50"
  );
};

const getInsightIconClass = (type: string) => {
  const classMap = {
    strength: "text-green-500",
    weakness: "text-red-500",
    opportunity: "text-blue-500",
    threat: "text-yellow-500",
  };
  return classMap[type as keyof typeof classMap] || "text-gray-500";
};

const getInsightIcon = (type: string) => {
  const iconMap = {
    strength: Check,
    weakness: Close,
    opportunity: Opportunity,
    threat: Warning,
  };
  return iconMap[type as keyof typeof iconMap] || QuestionFilled;
};

const getSubjectTagType = (level: string) => {
  const typeMap = {
    excellent: "success",
    good: "primary",
    average: "warning",
    needs_improvement: "danger",
  };
  return typeMap[level as keyof typeof typeMap] || "info";
};

const getPriorityTagType = (priority: string) => {
  const typeMap = {
    high: "danger",
    medium: "warning",
    low: "info",
  };
  return typeMap[priority as keyof typeof typeMap] || "info";
};

const getPriorityText = (priority: string) => {
  const textMap = {
    high: "高优先级",
    medium: "中优先级",
    low: "低优先级",
  };
  return textMap[priority as keyof typeof textMap] || priority;
};

const getRiskAlertType = (level: string) => {
  const typeMap = {
    high: "error",
    medium: "warning",
    low: "info",
  };
  return typeMap[level as keyof typeof typeMap] || "info";
};

const formatTime = (time: string) => {
  return dayjs(time).format("MM-DD HH:mm");
};

// 图表初始化
const initStyleRadar = () => {
  if (!styleRadar.value || !insights.value) return;

  styleRadarInstance = echarts.init(styleRadar.value);

  const option = {
    radar: {
      indicator: [
        { name: "视觉", max: 100 },
        { name: "听觉", max: 100 },
        { name: "动手", max: 100 },
        { name: "阅读", max: 100 },
      ],
      radius: "60%",
      splitNumber: 4,
      shape: "polygon",
      splitArea: {
        areaStyle: {
          color: ["rgba(59, 130, 246, 0.1)", "rgba(59, 130, 246, 0.05)"],
        },
      },
      splitLine: {
        lineStyle: {
          color: "#e5e7eb",
        },
      },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: [75, 60, 80, 85],
            areaStyle: {
              color: "rgba(59, 130, 246, 0.2)",
            },
            lineStyle: {
              color: "#3b82f6",
              width: 2,
            },
          },
        ],
      },
    ],
  };

  styleRadarInstance.setOption(option);
};

const initLearningPath = () => {
  if (!learningPath.value || !insights.value) return;

  learningPathInstance = echarts.init(learningPath.value);

  const option = {
    tooltip: {
      trigger: "item",
    },
    series: [
      {
        type: "graph",
        layout: "force",
        data: [
          {
            name: "当前水平",
            x: 100,
            y: 150,
            symbolSize: 50,
            itemStyle: { color: "#3b82f6" },
          },
          {
            name: "基础巩固",
            x: 250,
            y: 100,
            symbolSize: 40,
            itemStyle: { color: "#10b981" },
          },
          {
            name: "技能提升",
            x: 250,
            y: 200,
            symbolSize: 40,
            itemStyle: { color: "#f59e0b" },
          },
          {
            name: "综合应用",
            x: 400,
            y: 150,
            symbolSize: 60,
            itemStyle: { color: "#8b5cf6" },
          },
        ],
        links: [
          { source: "当前水平", target: "基础巩固" },
          { source: "当前水平", target: "技能提升" },
          { source: "基础巩固", target: "综合应用" },
          { source: "技能提升", target: "综合应用" },
        ],
        label: {
          show: true,
          fontSize: 12,
        },
        force: {
          repulsion: 100,
          edgeLength: 100,
        },
      },
    ],
  };

  learningPathInstance.setOption(option);
};

// 事件处理
const handleInsightTypeChange = () => {
  if (insights.value) {
    generateInsights();
  }
};

const generateInsights = async () => {
  generating.value = true;
  generatingProgress.value = 0;

  // 模拟生成过程
  const interval = setInterval(() => {
    generatingProgress.value += 10;
    if (generatingProgress.value >= 100) {
      clearInterval(interval);
      insights.value = generateMockInsights();
      generating.value = false;

      // 初始化图表
      setTimeout(() => {
        initStyleRadar();
        initLearningPath();
      }, 100);

      ElMessage.success("智能洞察生成完成");
    }
  }, 200);
};

const applySuggestion = (suggestion: any) => {
  ElMessage.success(`已应用建议: ${suggestion.title}`);
};

const dismissSuggestion = (suggestion: any) => {
  ElMessage.info(`已忽略建议: ${suggestion.title}`);
};

const exportInsights = () => {
  ElMessage.info("导出功能开发中");
};

const shareInsights = () => {
  ElMessage.info("分享功能开发中");
};

// 响应式处理
const handleResize = () => {
  styleRadarInstance?.resize();
  learningPathInstance?.resize();
};

onMounted(() => {
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  styleRadarInstance?.dispose();
  learningPathInstance?.dispose();
});
</script>

<style scoped>
.learning-insights {
  width: 100%;
}

.generating-state {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.score-card,
.efficiency-card,
.prediction-card {
  transition: transform 0.2s ease-in-out;
}

.score-card:hover,
.efficiency-card:hover,
.prediction-card:hover {
  transform: translateY(-2px);
}

.insight-item {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.8) 0%,
    rgba(249, 250, 251, 0.8) 100%
  );
}

.insight-item:hover {
  transform: translateY(-1px);
}

.pattern-card {
  transition: all 0.2s ease-in-out;
}

.pattern-card:hover {
  background-color: #f3f4f6;
  transform: translateY(-1px);
}

.suggestion-item {
  transition: all 0.2s ease-in-out;
}

.suggestion-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.confidence-badge {
  font-size: 10px;
  font-weight: 600;
}

.path-visualization {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  padding: 16px;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.insights-content > div {
  animation: fadeInUp 0.6s ease-out;
}

.insights-content > div:nth-child(1) {
  animation-delay: 0.1s;
}
.insights-content > div:nth-child(2) {
  animation-delay: 0.2s;
}
.insights-content > div:nth-child(3) {
  animation-delay: 0.3s;
}
.insights-content > div:nth-child(4) {
  animation-delay: 0.4s;
}
.insights-content > div:nth-child(5) {
  animation-delay: 0.5s;
}
.insights-content > div:nth-child(6) {
  animation-delay: 0.6s;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .overall-score .grid {
    grid-template-columns: 1fr;
  }

  .key-insights .grid {
    grid-template-columns: 1fr;
  }

  .patterns-grid {
    grid-template-columns: 1fr;
  }

  .insights-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .insights-actions > div {
    justify-content: center;
  }
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .learning-insights .bg-white {
    background-color: #1f2937;
    border-color: #374151;
  }

  .learning-insights .text-gray-900 {
    color: #f9fafb;
  }

  .learning-insights .text-gray-600 {
    color: #d1d5db;
  }

  .learning-insights .border-gray-200 {
    border-color: #374151;
  }

  .pattern-card {
    background-color: #374151;
  }

  .pattern-card:hover {
    background-color: #4b5563;
  }
}
</style>
