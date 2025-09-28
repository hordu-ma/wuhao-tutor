<template>
  <div class="loading-spinner" :class="containerClass">
    <div v-if="type === 'spinner'" class="spinner" :class="spinnerClass">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>

    <div v-else-if="type === 'dots'" class="dots-spinner" :class="spinnerClass">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>

    <div
      v-else-if="type === 'pulse'"
      class="pulse-spinner"
      :class="spinnerClass"
    >
      <div class="pulse-ring"></div>
    </div>

    <div v-else-if="type === 'bars'" class="bars-spinner" :class="spinnerClass">
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
    </div>

    <div v-else-if="type === 'skeleton'" class="skeleton-loader">
      <div
        class="skeleton-line"
        v-for="line in skeletonLines"
        :key="line"
      ></div>
    </div>

    <div
      v-if="text && type !== 'skeleton'"
      class="loading-text"
      :class="textClass"
    >
      {{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  type?: "spinner" | "dots" | "pulse" | "bars" | "skeleton";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  color?: "primary" | "secondary" | "success" | "warning" | "danger" | "white";
  text?: string;
  overlay?: boolean;
  fullscreen?: boolean;
  skeletonLines?: number;
  centered?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: "spinner",
  size: "md",
  color: "primary",
  text: "",
  overlay: false,
  fullscreen: false,
  skeletonLines: 3,
  centered: true,
});

const containerClass = computed(() => [
  {
    "loading-overlay": props.overlay,
    "loading-fullscreen": props.fullscreen,
    "loading-centered": props.centered,
  },
]);

const spinnerClass = computed(() => [
  `spinner-${props.size}`,
  `spinner-${props.color}`,
]);

const textClass = computed(() => [`text-${props.size}`, `text-${props.color}`]);
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.loading-centered {
  width: 100%;
  height: 100%;
  min-height: 100px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.loading-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  z-index: 10000;
}

/* 旋转圆圈加载器 */
.spinner {
  position: relative;
  display: inline-block;
}

.spinner-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid transparent;
  animation: spinner-rotate 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
}

/* 尺寸变体 */
.spinner-xs {
  width: 16px;
  height: 16px;
}

.spinner-xs .spinner-ring {
  width: 16px;
  height: 16px;
}

.spinner-sm {
  width: 20px;
  height: 20px;
}

.spinner-sm .spinner-ring {
  width: 20px;
  height: 20px;
}

.spinner-md {
  width: 32px;
  height: 32px;
}

.spinner-md .spinner-ring {
  width: 32px;
  height: 32px;
}

.spinner-lg {
  width: 48px;
  height: 48px;
}

.spinner-lg .spinner-ring {
  width: 48px;
  height: 48px;
}

.spinner-xl {
  width: 64px;
  height: 64px;
}

.spinner-xl .spinner-ring {
  width: 64px;
  height: 64px;
}

/* 颜色变体 */
.spinner-primary .spinner-ring {
  border-top-color: #3b82f6;
  border-right-color: #3b82f6;
}

.spinner-secondary .spinner-ring {
  border-top-color: #6b7280;
  border-right-color: #6b7280;
}

.spinner-success .spinner-ring {
  border-top-color: #10b981;
  border-right-color: #10b981;
}

.spinner-warning .spinner-ring {
  border-top-color: #f59e0b;
  border-right-color: #f59e0b;
}

.spinner-danger .spinner-ring {
  border-top-color: #ef4444;
  border-right-color: #ef4444;
}

.spinner-white .spinner-ring {
  border-top-color: #ffffff;
  border-right-color: #ffffff;
}

/* 点状加载器 */
.dots-spinner {
  display: flex;
  gap: 0.25rem;
}

.dot {
  border-radius: 50%;
  animation: dots-bounce 1.4s ease-in-out infinite both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.spinner-xs .dot {
  width: 3px;
  height: 3px;
}

.spinner-sm .dot {
  width: 4px;
  height: 4px;
}

.spinner-md .dot {
  width: 6px;
  height: 6px;
}

.spinner-lg .dot {
  width: 8px;
  height: 8px;
}

.spinner-xl .dot {
  width: 10px;
  height: 10px;
}

.spinner-primary .dot {
  background-color: #3b82f6;
}

.spinner-secondary .dot {
  background-color: #6b7280;
}

.spinner-success .dot {
  background-color: #10b981;
}

.spinner-warning .dot {
  background-color: #f59e0b;
}

.spinner-danger .dot {
  background-color: #ef4444;
}

.spinner-white .dot {
  background-color: #ffffff;
}

/* 脉冲加载器 */
.pulse-spinner {
  position: relative;
}

.pulse-ring {
  border-radius: 50%;
  animation: pulse-scale 1s ease-in-out infinite;
}

.spinner-xs .pulse-ring {
  width: 16px;
  height: 16px;
}

.spinner-sm .pulse-ring {
  width: 20px;
  height: 20px;
}

.spinner-md .pulse-ring {
  width: 32px;
  height: 32px;
}

.spinner-lg .pulse-ring {
  width: 48px;
  height: 48px;
}

.spinner-xl .pulse-ring {
  width: 64px;
  height: 64px;
}

.spinner-primary .pulse-ring {
  background-color: #3b82f6;
}

.spinner-secondary .pulse-ring {
  background-color: #6b7280;
}

.spinner-success .pulse-ring {
  background-color: #10b981;
}

.spinner-warning .pulse-ring {
  background-color: #f59e0b;
}

.spinner-danger .pulse-ring {
  background-color: #ef4444;
}

.spinner-white .pulse-ring {
  background-color: #ffffff;
}

/* 柱状加载器 */
.bars-spinner {
  display: flex;
  gap: 0.125rem;
  align-items: flex-end;
}

.bar {
  border-radius: 1px;
  animation: bars-scale 1.2s ease-in-out infinite;
}

.bar:nth-child(1) {
  animation-delay: -1.1s;
}

.bar:nth-child(2) {
  animation-delay: -1s;
}

.bar:nth-child(3) {
  animation-delay: -0.9s;
}

.bar:nth-child(4) {
  animation-delay: -0.8s;
}

.bar:nth-child(5) {
  animation-delay: -0.7s;
}

.spinner-xs .bar {
  width: 2px;
  height: 12px;
}

.spinner-sm .bar {
  width: 2px;
  height: 16px;
}

.spinner-md .bar {
  width: 3px;
  height: 24px;
}

.spinner-lg .bar {
  width: 4px;
  height: 32px;
}

.spinner-xl .bar {
  width: 5px;
  height: 40px;
}

.spinner-primary .bar {
  background-color: #3b82f6;
}

.spinner-secondary .bar {
  background-color: #6b7280;
}

.spinner-success .bar {
  background-color: #10b981;
}

.spinner-warning .bar {
  background-color: #f59e0b;
}

.spinner-danger .bar {
  background-color: #ef4444;
}

.spinner-white .bar {
  background-color: #ffffff;
}

/* 骨架屏加载器 */
.skeleton-loader {
  width: 100%;
  padding: 1rem;
}

.skeleton-line {
  height: 1rem;
  margin-bottom: 0.75rem;
  border-radius: 0.25rem;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-line:nth-child(1) {
  width: 100%;
}

.skeleton-line:nth-child(2) {
  width: 85%;
}

.skeleton-line:nth-child(3) {
  width: 70%;
}

.skeleton-line:last-child {
  margin-bottom: 0;
}

/* 加载文本 */
.loading-text {
  font-weight: 500;
  text-align: center;
  margin-top: 0.5rem;
}

.text-xs {
  font-size: 0.75rem;
}

.text-sm {
  font-size: 0.875rem;
}

.text-md {
  font-size: 1rem;
}

.text-lg {
  font-size: 1.125rem;
}

.text-xl {
  font-size: 1.25rem;
}

.text-primary {
  color: #3b82f6;
}

.text-secondary {
  color: #6b7280;
}

.text-success {
  color: #10b981;
}

.text-warning {
  color: #f59e0b;
}

.text-danger {
  color: #ef4444;
}

.text-white {
  color: #ffffff;
}

/* 动画定义 */
@keyframes spinner-rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dots-bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes pulse-scale {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

@keyframes bars-scale {
  0%,
  40%,
  100% {
    transform: scaleY(0.4);
  }
  20% {
    transform: scaleY(1);
  }
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .loading-overlay,
  .loading-fullscreen {
    background: rgba(17, 24, 39, 0.9);
  }

  .skeleton-line {
    background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
    background-size: 200% 100%;
  }
}

/* 减少动画模式支持 */
@media (prefers-reduced-motion: reduce) {
  .spinner-ring,
  .dot,
  .pulse-ring,
  .bar,
  .skeleton-line {
    animation: none;
  }

  .spinner-ring {
    border-top-color: currentColor;
    border-right-color: currentColor;
  }
}
</style>
