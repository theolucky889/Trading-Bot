<template>
    <div
      class="flex flex-col items-center justify-center rounded-2xl p-6 shadow-lg ring-1 ring-gray-700/40 bg-gray-900 hover:scale-[1.02] transition-transform duration-200 ease-out"
    >
      <i :class="[icon, textColor, 'text-2xl mb-2']" />
      <h3 class="font-semibold text-sm tracking-wide text-gray-400">{{ label }}</h3>
      <p class="text-2xl font-extrabold mt-1">{{ formattedValue }}</p>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const props = defineProps({
    label: { type: String, required: true },
    value: { type: [Number, String], required: true },
    icon: { type: String, default: 'fas fa-dollar-sign' },
    /** Tailwind color\, e.g. 'text-indigo-400' */
    textColor: { type: String, default: 'text-indigo-400' },
    currency: { type: String, default: '$' }
  })
  
  const formattedValue = computed(() => {
    if (typeof props.value === 'number') {
      return props.currency + props.value.toLocaleString()
    }
    return props.value
  })
  </script>
  