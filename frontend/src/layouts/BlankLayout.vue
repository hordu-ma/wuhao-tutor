<template>
  <div class="blank-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
/**
 * 空白布局组件
 * 用于登录页、错误页等不需要导航的页面
 */
</script>

<style lang="scss" scoped>
.blank-layout {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
    opacity: 0.3;
    pointer-events: none;
  }
}

@media (max-width: 768px) {
  .blank-layout {
    padding: 20px;
  }
}
</style>
