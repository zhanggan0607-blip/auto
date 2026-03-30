<template>
  <div class="stat-cards-wrapper">
    <el-row :gutter="gutter" class="stat-cards" justify="space-between">
      <el-col
        v-for="(stat, index) in stats"
        :key="index"
        class="stat-col"
        :style="{ animationDelay: `${index * 0.1}s` }"
      >
        <StatCard
          :value="stat.value"
          :label="stat.label"
          :type="stat.type || 'default'"
          :icon="stat.icon"
          :suffix="stat.suffix"
          :prefix="stat.prefix"
          :decimals="stat.decimals"
          :trend="stat.trend"
          :clickable="stat.clickable"
          @click="emit('cardClick', stat)"
        >
          <template v-if="stat.customIcon" #icon>
            <slot :name="`icon-${index}`" />
          </template>
        </StatCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import StatCard from './StatCard.vue'

defineProps({
  stats: {
    type: Array,
    required: true,
    default: () => []
  },
  gutter: {
    type: Number,
    default: 16
  }
})

const emit = defineEmits(['cardClick'])
</script>

<style scoped lang="scss">
.stat-cards-wrapper {
  width: 100%;
  overflow-x: auto;
}

.stat-cards {
  display: flex;
  flex-wrap: nowrap;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);

  &::-webkit-scrollbar {
    display: none;
  }
}

.stat-col {
  flex: 1;
  min-width: 160px;
  max-width: 280px;
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;

  &:last-child {
    flex: 0 0 auto;
  }
}

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

@media (max-width: 768px) {
  .stat-cards {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .stat-col {
    min-width: calc(50% - var(--spacing-md));
    max-width: calc(50% - var(--spacing-md));
  }
}
</style>
