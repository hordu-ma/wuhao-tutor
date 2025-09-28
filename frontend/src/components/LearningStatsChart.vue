<template>
  <div class="learning-stats-chart">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div
        v-for="stat in statsCards"
        :key="stat.key"
        class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm text-gray-600">{{ stat.label }}</div>
          <el-icon class="text-lg" :class="stat.color">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="text-2xl font-bold text-gray-900 mb-1">
          {{ stat.value }}
        </div>
        <div class="flex items-center text-xs">
          <span
            :class="
              stat.trend > 0
                ? 'text-green-600'
                : stat.trend < 0
                  ? 'text-red-600'
                  : 'text-gray-500'
            "
          >
            {{ stat.trend > 0 ? "↗" : stat.trend < 0 ? "↘" : "→" }}
            {{ Math.abs(stat.trend) }}%
          </span>
          <span class="text-gray-500 ml-1">vs 上周</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 学习时长趋势 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">学习时长趋势</h3>
          <el-select
            v-model="timeRange"
            size="small"
            @change="handleTimeRangeChange"
          >
            <el-option label="最近7天" value="7d" />
            <el-option label="最近30天" value="30d" />
            <el-option label="最近90天" value="90d" />
          </el-select>
        </div>
        <div ref="studyTimeChart" class="w-full h-64"></div>
      </div>

      <!-- 学科分布 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">学科学习分布</h3>
        <div ref="subjectChart" class="w-full h-64"></div>
      </div>

      <!-- 学习效率分析 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">学习效率分析</h3>
        <div ref="efficiencyChart" class="w-full h-64"></div>
      </div>

      <!-- 知识点掌握度 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">知识点掌握度</h3>
          <el-select
            v-model="selectedSubject"
            size="small"
            @change="handleSubjectChange"
          >
            <el-option label="全部学科" value="" />
            <el-option
              v-for="subject in subjects"
              :key="subject"
              :label="subject"
              :value="subject"
            />
          </el-select>
        </div>
        <div ref="knowledgeChart" class="w-full h-64"></div>
      </div>
    </div>

    <!-- 学习热力图 -->
    <div class="mt-6 bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">学习活跃度热力图</h3>
        <el-select
          v-model="selectedYear"
          size="small"
          @change="handleYearChange"
        >
          <el-option
            v-for="year in years"
            :key="year"
            :label="year"
            :value="year"
          />
        </el-select>
      </div>
      <div ref="heatmapChart" class="w-full h-40"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from "vue";
import * as echarts from "echarts";
import { useAnalyticsStore } from "../stores/analytics";
import { Clock, Document, TrendCharts, Flag } from "@element-plus/icons-vue";
import type { ECharts } from "echarts";
import dayjs from "dayjs";

interface Props {
  height?: string;
  autoRefresh?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  height: "400px",
  autoRefresh: false,
});

const analyticsStore = useAnalyticsStore();

// 图表实例引用
const studyTimeChart = ref<HTMLDivElement>();
const subjectChart = ref<HTMLDivElement>();
const efficiencyChart = ref<HTMLDivElement>();
const knowledgeChart = ref<HTMLDivElement>();
const heatmapChart = ref<HTMLDivElement>();

// 图表实例
let studyTimeChartInstance: ECharts | null = null;
let subjectChartInstance: ECharts | null = null;
let efficiencyChartInstance: ECharts | null = null;
let knowledgeChartInstance: ECharts | null = null;
let heatmapChartInstance: ECharts | null = null;

// 控制状态
const timeRange = ref("30d");
const selectedSubject = ref("");
const selectedYear = ref(new Date().getFullYear());

// 数据
const subjects = computed(() => {
  return Array.from(new Set(analyticsStore.subjectStats.map((s) => s.subject)));
});

const years = computed(() => {
  const currentYear = new Date().getFullYear();
  return Array.from({ length: 3 }, (_, i) => currentYear - i);
});

// 统计卡片数据
const statsCards = computed(() => [
  {
    key: "studyTime",
    label: "总学习时长",
    value: analyticsStore.getFormattedStats.studyTime,
    icon: Clock,
    color: "text-blue-500",
    trend: 12, // 模拟趋势数据
  },
  {
    key: "homework",
    label: "完成作业",
    value: `${analyticsStore.learningStats?.completedHomework || 0}份`,
    icon: Document,
    color: "text-green-500",
    trend: 8,
  },
  {
    key: "score",
    label: "平均成绩",
    value: analyticsStore.getFormattedStats.averageScore,
    icon: TrendCharts,
    color: "text-yellow-500",
    trend: 5,
  },
  {
    key: "streak",
    label: "连续学习",
    value: analyticsStore.getFormattedStats.streak,
    icon: Flag,
    color: "text-purple-500",
    trend: 0,
  },
]);

// 初始化学习时长趋势图
const initStudyTimeChart = () => {
  if (!studyTimeChart.value) return;

  studyTimeChartInstance = echarts.init(studyTimeChart.value);

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
      },
      formatter: (params: any) => {
        const data = params[0];
        return `
          <div class="text-sm">
            <div class="font-medium">${data.axisValue}</div>
            <div class="text-blue-600">学习时长: ${data.value}分钟</div>
          </div>
        `;
      },
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: analyticsStore.learningProgress.map((p) =>
        dayjs(p.date).format("MM-DD"),
      ),
      axisLabel: {
        fontSize: 12,
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: "{value}min",
        fontSize: 12,
      },
    },
    series: [
      {
        name: "学习时长",
        type: "line",
        smooth: true,
        data: analyticsStore.learningProgress.map((p) => p.studyTime),
        itemStyle: {
          color: "#3b82f6",
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(59, 130, 246, 0.3)" },
              { offset: 1, color: "rgba(59, 130, 246, 0.1)" },
            ],
          },
        },
      },
    ],
  };

  studyTimeChartInstance.setOption(option);
};

// 初始化学科分布图
const initSubjectChart = () => {
  if (!subjectChart.value) return;

  subjectChartInstance = echarts.init(subjectChart.value);

  const data = analyticsStore.subjectStats.map((s) => ({
    name: s.subject,
    value: s.studyTime,
  }));

  const option = {
    tooltip: {
      trigger: "item",
      formatter: "{a} <br/>{b}: {c}min ({d}%)",
    },
    series: [
      {
        name: "学习时长",
        type: "pie",
        radius: "50%",
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.5)",
          },
        },
        label: {
          show: true,
          formatter: "{b}: {d}%",
        },
      },
    ],
  };

  subjectChartInstance.setOption(option);
};

// 初始化效率分析图
const initEfficiencyChart = () => {
  if (!efficiencyChart.value) return;

  efficiencyChartInstance = echarts.init(efficiencyChart.value);

  const option = {
    tooltip: {
      trigger: "axis",
    },
    legend: {
      data: ["学习时长", "有效时长"],
    },
    xAxis: {
      type: "category",
      data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: "{value}min",
      },
    },
    series: [
      {
        name: "学习时长",
        type: "bar",
        data: [120, 90, 150, 80, 130, 110, 95],
        itemStyle: {
          color: "#e5e7eb",
        },
      },
      {
        name: "有效时长",
        type: "bar",
        data: [100, 75, 120, 65, 110, 90, 80],
        itemStyle: {
          color: "#3b82f6",
        },
      },
    ],
  };

  efficiencyChartInstance.setOption(option);
};

// 初始化知识点掌握度图
const initKnowledgeChart = () => {
  if (!knowledgeChart.value) return;

  knowledgeChartInstance = echarts.init(knowledgeChart.value);

  const filteredPoints = selectedSubject.value
    ? analyticsStore.knowledgePoints.filter(
        (p) => p.subject === selectedSubject.value,
      )
    : analyticsStore.knowledgePoints.slice(0, 10);

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow",
      },
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    },
    xAxis: {
      type: "value",
      max: 100,
      axisLabel: {
        formatter: "{value}%",
      },
    },
    yAxis: {
      type: "category",
      data: filteredPoints.map((p) => p.name),
      axisLabel: {
        fontSize: 11,
      },
    },
    series: [
      {
        name: "掌握度",
        type: "bar",
        data: filteredPoints.map((p) => ({
          value: p.masteryLevel,
          itemStyle: {
            color:
              p.masteryLevel >= 80
                ? "#10b981"
                : p.masteryLevel >= 60
                  ? "#f59e0b"
                  : "#ef4444",
          },
        })),
      },
    ],
  };

  knowledgeChartInstance.setOption(option);
};

// 初始化热力图
const initHeatmapChart = () => {
  if (!heatmapChart.value) return;

  heatmapChartInstance = echarts.init(heatmapChart.value);

  // 生成模拟热力图数据
  const generateHeatmapData = () => {
    const data = [];
    const startDate = dayjs(`${selectedYear.value}-01-01`);
    const endDate = dayjs(`${selectedYear.value}-12-31`);

    let currentDate = startDate;
    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate)) {
      const value = Math.floor(Math.random() * 4); // 0-3的随机值
      data.push([currentDate.format("YYYY-MM-DD"), value]);
      currentDate = currentDate.add(1, "day");
    }
    return data;
  };

  const option = {
    tooltip: {
      formatter: (params: any) => {
        return `${params.data[0]}<br/>学习强度: ${params.data[1]}`;
      },
    },
    visualMap: {
      min: 0,
      max: 3,
      inRange: {
        color: ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"],
      },
      show: false,
    },
    calendar: {
      top: 20,
      left: 20,
      right: 20,
      bottom: 20,
      range: selectedYear.value,
      itemStyle: {
        borderWidth: 1,
        borderColor: "#fff",
      },
      yearLabel: { show: false },
      monthLabel: {
        nameMap: "cn",
        fontSize: 12,
      },
      dayLabel: {
        nameMap: "cn",
        fontSize: 10,
      },
    },
    series: [
      {
        type: "heatmap",
        coordinateSystem: "calendar",
        data: generateHeatmapData(),
      },
    ],
  };

  heatmapChartInstance.setOption(option);
};

// 响应式处理
const handleResize = () => {
  studyTimeChartInstance?.resize();
  subjectChartInstance?.resize();
  efficiencyChartInstance?.resize();
  knowledgeChartInstance?.resize();
  heatmapChartInstance?.resize();
};

// 事件处理
const handleTimeRangeChange = () => {
  analyticsStore.fetchLearningStats(timeRange.value);
  analyticsStore.fetchLearningProgress(
    dayjs().subtract(parseInt(timeRange.value), "day").format("YYYY-MM-DD"),
    dayjs().format("YYYY-MM-DD"),
  );
};

const handleSubjectChange = () => {
  analyticsStore.fetchKnowledgePoints(selectedSubject.value || undefined);
};

const handleYearChange = () => {
  analyticsStore.fetchStudyHeatmap(selectedYear.value);
};

// 初始化所有图表
const initAllCharts = () => {
  setTimeout(() => {
    initStudyTimeChart();
    initSubjectChart();
    initEfficiencyChart();
    initKnowledgeChart();
    initHeatmapChart();
  }, 100);
};

// 监听数据变化
watch(
  () => analyticsStore.learningProgress,
  () => {
    if (studyTimeChartInstance) {
      initStudyTimeChart();
    }
  },
  { deep: true },
);

watch(
  () => analyticsStore.subjectStats,
  () => {
    if (subjectChartInstance) {
      initSubjectChart();
    }
  },
  { deep: true },
);

watch(
  () => analyticsStore.knowledgePoints,
  () => {
    if (knowledgeChartInstance) {
      initKnowledgeChart();
    }
  },
  { deep: true },
);

onMounted(() => {
  initAllCharts();
  window.addEventListener("resize", handleResize);

  // 初始化数据
  analyticsStore.initializeDashboard(timeRange.value);

  // 自动刷新
  if (props.autoRefresh) {
    const interval = setInterval(() => {
      analyticsStore.refreshAllData();
    }, 60000); // 每分钟刷新

    onUnmounted(() => {
      clearInterval(interval);
    });
  }
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  studyTimeChartInstance?.dispose();
  subjectChartInstance?.dispose();
  efficiencyChartInstance?.dispose();
  knowledgeChartInstance?.dispose();
  heatmapChartInstance?.dispose();
});
</script>

<style scoped>
.learning-stats-chart {
  @apply w-full;
}

.learning-stats-chart :deep(.el-select) {
  min-width: 120px;
}

.learning-stats-chart :deep(.el-card__body) {
  @apply p-0;
}
</style>
