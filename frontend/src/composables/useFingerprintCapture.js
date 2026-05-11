import { ref, onUnmounted } from 'vue'
import { FingerprintReader, SampleFormat } from '@digitalpersona/devices'
import api from '@/services/api'

/**
 * Composable de captura de huella dactilar via @digitalpersona/devices.
 *
 * Estado reactivo:
 *   - state: 'idle' | 'connecting' | 'connected' | 'capturing'
 *            | 'sample_received' | 'error' | 'disconnected'
 *   - lastSample (string base64 PNG)
 *   - lastQuality (number 0-100 del backend SourceAFIS)
 *   - lastMinutiae (number, conteo de minutiae del backend)
 *   - error (string | null)
 *   - deviceConnected (boolean)
 *
 * Acciones: connect(), startCapture(), stopCapture(), disconnect(), simulateSample(b64).
 *
 * Tras cada SamplesAcquired (o simulateSample) llama automaticamente a
 * /fingerprints/quality y publica lastQuality + lastMinutiae.
 *
 * No implementa reconexion automatica del lector. Si se desconecta a mitad
 * de flujo, transiciona a 'disconnected' con error='reader_disconnected'
 * y el consumidor decide si reintenta llamando connect() de nuevo.
 */
export function useFingerprintCapture(config = {}) {
  const {
    timeoutMs = 30000,
    quality_min_enroll = 60,
    quality_min_verify = 40,
    autoQualityCheck = true,
  } = config

  // ── Estado reactivo ──────────────────────────────────────

  const state = ref('idle')
  const lastSample = ref(null)
  const lastQuality = ref(null)
  const lastMinutiae = ref(null)
  const error = ref(null)
  const deviceConnected = ref(false)

  // ── Internos ─────────────────────────────────────────────

  let reader = null
  let captureTimeout = null

  // ── Acciones publicas ────────────────────────────────────

  async function connect() {
    if (!['idle', 'disconnected', 'error'].includes(state.value)) {
      console.warn('[useFingerprintCapture] connect() ignorado en estado', state.value)
      return
    }
    if (typeof window === 'undefined' || typeof window.WebSdk === 'undefined') {
      state.value = 'error'
      error.value = 'WebSdk global no disponible. Verifica /websdk/index.js en index.html.'
      return
    }

    state.value = 'connecting'
    error.value = null
    lastSample.value = null
    lastQuality.value = null
    lastMinutiae.value = null

    try {
      reader = new FingerprintReader()
      reader.on('DeviceConnected', onDeviceConnected)
      reader.on('DeviceDisconnected', onDeviceDisconnected)
      reader.on('SamplesAcquired', onSamplesAcquired)
      reader.on('AcquisitionStarted', onAcquisitionStarted)
      reader.on('AcquisitionStopped', onAcquisitionStopped)
      reader.on('ErrorOccurred', onErrorOccurred)
      reader.on('QualityReported', onQualityReported)

      const devices = await reader.enumerateDevices()
      deviceConnected.value = Array.isArray(devices) && devices.length > 0
      state.value = 'connected'
    } catch (err) {
      state.value = 'error'
      error.value = `No se pudo conectar con el agente local: ${err.message || err}`
      console.error('[useFingerprintCapture] connect error:', err)
    }
  }

  async function startCapture() {
    if (state.value !== 'connected') {
      error.value = `No se puede iniciar captura en estado '${state.value}'`
      return
    }
    if (!deviceConnected.value) {
      error.value = 'No hay lector conectado al agente'
      return
    }

    error.value = null
    try {
      await reader.startAcquisition(SampleFormat.PngImage)
      captureTimeout = setTimeout(() => {
        if (state.value === 'capturing') {
          stopCapture()
          error.value = `Timeout de captura tras ${timeoutMs} ms`
        }
      }, timeoutMs)
    } catch (err) {
      state.value = 'error'
      error.value = `Error al iniciar captura: ${err.message || err}`
      console.error('[useFingerprintCapture] startCapture error:', err)
    }
  }

  async function stopCapture() {
    if (captureTimeout) {
      clearTimeout(captureTimeout)
      captureTimeout = null
    }
    if (!reader) return
    try {
      await reader.stopAcquisition()
    } catch (err) {
      console.warn('[useFingerprintCapture] stopCapture warning:', err)
    }
  }

  async function disconnect() {
    if (captureTimeout) {
      clearTimeout(captureTimeout)
      captureTimeout = null
    }
    if (reader) {
      try {
        await reader.off()
      } catch (err) {
        console.warn('[useFingerprintCapture] off warning:', err)
      }
      reader = null
    }
    state.value = 'disconnected'
    deviceConnected.value = false
  }

  /**
   * Inyecta una muestra simulada sin pasar por el lector.
   * Util para probar la logica del composable sin hardware real.
   */
  async function simulateSample(b64) {
    if (!b64 || typeof b64 !== 'string') {
      error.value = 'simulateSample requiere un string base64'
      return
    }
    state.value = 'capturing'
    await processSample(b64)
  }

  // ── Handlers de eventos del lector ───────────────────────

  function onDeviceConnected(e) {
    console.log('[useFingerprintCapture] DeviceConnected', e)
    deviceConnected.value = true
  }

  function onDeviceDisconnected(e) {
    console.log('[useFingerprintCapture] DeviceDisconnected', e)
    deviceConnected.value = false
    state.value = 'disconnected'
    error.value = 'reader_disconnected'
  }

  function onAcquisitionStarted(e) {
    console.log('[useFingerprintCapture] AcquisitionStarted', e)
    state.value = 'capturing'
  }

  function onAcquisitionStopped(e) {
    console.log('[useFingerprintCapture] AcquisitionStopped', e)
    if (state.value === 'capturing') {
      state.value = 'connected'
    }
  }

  function onSamplesAcquired(e) {
    console.log('[useFingerprintCapture] SamplesAcquired', e)
    if (captureTimeout) {
      clearTimeout(captureTimeout)
      captureTimeout = null
    }

    let samples
    try {
      samples = typeof e.samples === 'string' ? JSON.parse(e.samples) : e.samples
    } catch (err) {
      console.error('[useFingerprintCapture] Error parsing samples:', err)
      state.value = 'error'
      error.value = 'Formato de muestra invalido'
      return
    }

    if (!samples || samples.length === 0) {
      state.value = 'error'
      error.value = 'Muestra vacia recibida del lector'
      return
    }

    const b64 = samples[0]
    processSample(b64)
  }

  function onQualityReported(e) {
    console.log('[useFingerprintCapture] QualityReported', e)
    // Calidad rapida del lector. La definitiva viene del backend /quality.
  }

  function onErrorOccurred(e) {
    console.error('[useFingerprintCapture] ErrorOccurred', e)
    state.value = 'error'
    error.value = e?.error || e?.message || 'Error reportado por el lector'
  }

  async function processSample(b64) {
    lastSample.value = b64
    state.value = 'sample_received'

    if (autoQualityCheck) {
      try {
        const { data } = await api.post('/fingerprints/quality', {
          image_b64: b64,
          image_format: 'png',
        })
        lastQuality.value = data.quality_score ?? null
        lastMinutiae.value = data.minutiae_count ?? null
      } catch (err) {
        console.warn('[useFingerprintCapture] /quality error:', err)
        lastQuality.value = null
        lastMinutiae.value = null
      }
    }
  }

  // ── Cleanup automatico al desmontar el consumidor ────────

  onUnmounted(() => {
    disconnect()
  })

  // ── API publica ──────────────────────────────────────────

  return {
    state,
    lastSample,
    lastQuality,
    lastMinutiae,
    error,
    deviceConnected,
    connect,
    startCapture,
    stopCapture,
    disconnect,
    simulateSample,
    config: { timeoutMs, quality_min_enroll, quality_min_verify, autoQualityCheck },
  }
}
