// ============================================================
//  htmx-config.js — Configuración global de HTMX
// ============================================================

// Tiempo extra antes de ocultar el indicador para evitar parpadeos.
if (window.htmx) {
  htmx.config.defaultSwapStyle = 'innerHTML';
  htmx.config.includeIndicatorStyles = false;
}

// Manejo de errores de respuesta HTMX (4xx/5xx): muestra un aviso simple.
document.addEventListener('htmx:responseError', function (evt) {
  console.error('Error HTMX:', evt.detail.xhr.status, evt.detail.xhr.responseURL);
});

// Errores de red/timeout.
document.addEventListener('htmx:sendError', function () {
  console.error('Error de red en la solicitud HTMX.');
});
