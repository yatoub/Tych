/**
 * charts.js — Graphes statistiques avec Plotly (thème Catppuccin Mocha)
 */

const MOCHA_PLOTLY = {
  base:     '#1e1e2e',
  mantle:   '#181825',
  crust:    '#11111b',
  surface0: '#313244',
  surface1: '#45475a',
  text:     '#cdd6f4',
  subtext0: '#a6adc8',
  mauve:    '#cba6f7',
  blue:     '#89b4fa',
  green:    '#a6e3a1',
  red:      '#f38ba8',
  peach:    '#fab387',
  yellow:   '#f9e2af',
  sapphire: '#74c7ec',
};

const LAYOUT_BASE = {
  paper_bgcolor: MOCHA_PLOTLY.crust,
  plot_bgcolor:  MOCHA_PLOTLY.mantle,
  font:          { color: MOCHA_PLOTLY.text, family: "'JetBrains Mono', monospace", size: 11 },
  margin:        { t: 30, r: 12, b: 40, l: 50 },
  xaxis: {
    gridcolor: MOCHA_PLOTLY.surface0,
    zerolinecolor: MOCHA_PLOTLY.surface1,
    linecolor: MOCHA_PLOTLY.surface1,
    tickfont: { color: MOCHA_PLOTLY.subtext0 },
  },
  yaxis: {
    gridcolor: MOCHA_PLOTLY.surface0,
    zerolinecolor: MOCHA_PLOTLY.surface1,
    linecolor: MOCHA_PLOTLY.surface1,
    tickfont: { color: MOCHA_PLOTLY.subtext0 },
  },
  legend: { bgcolor: 'transparent', font: { color: MOCHA_PLOTLY.subtext0 } },
  showlegend: true,
};

const CONFIG = { responsive: true, displayModeBar: false };

function plotHistogram(divId, data) {
  const { histogram, kde } = data;
  const traces = [
    {
      x: histogram.bin_centers,
      y: histogram.pendulum,
      type: 'bar',
      name: 'Pendule',
      marker: { color: MOCHA_PLOTLY.mauve, opacity: 0.75 },
    },
    {
      x: histogram.bin_centers,
      y: histogram.urandom,
      type: 'bar',
      name: '/dev/urandom',
      marker: { color: MOCHA_PLOTLY.blue, opacity: 0.75 },
    },
    {
      x: kde.x,
      y: kde.pendulum,
      type: 'scatter',
      mode: 'lines',
      name: 'KDE Pendule',
      line: { color: MOCHA_PLOTLY.mauve, width: 2, dash: 'solid' },
    },
    {
      x: kde.x,
      y: kde.urandom,
      type: 'scatter',
      mode: 'lines',
      name: 'KDE urandom',
      line: { color: MOCHA_PLOTLY.blue, width: 2, dash: 'dot' },
    },
  ];

  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'Histogramme + KDE', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    barmode: 'overlay',
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Valeur' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Densité' },
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotQQNormal(divId, data) {
  const { qq_normal } = data;
  if (!qq_normal || !qq_normal.theoretical.length) return;

  const min_ = Math.min(...qq_normal.theoretical);
  const max_ = Math.max(...qq_normal.theoretical);

  const traces = [
    {
      x: qq_normal.theoretical,
      y: qq_normal.sample,
      type: 'scatter',
      mode: 'markers',
      name: 'Pendule',
      marker: { color: MOCHA_PLOTLY.mauve, size: 3, opacity: 0.7 },
    },
    {
      x: [min_, max_],
      y: [min_, max_],
      type: 'scatter',
      mode: 'lines',
      name: 'Référence',
      line: { color: MOCHA_PLOTLY.red, width: 1, dash: 'dash' },
      showlegend: false,
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'QQ-plot vs Normale', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Quantiles théoriques' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Quantiles observés' },
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotQQCompare(divId, data) {
  const { qq_compare } = data;
  if (!qq_compare || !qq_compare.a.length) return;

  const all = [...qq_compare.a, ...qq_compare.b];
  const min_ = Math.min(...all), max_ = Math.max(...all);
  const stride = Math.max(1, Math.floor(qq_compare.a.length / 500));

  const traces = [
    {
      x: qq_compare.a.filter((_, i) => i % stride === 0),
      y: qq_compare.b.filter((_, i) => i % stride === 0),
      type: 'scatter',
      mode: 'markers',
      name: 'Pendule vs urandom',
      marker: { color: MOCHA_PLOTLY.sapphire, size: 3, opacity: 0.6 },
    },
    {
      x: [min_, max_],
      y: [min_, max_],
      type: 'scatter',
      mode: 'lines',
      showlegend: false,
      line: { color: MOCHA_PLOTLY.red, width: 1, dash: 'dash' },
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'QQ-plot Pendule vs /dev/urandom', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Quantiles Pendule (normalisés)' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Quantiles urandom (normalisés)' },
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotGenerateHistogram(divId, data) {
  const { histogram } = data;
  const traces = [
    {
      x: histogram.bin_centers,
      y: histogram.counts,
      type: 'bar',
      name: 'Pendule',
      marker: { color: MOCHA_PLOTLY.mauve, opacity: 0.85 },
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'Distribution des nombres générés', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Valeur [0,1]' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Nombre d\'occurrences' },
    showlegend: false,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotLabHistogram(divId, data) {
  const { histogram } = data;
  const n = histogram.counts.reduce((a, b) => a + b, 0);
  const ideal = n / histogram.counts.length;

  const traces = [
    {
      x: histogram.bin_centers,
      y: histogram.counts,
      type: 'bar',
      name: 'Pendule',
      marker: { color: MOCHA_PLOTLY.mauve, opacity: 0.85 },
    },
    {
      x: [histogram.bin_centers[0], histogram.bin_centers[histogram.bin_centers.length - 1]],
      y: [ideal, ideal],
      type: 'scatter',
      mode: 'lines',
      name: 'Idéal (uniforme)',
      line: { color: MOCHA_PLOTLY.peach, width: 2, dash: 'dot' },
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'Distribution vs idéal uniforme', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Valeur [0,1]' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Occurrences' },
    showlegend: true,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotACF(divId, acfValues) {
  const lags = Array.from({ length: acfValues.length }, (_, i) => i + 1);
  const traces = [
    {
      x: lags,
      y: acfValues,
      type: 'bar',
      name: 'ACF',
      marker: {
        color: acfValues.map(v => Math.abs(v) > 0.05 ? MOCHA_PLOTLY.peach : MOCHA_PLOTLY.green),
      },
    },
    {
      x: [1, lags.length],
      y: [0.05, 0.05],
      type: 'scatter', mode: 'lines',
      name: 'Seuil +5%',
      line: { color: MOCHA_PLOTLY.red, width: 1, dash: 'dot' },
      showlegend: false,
    },
    {
      x: [1, lags.length],
      y: [-0.05, -0.05],
      type: 'scatter', mode: 'lines',
      name: 'Seuil -5%',
      line: { color: MOCHA_PLOTLY.red, width: 1, dash: 'dot' },
      showlegend: false,
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'Autocorrélation (lags 1–20)', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Lag' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'ACF', range: [-1, 1] },
    showlegend: false,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotSpectrum(divId, spectrum) {
  const freqs = Array.from({ length: spectrum.length }, (_, i) => i + 1);
  const traces = [
    {
      x: freqs,
      y: spectrum,
      type: 'scatter',
      mode: 'lines',
      name: 'Puissance',
      line: { color: MOCHA_PLOTLY.sapphire, width: 1.5 },
      fill: 'tozeroy',
      fillcolor: MOCHA_PLOTLY.sapphire + '30',
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: 'Spectre de puissance (FFT)', font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: 'Fréquence' },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Puissance normalisée' },
    showlegend: false,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotRadar(divId, scores) {
  const categories = ['Uniformité', 'Indépendance', 'Entropie', 'Moments'];
  const values = [
    (scores.uniformite  ?? 0) * 100,
    (scores.independance ?? 0) * 100,
    (scores.entropie    ?? 0) * 100,
    (scores.moments     ?? 0) * 100,
  ];
  // Fermer le polygone
  const theta = [...categories, categories[0]];
  const r     = [...values, values[0]];

  const traces = [
    {
      type: 'scatterpolar',
      r,
      theta,
      fill: 'toself',
      fillcolor: MOCHA_PLOTLY.mauve + '40',
      line: { color: MOCHA_PLOTLY.mauve, width: 2 },
      name: 'Score',
    },
  ];
  const layout = {
    paper_bgcolor: MOCHA_PLOTLY.crust,
    plot_bgcolor:  MOCHA_PLOTLY.mantle,
    font: { color: MOCHA_PLOTLY.text, family: "'JetBrains Mono', monospace", size: 11 },
    margin: { t: 30, r: 30, b: 30, l: 30 },
    polar: {
      bgcolor: MOCHA_PLOTLY.mantle,
      radialaxis: {
        visible: true,
        range: [0, 100],
        tickfont: { color: MOCHA_PLOTLY.subtext0, size: 9 },
        gridcolor: MOCHA_PLOTLY.surface0,
        linecolor: MOCHA_PLOTLY.surface1,
      },
      angularaxis: {
        tickfont: { color: MOCHA_PLOTLY.text, size: 10 },
        linecolor: MOCHA_PLOTLY.surface1,
        gridcolor: MOCHA_PLOTLY.surface0,
      },
    },
    showlegend: false,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

function plotSweep(divId, data) {
  const xs = data.points.map(p => p.param_value);
  const traces = [
    {
      x: xs,
      y: data.points.map(p => p.global),
      type: 'scatter', mode: 'lines+markers',
      name: 'Global',
      line: { color: MOCHA_PLOTLY.mauve, width: 2 },
      marker: { size: 6 },
    },
    {
      x: xs,
      y: data.points.map(p => (p.uniformite  ?? 0) * 100),
      type: 'scatter', mode: 'lines',
      name: 'Uniformité',
      line: { color: MOCHA_PLOTLY.blue, width: 1.5, dash: 'dot' },
    },
    {
      x: xs,
      y: data.points.map(p => (p.independance ?? 0) * 100),
      type: 'scatter', mode: 'lines',
      name: 'Indépendance',
      line: { color: MOCHA_PLOTLY.green, width: 1.5, dash: 'dot' },
    },
    {
      x: xs,
      y: data.points.map(p => (p.entropie ?? 0) * 100),
      type: 'scatter', mode: 'lines',
      name: 'Entropie',
      line: { color: MOCHA_PLOTLY.peach, width: 1.5, dash: 'dot' },
    },
  ];
  const layout = {
    ...LAYOUT_BASE,
    title: { text: `Score vs ${data.param}`, font: { color: MOCHA_PLOTLY.text, size: 12 } },
    xaxis: { ...LAYOUT_BASE.xaxis, title: data.param },
    yaxis: { ...LAYOUT_BASE.yaxis, title: 'Score [0–100]', range: [0, 100] },
    showlegend: true,
  };
  Plotly.newPlot(divId, traces, layout, CONFIG);
}

export { plotHistogram, plotQQNormal, plotQQCompare, plotGenerateHistogram, plotLabHistogram, plotACF, plotSpectrum, plotRadar, plotSweep };
