<template>
  <div class="home-page">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            <span class="gradient-text">五好伴学</span>
            <br />
            智能学习助手
          </h1>
          <p class="hero-subtitle">
            基于AI技术的智能学习管理平台
            <br />
            让学习更高效，让进步更明显
          </p>
          <div class="hero-actions">
            <el-button
              type="primary"
              size="large"
              @click="router.push('/homework')"
              class="action-button primary-button"
            >
              <el-icon class="mr-2">
                <Upload />
              </el-icon>
              开始批改作业
            </el-button>
            <el-button
              size="large"
              @click="router.push('/learning')"
              class="action-button secondary-button"
            >
              <el-icon class="mr-2">
                <ChatDotSquare />
              </el-icon>
              智能问答
            </el-button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="floating-card">
            <el-icon class="card-icon">
              <Document />
            </el-icon>
            <span class="card-text">作业批改</span>
          </div>
          <div class="floating-card card-delay-1">
            <el-icon class="card-icon">
              <ChatDotSquare />
            </el-icon>
            <span class="card-text">学习问答</span>
          </div>
          <div class="floating-card card-delay-2">
            <el-icon class="card-icon">
              <TrendCharts />
            </el-icon>
            <span class="card-text">学习进度</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特色 -->
    <section class="features-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">核心功能</h2>
          <p class="section-subtitle">全面的学习辅助工具，助力学习成长</p>
        </div>

        <div class="features-grid">
          <div
            v-for="feature in features"
            :key="feature.id"
            class="feature-card"
            @click="router.push(feature.path)"
          >
            <div class="feature-icon">
              <el-icon :size="40">
                <component :is="feature.icon" />
              </el-icon>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>
            <div class="feature-stats">
              <span class="stat-item">
                <el-icon class="stat-icon">
                  <Check />
                </el-icon>
                {{ feature.stat }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 使用步骤 -->
    <section class="steps-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">简单三步，开启智能学习</h2>
          <p class="section-subtitle">操作简单，效果显著</p>
        </div>

        <div class="steps-container">
          <div v-for="(step, index) in steps" :key="step.id" class="step-item">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-icon">
                <el-icon :size="32">
                  <component :is="step.icon" />
                </el-icon>
              </div>
              <h4 class="step-title">{{ step.title }}</h4>
              <p class="step-description">{{ step.description }}</p>
            </div>
            <div v-if="index < steps.length - 1" class="step-arrow">
              <el-icon>
                <ArrowRight />
              </el-icon>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据展示 -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div v-for="stat in stats" :key="stat.id" class="stat-card">
            <div class="stat-number">{{ stat.number }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 开始使用 -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-content">
          <h2 class="cta-title">准备好开始学习之旅了吗？</h2>
          <p class="cta-subtitle">加入千万学生的选择，让AI成为你的学习伙伴</p>
          <div class="cta-actions">
            <el-button
              type="primary"
              size="large"
              @click="router.push('/dashboard')"
              class="cta-button"
            >
              立即开始
              <el-icon class="ml-2">
                <ArrowRight />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import {
  Upload,
  ChatDotSquare,
  Document,
  TrendCharts,
  Check,
  ArrowRight,
} from "@element-plus/icons-vue";

const router = useRouter();

// 功能特色数据
const features = ref([
  {
    id: 1,
    title: "智能作业批改",
    description: "AI快速识别并批改各科作业，提供详细解析和建议",
    icon: "Document",
    path: "/homework",
    stat: "准确率98%+",
  },
  {
    id: 2,
    title: "学习问答助手",
    description: "24小时在线AI助手，解答学习疑问，提供个性化指导",
    icon: "ChatRound",
    path: "/learning",
    stat: "响应时间<3s",
  },
  {
    id: 3,
    title: "学情数据分析",
    description: "科学分析学习数据，提供专业的学习报告和改进建议",
    icon: "DataAnalysis",
    path: "/analytics",
    stat: "多维度分析",
  },
]);

// 使用步骤数据
const steps = ref([
  {
    id: 1,
    title: "上传作业",
    description: "拍照或上传作业图片",
    icon: "Upload",
  },
  {
    id: 2,
    title: "AI智能分析",
    description: "AI快速识别并分析作业内容",
    icon: "TrendCharts",
  },
  {
    id: 3,
    title: "获得反馈",
    description: "收到详细的批改结果和学习建议",
    icon: "ChatDotSquare",
  },
]);

// 统计数据
const stats = ref([
  {
    id: 1,
    number: "1000万+",
    label: "服务学生数",
  },
  {
    id: 2,
    number: "500万+",
    label: "批改作业数",
  },
  {
    id: 3,
    number: "98%",
    label: "识别准确率",
  },
  {
    id: 4,
    number: "24/7",
    label: "在线服务",
  },
]);
</script>

<style scoped lang="scss">
.home-page {
  min-height: 100vh;
  overflow-x: hidden;
}

// 英雄区域
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(1px);
  }
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 2rem;
    text-align: center;
  }
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 1.5rem;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
}

.gradient-text {
  background: linear-gradient(45deg, #ffd700, #ffeb3b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  line-height: 1.6;
  margin-bottom: 2rem;
  opacity: 0.9;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
}

.hero-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    justify-content: center;
  }
}

.action-button {
  padding: 0.75rem 2rem;
  font-size: 1.1rem;
  border-radius: 50px;
  transition: all 0.3s ease;

  &.primary-button {
    background: linear-gradient(45deg, #ffd700, #ffeb3b);
    border: none;
    color: #333;
    font-weight: 600;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3);
    }
  }

  &.secondary-button {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;

    &:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: translateY(-2px);
    }
  }
}

// 浮动卡片
.hero-visual {
  position: relative;
  height: 400px;
}

.floating-card {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  animation: float 3s ease-in-out infinite;

  &:nth-child(1) {
    top: 10%;
    left: 20%;
    animation-delay: 0s;
  }

  &:nth-child(2) {
    top: 40%;
    right: 10%;
    animation-delay: 1s;
  }

  &:nth-child(3) {
    bottom: 20%;
    left: 10%;
    animation-delay: 2s;
  }

  .card-icon {
    font-size: 2rem;
    color: #ffd700;
  }

  .card-text {
    font-weight: 500;
    white-space: nowrap;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

// 通用容器
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

// 节标题
.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 1rem;

  @media (max-width: 768px) {
    font-size: 2rem;
  }
}

.section-subtitle {
  font-size: 1.1rem;
  color: #666;
  max-width: 600px;
  margin: 0 auto;
}

// 功能特色
.features-section {
  padding: 5rem 0;
  background: #f8fafc;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  }
}

.feature-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  color: white;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
}

.feature-description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.feature-stats {
  .stat-item {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: #10b981;
    font-weight: 500;

    .stat-icon {
      color: #10b981;
    }
  }
}

// 使用步骤
.steps-section {
  padding: 5rem 0;
  background: white;
}

.steps-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.step-item {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex: 1;

  @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
}

.step-number {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-content {
  .step-icon {
    color: #667eea;
    margin-bottom: 1rem;
  }

  .step-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
  }

  .step-description {
    color: #666;
    line-height: 1.5;
  }
}

.step-arrow {
  color: #667eea;
  font-size: 2rem;

  @media (max-width: 768px) {
    transform: rotate(90deg);
  }
}

// 数据展示
.stats-section {
  padding: 3rem 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.stat-card {
  text-align: center;
  padding: 1rem;

  .stat-number {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(45deg, #ffd700, #ffeb3b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .stat-label {
    font-size: 1rem;
    opacity: 0.9;
  }
}

// CTA区域
.cta-section {
  padding: 5rem 0;
  background: #f8fafc;
}

.cta-content {
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.cta-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 1rem;

  @media (max-width: 768px) {
    font-size: 2rem;
  }
}

.cta-subtitle {
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.cta-button {
  padding: 1rem 3rem;
  font-size: 1.1rem;
  border-radius: 50px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
  }
}
</style>
