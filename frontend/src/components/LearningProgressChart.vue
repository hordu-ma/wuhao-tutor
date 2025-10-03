<template>
  <div class="learning-progress-chart">
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <!-- 头部控制 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <el-icon class="text-blue-500 mr-2">
              <TrendCharts />
            </el-icon>
            学习进度对比
          </h3>
          <p class="text-sm text-gray-600 mt-1">查看不同时间段的学习表现趋势</p>
        </div>
        <div class="flex items-center space-x-3">
          <el-select
            v-model="selectedMetric"
            size="small"
            @change="handleMetricChange"
          >
            <el-option label="学习时长" value="studyTime" />
            <el-option label="作业完成" value="homework" />
            <el-option label="平均分数" value="score" />
            <el-option label="提问次数" value="questions" />
          </el-select>
          <el-select
            v-model="selectedPeriod"
            size="small"
            @change="handlePeriodChange"
          >
            <el-option label="最近7天" value="7d" />
            <el-option label="最近30天" value="30d" />
            <el-option label="最近90天" value="90d" />
          </el-select>
          <el-button
            size="small"
            type="primary"
            :icon="Refresh"
            @click="refreshData"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 对比选项 -->
      <div class="comparison-controls mb-6">
        <div class="flex items-center space-x-4">
          <el-checkbox
            v-model="showComparison"
            @change="handleComparisonToggle"
          >
            显示对比
          </el-checkbox>
          <el-select
            v-if="showComparison"
            v-model="comparisonPeriod"
            size="small"
            placeholder="选择对比期"
            @change="handleComparisonChange"
          >
            <el-option label="上周同期" value="last_week" />
            <el-option label="上月同期" value="last_month" />
            <el-option label="去年同期" value="last_year" />
            <el-option label="自定义期间" value="custom" />
          </el-select>
          <el-switch
            v-model="showTrendLine"
            active-text="趋势线"
            inactive-text="柱状图"
            size="small"
            @change="handleChartTypeChange"
          />
        </div>
      </div>

      <!-- 关键指标卡片 -->
      <div class="metrics-summary grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div
          v-for="metric in metricsData"
          :key="metric.key"
          class="metric-card p-4 rounded-lg border-2 transition-all duration-200"
          :class="getMetricCardClass(metric)"
        >
          <div class="flex items-center justify-between mb-2">
            <el-icon :class="metric.iconClass">
              <component :is="metric.icon" />
            </el-icon>
            <div
              class="trend-badge text-xs px-2 py-1 rounded-full"
              :class="getTrendBadgeClass(metric.trend)"
            >
              {{ metric.trend > 0 ? "+" : "" }}{{ metric.trend }}%
            </div>
          </div>
          <div class="metric-value text-xl font-bold text-gray-900 mb-1">
            {{ metric.value }}
          </div>
          <div class="metric-label text-sm text-gray-600">
            {{ metric.label }}
          </div>
          <div class="metric-subtitle text-xs text-gray-500 mt-1">
            vs {{ comparisonLabel }}
          </div>
        </div>
      </div>

      <!-- 主图表 -->
      <div class="chart-container mb-6">
        <div ref="mainChart" class="w-full h-80"></div>
      </div>

      <!-- 数据表格 -->
      <div v-if="showDataTable" class="data-table">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-md font-semibold text-gray-900">详细数据</h4>
          <div class="flex items-center space-x-2">
            <el-button size="small" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            <el-button size="small" @click="showDataTable = false" type="text">
              隐藏表格
            </el-button>
          </div>
        </div>
        <el-table
          :data="tableData"
          size="small"
          :max-height="300"
          style="width: 100%"
        >
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column
            :prop="selectedMetric"
            :label="getMetricLabel(selectedMetric)"
            width="120"
          >
            <template #default="{ row }">
              <span class="font-medium">{{
                formatMetricValue(row[selectedMetric])
              }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="showComparison"
            prop="comparisonValue"
            label="对比值"
            width="120"
          >
            <template #default="{ row }">
              <span class="text-gray-600">{{
                formatMetricValue(row.comparisonValue)
              }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="showComparison"
            prop="difference"
            label="差异"
            width="100"
          >
            <template #default="{ row }">
              <span
                :class="row.difference >= 0 ? 'text-green-600' : 'text-red-600'"
                class="font-medium"
              >
                {{ row.difference >= 0 ? "+" : ""
                }}{{ formatMetricValue(row.difference) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="150">
            <template #default="{ row }">
              <span class="text-gray-500 text-xs">{{ row.notes || "-" }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 底部控制 -->
      <div
        class="chart-controls flex items-center justify-between pt-4 border-t"
      >
        <div class="flex items-center space-x-3">
          <el-button
            size="small"
            @click="showDataTable = !showDataTable"
            type="text"
          >
            {{ showDataTable ? "隐藏" : "显示" }}数据表格
          </el-button>
          <el-button size="small" @click="resetView" type="text">
            重置视图
          </el-button>
        </div>
        <div class="flex items-center space-x-2">
          <el-button size="small" @click="shareChart">
            <el-icon><Share /></el-icon>
            分享图表
          </el-button>
          <el-button size="small" @click="saveAsImage">
            <el-icon><Picture /></el-icon>
            保存图片
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import * as echarts from "echarts";
import { useAnalyticsStore } from "../stores/analytics";
import {
  TrendCharts,
  Refresh,
  Download,
  Share,
  Picture,
  Clock,
  Document,
  Flag,
  QuestionFilled,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { ECharts } from "echarts";
import dayjs from "dayjs";

interface Props {
  height?: string;
  defaultMetric?: string;
  showControls?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  height: "320px",
  defaultMetric: "studyTime",
  showControls: true,
});

const analyticsStore = useAnalyticsStore();

// 图表实例
const mainChart = ref<HTMLDivElement>();
let chartInstance: ECharts | null = null;

// 状态管理
const loading = ref(false);
const selectedMetric = ref(props.defaultMetric);
const selectedPeriod = ref("30d");
const showComparison = ref(false);
const comparisonPeriod = ref("last_week");
const showTrendLine = ref(true);
const showDataTable = ref(false);

// 计算属性
const progressData = computed(() => analyticsStore.learningProgress);

const comparisonLabel = computed(() => {
  const labels = {
    last_week: "上周",
    last_month: "上月",
    last_year: "去年",
    custom: "自定义期间",
  };
  return labels[comparisonPeriod.value as keyof typeof labels] || "对比期";
});

const metricsData = computed(() => {
  const current = getCurrentPeriodData();
  const comparison = getComparisonData();

  return [
    {
      key: "studyTime",
      label: "学习时长",
      value: `${Math.round(current.studyTime / 60)}h`,
      trend: calculateTrend(current.studyTime, comparison.studyTime),
      icon: Clock,
      iconClass: "text-blue-500",
    },
    {
      key: "homework",
      label: "完成作业",
      value: `${current.homework}份`,
      trend: calculateTrend(current.homework, comparison.homework),
      icon: Document,
      iconClass: "text-green-500",
    },
    {
      key: "score",
      label: "平均分数",
      value: `${current.score}分`,
      trend: calculateTrend(current.score, comparison.score),
      icon: Flag,
      iconClass: "text-yellow-500",
    },
    {
      key: "questions",
      label: "提问次数",
      value: `${current.questions}个`,
      trend: calculateTrend(current.questions, comparison.questions),
      icon: QuestionFilled,
      iconClass: "text-purple-500",
    },
  ];
});

const tableData = computed(() => {
  return progressData.value.map((item) => ({
    date: dayjs(item.date).format("MM-DD"),
    studyTime: item.studyTime,
    homework: item.homeworkCount,
    score: item.averageScore,
    questions: item.questionCount,
    comparisonValue: getComparisonValueForDate(item.date),
    difference:
      (item[selectedMetric.value as keyof typeof item] as number) -
      getComparisonValueForDate(item.date),
    notes: generateNotes(item),
  }));
});

// 工具函数
const getCurrentPeriodData = () => {
  const data = progressData.value;
  return {
    studyTime: data.reduce((sum, item) => sum + item.studyTime, 0),
    homework: data.reduce((sum, item) => sum + item.homeworkCount, 0),
    score:
      data.length > 0
        ? data.reduce((sum, item) => sum + item.averageScore, 0) / data.length
        : 0,
    questions: data.reduce((sum, item) => sum + item.questionCount, 0),
  };
};

const getComparisonData = () => {
  // 模拟对比期数据，实际应该从API获取
  const current = getCurrentPeriodData();
  const factor = comparisonPeriod.value === "last_week" ? 0.9 : 0.85;

  return {
    studyTime: current.studyTime * factor,
    homework: Math.round(current.homework * factor),
    score: current.score * (0.95 + Math.random() * 0.1),
    questions: Math.round(current.questions * factor),
  };
};

const calculateTrend = (current: number, comparison: number) => {
  if (comparison === 0) return 0;
  return Math.round(((current - comparison) / comparison) * 100);
};

const getComparisonValueForDate = (_date: string) => {
  // 模拟获取对比期同一天的数据
  return Math.round(Math.random() * 100 + 50);
};

const generateNotes = (item: any) => {
  if (item.studyTime > 120) return "学习时间较长";
  if (item.averageScore > 90) return "成绩优秀";
  if (item.homeworkCount === 0) return "未完成作业";
  return "";
};

// 样式类生成
const getMetricCardClass = (metric: any) => {
  if (selectedMetric.value === metric.key) {
    return "border-blue-300 bg-blue-50";
  }
  return "border-gray-200 hover:border-gray-300 cursor-pointer";
};

const getTrendBadgeClass = (trend: number) => {
  if (trend > 0) {
    return "bg-green-100 text-green-800";
  } else if (trend < 0) {
    return "bg-red-100 text-red-800";
  }
  return "bg-gray-100 text-gray-800";
};

const getMetricLabel = (metric: string) => {
  const labels = {
    studyTime: "学习时长(分钟)",
    homework: "作业数量",
    score: "平均分数",
    questions: "提问次数",
  };
  return labels[metric as keyof typeof labels] || metric;
};

const formatMetricValue = (value: number) => {
  if (selectedMetric.value === "studyTime") {
    return `${value}分钟`;
  } else if (selectedMetric.value === "score") {
    return `${value.toFixed(1)}分`;
  }
  return value.toString();
};

// 图表初始化
const initChart = () => {
  if (!mainChart.value) return;

  chartInstance = echarts.init(mainChart.value);

  const data = progressData.value;
  const xAxisData = data.map((item) => dayjs(item.date).format("MM-DD"));
  const seriesData = data.map(
    (item) => item[selectedMetric.value as keyof typeof item],
  );

  const option = {
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      borderColor: "#e5e7eb",
      borderWidth: 1,
      textStyle: {
        color: "#374151",
        fontSize: 12,
      },
      formatter: (params: any) => {
        let content = `<div style="padding: 8px;"><div style="font-weight: 600; margin-bottom: 4px;">${params[0].axisValue}</div>`;

        params.forEach((param: any) => {
          content += `<div style="color: ${param.color}; margin-bottom: 2px;">${param.seriesName}: ${formatMetricValue(param.value)}</div>`;
        });

        content += "</div>";
        return content;
      },
    },
    legend: {
      data: showComparison.value ? ["当前期间", "对比期间"] : ["当前期间"],
      top: "top",
      textStyle: {
        fontSize: 12,
        color: "#374151",
      },
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "8%",
      top: "15%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: xAxisData,
      axisLabel: {
        fontSize: 11,
        color: "#6b7280",
        rotate: 45,
      },
      axisLine: {
        lineStyle: {
          color: "#e5e7eb",
        },
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        fontSize: 11,
        color: "#6b7280",
        formatter: (value: number) => formatMetricValue(value),
      },
      axisLine: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: "#f3f4f6",
          type: "dashed",
        },
      },
    },
    series: [
      {
        name: "当前期间",
        type: showTrendLine.value ? "line" : "bar",
        data: seriesData,
        smooth: true,
        itemStyle: {
          color: "#3b82f6",
          borderWidth: 2,
          borderColor: "#ffffff",
        },
        lineStyle: showTrendLine.value
          ? {
              width: 3,
              color: "#3b82f6",
            }
          : undefined,
        areaStyle: showTrendLine.value
          ? {
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: "rgba(59, 130, 246, 0.25)" },
                  { offset: 1, color: "rgba(59, 130, 246, 0.05)" },
                ],
              },
            }
          : undefined,
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: "cubicOut",
  };

  // 添加对比数据
  if (showComparison.value) {
    const comparisonData = data.map(() => Math.random() * 100 + 20);
    (option.series as any[]).push({
      name: "对比期间",
      type: showTrendLine.value ? "line" : "bar",
      data: comparisonData,
      smooth: true,
      itemStyle: {
        color: "#10b981",
        borderWidth: 2,
        borderColor: "#ffffff",
      },
      lineStyle: showTrendLine.value
        ? {
            width: 2,
            color: "#10b981",
          }
        : undefined,
      areaStyle: undefined,
    });
  }

  chartInstance.setOption(option as any);
};

// 事件处理
const handleMetricChange = () => {
  initChart();
};

const handlePeriodChange = () => {
  analyticsStore.fetchLearningProgress(
    dayjs()
      .subtract(parseInt(selectedPeriod.value), "day")
      .format("YYYY-MM-DD"),
    dayjs().format("YYYY-MM-DD"),
  );
};

const handleComparisonToggle = () => {
  initChart();
};

const handleComparisonChange = () => {
  initChart();
};

const handleChartTypeChange = () => {
  initChart();
};

const refreshData = async () => {
  loading.value = true;
  try {
    await handlePeriodChange();
    ElMessage.success("数据刷新成功");
  } catch (error) {
    ElMessage.error("刷新失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

const exportData = () => {
  const csvContent = [
    ["日期", getMetricLabel(selectedMetric.value), "对比值", "差异", "备注"],
    ...tableData.value.map((row) => [
      row.date,
      formatMetricValue(
        row[selectedMetric.value as keyof typeof row] as number,
      ),
      formatMetricValue(row.comparisonValue),
      formatMetricValue(row.difference),
      row.notes || "",
    ]),
  ]
    .map((row) => row.join(","))
    .join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `学习进度对比_${dayjs().format("YYYY-MM-DD")}.csv`,
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  ElMessage.success("数据导出成功");
};

const shareChart = () => {
  ElMessage.info("分享功能开发中");
};

const saveAsImage = () => {
  if (chartInstance) {
    const imgUrl = chartInstance.getDataURL({
      type: "png",
      pixelRatio: 2,
      backgroundColor: "#ffffff",
    });

    const link = document.createElement("a");
    link.download = `学习进度图表_${dayjs().format("YYYY-MM-DD")}.png`;
    link.href = imgUrl;
    link.click();

    ElMessage.success("图表已保存");
  }
};

const resetView = () => {
  selectedMetric.value = props.defaultMetric;
  selectedPeriod.value = "30d";
  showComparison.value = false;
  showTrendLine.value = true;
  showDataTable.value = false;
  initChart();
};

// 响应式处理
const handleResize = () => {
  chartInstance?.resize();
};

// 监听数据变化
watch(
  () => progressData.value,
  () => {
    if (chartInstance) {
      initChart();
    }
  },
  { deep: true },
);

onMounted(() => {
  setTimeout(() => {
    initChart();
  }, 100);

  window.addEventListener("resize", handleResize);

  // 初始化数据
  if (progressData.value.length === 0) {
    handlePeriodChange();
  }
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  chartInstance?.dispose();
});
</script>

<style scoped>
.learning-progress-chart {
  width: 100%;
}

.metric-card {
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card.selected {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.trend-badge {
  font-weight: 600;
  letter-spacing: 0.025em;
}

.chart-container {
  position: relative;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.data-table {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.data-table :deep(.el-table) {
  background: transparent;
}

.data-table :deep(.el-table th) {
  background-color: #f3f4f6;
  border-color: #e5e7eb;
}

.data-table :deep(.el-table td) {
  border-color: #f3f4f6;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .metrics-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .comparison-controls {
    flex-direction: column;
    align-items: flex-start;
  }

  .comparison-controls > div {
    flex-wrap: wrap;
    gap: 8px;
  }

  .chart-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .chart-controls > div {
    justify-content: center;
  }
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .learning-progress-chart .bg-white {
    background-color: #1f2937;
    border-color: #374151;
  }

  .learning-progress-chart .text-gray-900 {
    color: #f9fafb;
  }

  .learning-progress-chart .text-gray-600 {
    color: #d1d5db;
  }

  .learning-progress-chart .border-gray-200 {
    border-color: #374151;
  }

  .chart-container {
    background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
    border-color: #6b7280;
  }
}
</style>
