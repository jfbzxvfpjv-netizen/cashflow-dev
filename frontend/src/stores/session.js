import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import sessionService from '@/services/sessionService'

export const useSessionStore = defineStore('session', () => {
  const activeSession = ref(null)
  const loading = ref(false)
  const hasActiveSession = computed(() => activeSession.value !== null)
  const sessionId = computed(() => activeSession.value?.id ?? null)
  const sessionDelegacion = computed(() => activeSession.value?.delegacion ?? null)

  async function fetchActive() {
    loading.value = true
    try { const { data } = await sessionService.getActive(); activeSession.value = data }
    catch { activeSession.value = null }
    finally { loading.value = false }
  }
  async function openSession(p) { const { data } = await sessionService.open(p); activeSession.value = data; return data }
  async function closeSession(notes = '') { if (!activeSession.value) return; const { data } = await sessionService.close(activeSession.value.id, { notes }); activeSession.value = null; return data }
  function clear() { activeSession.value = null }

  return { activeSession, loading, hasActiveSession, sessionId, sessionDelegacion, fetchActive, openSession, closeSession, clear }
})
