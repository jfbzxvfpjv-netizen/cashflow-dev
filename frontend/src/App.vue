<template>
  <div>
    <router-view v-if="isPublicRoute" />
    <AppLayout v-else />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'
const route = useRoute(); const auth = useAuthStore()
const isPublicRoute = computed(() => route.meta.requiresAuth === false)
onMounted(async () => { if (auth.token) await auth.verifyToken() })
</script>
