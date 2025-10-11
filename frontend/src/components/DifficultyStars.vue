<template>
  <div class="difficulty-stars">
    <el-icon 
      v-for="i in 5" 
      :key="i" 
      :class="starClass(i)"
      class="star-icon"
    >
      <StarFilled />
    </el-icon>
    <span class="difficulty-text">{{ difficultyText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { StarFilled } from '@element-plus/icons-vue'

interface Props {
  level: number
  showText?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showText: true
})

const starClass = (index: number) => {
  return index <= props.level ? 'star-filled' : 'star-empty'
}

const difficultyText = computed(() => {
  if (!props.showText) return ''
  
  const texts = {
    1: '很简单',
    2: '简单',
    3: '中等',
    4: '困难',
    5: '很困难'
  }
  return texts[props.level as keyof typeof texts] || '未知'
})
</script>

<style scoped>
.difficulty-stars {
  display: flex;
  align-items: center;
  gap: 2px;
}

.star-icon {
  font-size: 14px;
  transition: color 0.3s;
}

.star-filled {
  color: #ffd04b;
}

.star-empty {
  color: #e4e7ed;
}

.difficulty-text {
  margin-left: 4px;
  font-size: 12px;
  color: #909399;
}
</style>