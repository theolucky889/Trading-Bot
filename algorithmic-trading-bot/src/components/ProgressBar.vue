<template>
    <div class="w-full">
      <h3 class="text-sm font-semibold mb-1 text-gray-400">
        {{ label }}:
        <span class="text-gray-300 font-medium">{{ formattedValue }}</span>
      </h3>
  
      <div class="h-3 w-full bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full transition-all duration-300"
          :class="barColor"
          :style="{ width: clampedPercent + '%' }"
        ></div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const props = defineProps({
    /** Label displayed to the left of the bar */
    label: { type: String, required: true },
    /** Percentage as 0‑100 (numbers outside the range get clamped) */
    percent: { type: Number, required: true },
    /** Optional raw numeric value to display instead of the % */
    value: { type: [Number, String], default: null },
    /** Prepend this for numeric `value` (e.g. $) */
    currency: { type: String, default: '$' },
    /** Tailwind background‑color class for the fill */
    barColor: { type: String, default: 'bg-green-500' }
  })
  
  const clampedPercent = computed(() => Math.max(0, Math.min(100, props.percent)))
  
  const formattedValue = computed(() => {
    if (props.value !== null) {
      if (typeof props.value === 'number') return props.currency + props.value.toLocaleString()
      return props.value
    }
    return clampedPercent.value + '%'
  })
  </script>
  