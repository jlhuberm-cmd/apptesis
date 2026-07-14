// ============================================================
//  charts.js — Inicialización de gráficos Plotly.js (branding UTPL)
// ============================================================

const UTPL_COLORS = ['#003B71', '#F39C12', '#27AE60', '#E74C3C'];

function _baseConfig() {
  return { responsive: true, displayModeBar: false, locale: 'es' };
}

function _baseLayout(extra) {
  return Object.assign(
    {
      font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
      margin: { t: 30, r: 20, b: 50, l: 45 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    },
    extra || {}
  );
}

// Gráfico radar (4 vértices = 4 competencias).
function initRadarChart(elementId, labels, values, maxValue) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const data = [
    {
      type: 'scatterpolar',
      r: values.concat(values.length ? values[0] : 0),
      theta: labels.concat(labels.length ? labels[0] : ''),
      fill: 'toself',
      fillcolor: 'rgba(0, 59, 113, 0.25)',
      line: { color: '#003B71' },
      hovertemplate: '%{theta}: %{r:.2f}<extra></extra>',
    },
  ];
  const layout = _baseLayout({
    polar: { radialaxis: { visible: true, range: [0, maxValue || 4] } },
    showlegend: false,
  });
  Plotly.newPlot(el, data, layout, _baseConfig());
}

// Gráfico de barras (media por competencia).
function initBarChart(elementId, labels, values, colors, maxValue) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const data = [
    {
      type: 'bar',
      x: labels,
      y: values,
      marker: { color: colors || UTPL_COLORS },
      text: values.map((v) => v.toFixed(2)),
      textposition: 'auto',
      hovertemplate: '%{x}: %{y:.2f}<extra></extra>',
    },
  ];
  const layout = _baseLayout({
    yaxis: { range: [0, maxValue || 4], title: 'Media' },
    xaxis: { automargin: true },
  });
  Plotly.newPlot(el, data, layout, _baseConfig());
}

// Histograma de distribución de una competencia (con línea de la media).
function initDistributionChart(elementId, bins, freqs, meanLine, name) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const data = [
    {
      type: 'bar',
      x: bins,
      y: freqs,
      marker: { color: '#003B71' },
      hovertemplate: '%{x}: %{y}<extra></extra>',
    },
  ];
  const shapes = [];
  if (typeof meanLine === 'number') {
    shapes.push({
      type: 'line',
      x0: meanLine, x1: meanLine, y0: 0, y1: 1, yref: 'paper',
      line: { color: '#F39C12', width: 2, dash: 'dash' },
    });
  }
  const layout = _baseLayout({
    yaxis: { title: 'Frecuencia' },
    xaxis: { title: name || '', automargin: true },
    shapes: shapes,
    bargap: 0.05,
  });
  Plotly.newPlot(el, data, layout, _baseConfig());
}

// Expone las funciones globalmente para los partials inline y tras swaps HTMX.
window.initRadarChart = initRadarChart;
window.initBarChart = initBarChart;
window.initDistributionChart = initDistributionChart;
