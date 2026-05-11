// ============================================================================
// Shim para satisfacer el `import 'WebSdk'` del paquete @digitalpersona/devices.
// ============================================================================
// El paquete hace internamente `import 'WebSdk'` como side-effect (sin nombres
// destructurados) y luego accede a WebSdk.WebChannelClient como variable
// global en runtime. La WebSdk real se carga via <script src="/websdk/index.js">
// en index.html y queda en window.WebSdk.
//
// Este archivo existe solo para que Rollup resuelva el import durante el build.
// No exporta ni hace nada en runtime.
// ============================================================================

export {}
