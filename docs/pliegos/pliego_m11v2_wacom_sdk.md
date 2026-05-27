# Pliego M11-v2 — Refactor WacomCaptureBox con Wacom Ink SDK for Signature JS

> **Estado**: bloqueado por recurso externo (descarga SDK)
> **Sesión estimada**: 2-3 h una vez se tenga el SDK descargado
> **Fecha redacción**: 27/05/2026

---

## 1. Contexto: por qué se invalidó el diseño original

El diseño M11 firmado el 18/04/2026 asumía que el Wacom se comportaría como un dispositivo de puntero estándar y que `pointerdown`/`pointermove` recogerían los datos. La realidad con el hardware real **Wacom STU-430** (signature pad LCD que tenemos en oficina) es distinta:

- El STU-430 **NO expone puntero al sistema operativo**. El SO no lo ve como un dispositivo HID estándar de pointing.
- La pantalla LCD del dispositivo necesita recibir comandos del PC para mostrar lo que el firmante dibuja en su pantalla.
- La presión del stylus se entrega como datos brutos por canal HID privado.

Por tanto, el componente `WacomCaptureBox.vue` actual (202 líneas, canvas + eventos mouse/touch del navegador) **no captura firma alguna** cuando el firmante usa el Wacom: el navegador no recibe los eventos.

## 2. Decisión final (27/05/2026)

Usar el **Wacom Ink SDK for Signature — JavaScript edition**, disponible en `developer.wacom.com`:

- Plan **Lite (gratuito)** + **Evaluation License** renovable cada 3 meses
- Tecnología: **WebHID API** (soportada únicamente en Chrome y Edge)
- Restricción operativa: solo accesible desde los **2 PCs corporativos** donde está instalado Chrome/Edge actualizado y donde físicamente está conectado el STU-430

Sigue valiendo el resto del diseño M11:

- Empleados con huella ya enrolada (Pedro Lopez Requena y Yudisleidy Nunez Lavastida en dev, pendiente enrolar en prod) → fingerprint U.are.U
- Personal externo (proveedores, clientes, contrapartes puntuales) → STU-430 vía SDK
- Empleados sin huella enrolada en periodo de implantación → fallback a STU-430 con marca "firma provisional"
- El sistema sigue deduciendo el mecanismo sin pregunta al usuario

## 3. Prerequisitos antes de la sesión de ejecución

A completar offline antes de empezar:

1. Registrarse en `https://developer.wacom.com` (cuenta gratuita)
2. Solicitar y aceptar la **Evaluation License** del SDK Lite for Signature, edición JavaScript
3. Descargar el ZIP del SDK (suele incluir `wacom-stu-sdk.js`, samples y documentación)
4. Tener disponibles las **API keys** de la licencia eval (suele ser un par de strings: license key + license token)
5. Hardware: STU-430 conectado por USB a un PC corporativo con Chrome o Edge actualizado
6. Verificar que el navegador del PC soporta WebHID (`chrome://device-log` debería listar el STU cuando se enchufa)

## 4. Plan de ejecución (orden estricto)

### Fase A — Preparación (15 min)

1. Crear carpeta `frontend/public/vendor/wacom/` y descomprimir ahí el SDK
2. Añadir las API keys al `.env` del frontend como `VITE_WACOM_LICENSE_KEY` y `VITE_WACOM_LICENSE_TOKEN`, con sus equivalentes en `.env.example`
3. Verificar que el archivo `wacom-stu-sdk.js` se puede cargar dinámicamente desde Vue

### Fase B — Refactor WacomCaptureBox (60-90 min)

Sustituir el contenido entero del componente actual (202 líneas, canvas + eventos del navegador) por una implementación basada en SDK. Mantener intacto el **contrato de emit** para no romper el resto del flujo de firmas:

- Emit `signed` con payload `{ dataUrl: string }` (mismo formato actual)
- Emit `reset` cuando el firmante borra
- Props: igual al actual (`canvasWidth`, `canvasHeight`, etc.)

Lógica interna nueva:

- `onMounted`: pedir permiso WebHID al usuario (botón "Conectar Wacom"), inicializar SDK con las API keys, abrir sesión con el dispositivo
- Listener del stream del SDK: dibujar los trazos en un `<canvas>` propio del componente (lo que el firmante ve en pantalla del PC, en paralelo con lo que ve en el LCD del STU)
- Botón "Listo" del firmante: capturar el PNG del canvas (`toDataURL`) y emit `signed`
- Botón "Borrar": resetear stream + canvas + emit `reset`
- `onBeforeUnmount`: cerrar sesión con el SDK, liberar el dispositivo

### Fase C — Detección de dispositivo (15-30 min)

Refinar `useSignatureMethod.js` para que la deducción automática del método siga funcionando:

- Si el navegador soporta WebHID **y** hay un STU-430 conectado y emparejado → habilitar Wacom como opción
- Si no, ocultar el botón Wacom del UI y forzar otro método (huella si aplica, o degradación marcada)
- Mostrar un indicador discreto del estado del dispositivo (conectado / no detectado)

### Fase D — Validación E2E (30-45 min)

1. Conectar STU-430 al PC corporativo
2. Iniciar sesión como gestor en `/transactions/new`, elegir contraparte tipo externa (que dispara Wacom)
3. Verificar que aparece el botón "Conectar Wacom" la primera vez (solicitud de permiso WebHID)
4. Firmar en el dispositivo físico → comprobar que aparece la firma en el canvas del navegador
5. Pulsar "Listo" → la transacción se registra con la firma adjunta
6. Repetir con personal externo y con un empleado sin huella enrolada (caso "firma provisional")
7. Probar también desde el PC que NO tiene el STU conectado: el botón Wacom no debe aparecer (degradación grácil)

### Fase E — Cierre (10 min)

- Eliminar el archivo `WacomCaptureBox.vue` antiguo (queda en historial git)
- Commit dev con tag descriptivo
- Replicar a producción cuando esté validado en los 2 PCs corporativos
- Actualizar memoria del proyecto y este pliego con resultado real

## 5. Riesgos conocidos

- **Compatibilidad WebHID**: si Edge corporativo es muy antiguo o tiene políticas que bloquean WebHID, hay que actualizarlo o gestionar excepción con IT. Verificar antes de empezar.
- **Eval License caducada**: la licencia caduca a los 3 meses. Calendario manual para renovar o solicitar Lite extendida.
- **Datos del stream**: el SDK suele entregar coordenadas + presión a alta frecuencia; hay que ratear o filtrar antes de dibujar para no saturar el canvas.
- **PNG generado pesado**: dimensiones grandes producen blobs grandes para la BD. Validar tamaño tras primer test y ajustar `canvasWidth/canvasHeight` si hace falta.

## 6. Fuera del alcance de esta sesión

- Wacom para empleados con huella enrolada (ya funciona con U.are.U, no se toca)
- Sustitución del Wacom por otro modelo (decisión cerrada: STU-430 es el oficial)
- Firma desde el móvil (no se contempla en M11)

## 7. Estado de partida para la próxima sesión

- `frontend/src/components/admin/WacomCaptureBox.vue` (202 líneas, canvas + eventos navegador, **inservible con STU-430**)
- `frontend/src/components/admin/SignatureSection.vue` (orquestador, **no requiere cambios** salvo ajuste menor de detección)
- `frontend/src/composables/useSignatureMethod.js` (lógica deducción método, **requiere refinamiento** según Fase C)

Comandos útiles para arrancar la sesión rápido:

```bash
cd ~/cashflow-dev
git status
grep -nE "pointerdown|pointermove|PointerEvent|HID|emit\(" frontend/src/components/admin/WacomCaptureBox.vue
```

