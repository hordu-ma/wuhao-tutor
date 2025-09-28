<template>
  <div class="learning-page">
    <ChatInterface />
  </div>
</template>

<script setup lang="ts">
import ChatInterface from "@/components/ChatInterface.vue";

// 页面元信息
defineOptions({
  name: "LearningPage",
});
</script>

<style scoped lang="scss">
.learning-page {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
