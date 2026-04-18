<template>
  <div>
    <router-view v-if="isPublicRoute" />
    <AppLayout v-else />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
const route = useRoute()
const isPublicRoute = computed(() => route.meta.requiresAuth === false)
</script>
