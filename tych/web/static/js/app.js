/**
 * app.js — Logique principale de l'interface Tych
 */

import { getAnimator } from './pendulum.js';
import { plotGenerateHistogram, plotLabHistogram, plotACF, plotSpectrum, plotRadar, plotSweep } from './charts.js';

// ── DOM helpers ──────────────────────────────────────────────────────────────
const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function setStatus(el, msg, kind = '') {
  el.textContent = msg;
  el.className = `status ${kind}`;
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
$$('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.tab-btn').forEach(b => b.classList.remove('active'));
    $$('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('#' + btn.dataset.tab).classList.add('active');
  });
});

// ── Sidebar sliders ──────────────────────────────────────────────────────────
function bindSlider(sliderId, displayId) {
  const slider  = $('#' + sliderId);
  const display = $('#' + displayId);
  display.textContent = slider.value;
  slider.addEventListener('input', () => { display.textContent = slider.value; });
}

bindSlider('gen-n-slider',    'gen-n-val');
bindSlider('gen-pendulums',   'gen-pendulums-val');
bindSlider('gen-noise',       'gen-noise-val');

// Bindings bidirectionnels slider ↔ input[number] pour les paramètres physiques
function bindPhysicsSlider(sliderId, numId) {
  const slider = $('#' + sliderId);
  const num    = $('#' + numId);
  num.value = parseFloat(slider.value).toFixed(3);
  slider.addEventListener('input', () => { num.value = parseFloat(slider.value).toFixed(3); });
  num.addEventListener('input',    () => { const v = parseFloat(num.value); if (!isNaN(v)) slider.value = v; });
  num.addEventListener('change',   () => {
    const lo = parseFloat(slider.min), hi = parseFloat(slider.max);
    let v = parseFloat(num.value);
    if (isNaN(v)) v = parseFloat(slider.value);
    v = Math.max(lo, Math.min(hi, v));
    slider.value = v;
    num.value    = v.toFixed(3);
  });
}

bindPhysicsSlider('phys-l1',      'phys-l1-num');
bindPhysicsSlider('phys-l2',      'phys-l2-num');
bindPhysicsSlider('phys-m1',      'phys-m1-num');
bindPhysicsSlider('phys-m2',      'phys-m2-num');
bindPhysicsSlider('phys-g',       'phys-g-num');
bindPhysicsSlider('phys-damping', 'phys-damping-num');

function setPhysicsParam(key, val) {
  const slider = $('#phys-' + key);
  const num    = $('#phys-' + key + '-num');
  if (slider) slider.value = val;
  if (num)    num.value    = parseFloat(val).toFixed(3);
}

// ── Paramètres physiques ─────────────────────────────────────────────────────
const PHYSICS_DEFAULTS = { l1: 1.0, l2: 1.0, m1: 1.0, m2: 1.0, g: 9.81, damping: 0.999 };

function getPhysics() {
  return {
    l1:      parseFloat($('#phys-l1').value),
    l2:      parseFloat($('#phys-l2').value),
    m1:      parseFloat($('#phys-m1').value),
    m2:      parseFloat($('#phys-m2').value),
    g:       parseFloat($('#phys-g').value),
    damping: parseFloat($('#phys-damping').value),
  };
}

$('#phys-reset').addEventListener('click', () => {
  Object.entries(PHYSICS_DEFAULTS).forEach(([key, val]) => setPhysicsParam(key, val));
});

$('#traj-speed').addEventListener('input', (e) => {
  if (genAnimator) genAnimator.setSpeed(parseInt(e.target.value));
  $('#traj-speed-val').textContent = e.target.value + '×';
});

// ── Pendulum animator (génération) ───────────────────────────────────────────
let genAnimator = null;

function setupGenCanvas(n_pendulums) {
  const canvas = $('#gen-canvas');
  const placeholder = $('#gen-canvas-placeholder');

  // Dimensions : carré, rempli dans la colonne de 340px
  const size = 308; // 340px col - 2×16px padding
  canvas.width  = size;
  canvas.height = size;

  if (placeholder) placeholder.style.display = 'none';
  if (canvas) canvas.style.display = 'block';

  if (genAnimator) genAnimator.pause();
  genAnimator = getAnimator('gen-canvas');
}

function setAnimationControls(enabled) {
  $('#traj-play').disabled   = !enabled;
  $('#traj-rewind').disabled = !enabled;
}

$('#traj-play').addEventListener('click', () => {
  if (!genAnimator) return;
  genAnimator.toggle();
  $('#traj-play').textContent = genAnimator.playing ? '⏸ Pause' : '▶ Play';
});

$('#traj-rewind').addEventListener('click', () => {
  if (!genAnimator) return;
  genAnimator.rewind();
  genAnimator.play();
  $('#traj-play').textContent = '⏸ Pause';
});

// ── Generate ─────────────────────────────────────────────────────────────────
$('#gen-run').addEventListener('click', async () => {
  const n         = parseInt($('#gen-n-slider').value);
  const pendulums = parseInt($('#gen-pendulums').value);
  const noise     = parseFloat($('#gen-noise').value);
  const status    = $('#gen-status');
  const spinner   = $('#gen-spinner');

  setStatus(status, 'Génération + simulation en cours…', 'busy');
  spinner.classList.add('visible');
  $('#gen-run').disabled = true;
  setAnimationControls(false);

  // Nombre de frames proportionnel à n, borné pour rester rapide
  const trajSteps = Math.min(1200, Math.max(400, n));

  try {
    const physics = getPhysics();

    // Appels parallèles : génération + trajectoires
    const [genRes, trajRes] = await Promise.all([
      fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n, pendulums, noise, ...physics }),
      }),
      fetch('/api/trajectory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps: trajSteps, pendulums, ...physics }),
      }),
    ]);

    if (!genRes.ok)  throw new Error((await genRes.json()).detail  || genRes.statusText);
    if (!trajRes.ok) throw new Error((await trajRes.json()).detail || trajRes.statusText);

    const [genData, trajData] = await Promise.all([genRes.json(), trajRes.json()]);

    // ── Animation pendules ───────────────────────────────────────────────────
    setupGenCanvas(pendulums);
    genAnimator.load(trajData);
    genAnimator.play();
    $('#traj-play').textContent = '⏸ Pause';
    setAnimationControls(true);

    // ── Stats ────────────────────────────────────────────────────────────────
    $('#gen-mean').textContent = genData.mean.toFixed(5);
    $('#gen-std').textContent  = genData.std.toFixed(5);
    $('#gen-min').textContent  = genData.min.toFixed(5);
    $('#gen-max').textContent  = genData.max.toFixed(5);

    // ── Échantillon ──────────────────────────────────────────────────────────
    $('#gen-sample').textContent = genData.sample.map(v => v.toFixed(6)).join('\n');

    // ── Histogramme ──────────────────────────────────────────────────────────
    hide('gen-chart-placeholder');
    show('gen-chart');
    try { plotGenerateHistogram('gen-chart', genData); } catch (_) {}

    setStatus(status, `${genData.n} valeurs générées · ${trajData.pendulums.length} pendule(s) animé(s) ✓`, 'ok');

  } catch (e) {
    setStatus(status, `Erreur : ${e.message}`, 'error');
  } finally {
    spinner.classList.remove('visible');
    $('#gen-run').disabled = false;
  }
});

// ── Évaluation ───────────────────────────────────────────────────────────────

let labHistory = [];   // max 8 : { score, params, raw, sub_scores }
let labBest    = null; // { score, params }
let labN       = 500;  // contrôlé par les boutons précision

// Sélecteur de précision
$$('#lab-precision-group .precision-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('#lab-precision-group .precision-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    labN = parseInt(btn.dataset.n);
  });
});

function scoreColorClass(score) {
  if (score >= 75) return 'score-good';
  if (score >= 60) return 'score-mid';
  if (score >= 40) return 'score-low';
  return 'score-bad';
}

function subScoreColor(pct) {
  if (pct >= 0.75) return 'var(--green)';
  if (pct >= 0.50) return 'var(--yellow)';
  if (pct >= 0.30) return 'var(--peach)';
  return 'var(--red)';
}

function historyBarColor(score) {
  if (score >= 75) return 'var(--green)';
  if (score >= 60) return 'var(--yellow)';
  if (score >= 40) return 'var(--peach)';
  return 'var(--red)';
}

function animateCounter(el, target, cls) {
  let current = 0;
  const step  = Math.max(1, Math.ceil(target / 40));
  el.className = 'score-number';
  const tick = () => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current < target) setTimeout(tick, 25);
    else {
      el.textContent = target;
      el.className   = 'score-number ' + cls;
    }
  };
  tick();
}

function updateStars(score) {
  const stars = $$('#lab-stars span');
  const filled = Math.round(score / 20);
  stars.forEach((s, i) => {
    s.textContent  = i < filled ? '★' : '☆';
    s.className    = i < filled ? 'star-on' : 'star-off';
  });
}

function renderSubScore(key, value) {
  const pct = Math.round((value ?? 0) * 100);
  const fillEl = $('#fill-' + key);
  const pctEl  = $('#pct-'  + key);
  if (!fillEl || !pctEl) return;
  fillEl.style.width      = pct + '%';
  fillEl.style.background = subScoreColor(value ?? 0);
  pctEl.textContent       = pct + '%';
}

function show(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.remove('chart-hidden'); el.style.removeProperty('display'); }
  return el;
}

function hide(id) {
  const el = document.getElementById(id);
  if (el) { el.style.display = 'none'; }
  return el;
}

function updateHint(categories, raw) {
  const hint = $('#lab-hint');
  if (!hint) return;
  hint.style.display = 'block';

  const entries = Object.entries(categories).sort((a, b) => (a[1].score ?? 0) - (b[1].score ?? 0));
  const [worstKey, worstData] = entries[0];
  const worstVal = worstData.score ?? 0;

  if (worstVal >= 0.85) {
    hint.textContent = "Configuration excellente ! Tous les indicateurs sont au vert. Passe en mode Fine pour confirmer.";
    return;
  }

  const IDEAL_STD = 1 / Math.sqrt(12);
  const messages = {
    uniformite:   () => `Uniformité faible (KS stat = ${(raw?.ks_stat ?? '?').toString().slice(0,6)}, p = ${(raw?.ks_p ?? '?').toString().slice(0,6)}) — modifie l1 ≠ l2 pour amplifier la sensibilité aux conditions initiales.`,
    independance: () => `Indépendance faible (ACF max = ${(worstData.acf_max ?? '?').toString().slice(0,6)}, runs p = ${(worstData.runs_p ?? '?').toString().slice(0,6)}) — augmente le nombre de pendules ou réduis l'amortissement.`,
    entropie:     () => `Entropie faible (Shannon = ${(worstData.shannon_ratio ?? 0).toFixed(3)}) — augmente le bruit pour diversifier les états chaotiques.`,
    moments:      () => `Moments hors-cible (moy. = ${(raw?.mean ?? 0).toFixed(4)}, σ = ${(raw?.std ?? 0).toFixed(4)}) — essaie m1 ≠ m2 ou modifie l'amortissement.`,
  };
  hint.textContent = (messages[worstKey] || (() => 'Ajuste les paramètres physiques.'))();
}

function renderHistory() {
  const list = $('#lab-history');
  if (!labHistory.length) {
    list.innerHTML = '<div style="color:var(--overlay0);font-size:0.78rem;padding:0.5rem 0">Aucune évaluation</div>';
    return;
  }
  list.innerHTML = '';
  labHistory.forEach((entry, i) => {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.title     = 'Cliquer pour restaurer ces paramètres';

    const rank  = document.createElement('span');
    rank.className   = 'history-rank';
    rank.textContent = '#' + (i + 1);

    const wrap = document.createElement('div');
    wrap.className = 'history-bar-wrap';
    const bar = document.createElement('div');
    bar.className        = 'history-bar';
    bar.style.width      = entry.score + '%';
    bar.style.background = historyBarColor(entry.score);
    wrap.appendChild(bar);

    const scoreEl = document.createElement('span');
    scoreEl.className   = 'history-score';
    scoreEl.textContent = entry.score;
    scoreEl.style.color = historyBarColor(entry.score);

    item.appendChild(rank);
    item.appendChild(wrap);
    item.appendChild(scoreEl);

    item.addEventListener('click', () => {
      Object.entries(entry.params).forEach(([key, val]) => setPhysicsParam(key, val));
    });

    list.appendChild(item);
  });
}

async function labEval() {
  const params    = getPhysics();
  const pendulums = parseInt($('#gen-pendulums').value);
  const noise     = parseFloat($('#gen-noise').value);
  const status    = $('#lab-status');
  const spinner   = $('#lab-spinner');

  setStatus(status, 'Évaluation en cours…', 'busy');
  spinner.classList.add('visible');
  $('#lab-run').disabled = true;

  try {
    const res = await fetch('/api/quality', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ n: labN, pendulums, noise, compute_apen: labN >= 500, ...params }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const data = await res.json();

    updateLabUI(data, params);
    setStatus(status, `Score : ${data.global}/100 sur ${data.n} valeurs ✓`, 'ok');

  } catch (e) {
    setStatus(status, `Erreur : ${e.message}`, 'error');
  } finally {
    spinner.classList.remove('visible');
    $('#lab-run').disabled = false;
  }
}

function updateLabUI(data, params) {
  const score = data.global;
  const cls   = scoreColorClass(score);

  // Compteur animé
  animateCounter($('#lab-score'), score, cls);

  // Étoiles
  updateStars(score);

  // Meilleur score
  if (!labBest || score > labBest.score) {
    labBest = { score, params: { ...params } };
    const best = document.getElementById('lab-best');
    if (best) best.style.display = 'flex';
    const bestScore = document.getElementById('lab-best-score');
    if (bestScore) bestScore.textContent = score;
    const card = document.querySelector('.score-card');
    if (card) {
      card.style.borderColor = 'var(--green)';
      setTimeout(() => { card.style.borderColor = ''; }, 1200);
    }
  }

  // Sous-scores
  const cats = { uniformite: data.uniformite, independance: data.independance, entropie: data.entropie, moments: data.moments };
  Object.entries(cats).forEach(([k, v]) => renderSubScore(k, v?.score ?? 0));

  // Conseil
  updateHint(cats, { ...data.uniformite, ...data.moments });

  // Histogramme
  hide('lab-chart-placeholder');
  show('lab-chart');
  try { plotLabHistogram('lab-chart', data); } catch (_) {}

  // Radar
  if (data.uniformite) {
    show('lab-radar');
    try {
      plotRadar('lab-radar', { uniformite: data.uniformite.score, independance: data.independance.score, entropie: data.entropie.score, moments: data.moments.score });
    } catch (_) {}
  }

  // ACF
  if (data.acf && data.acf.length) {
    show('lab-acf-box');
    try { plotACF('lab-acf', data.acf); } catch (_) {}
  }

  // Spectre
  if (data.spectrum && data.spectrum.length) {
    show('lab-spectrum-box');
    try { plotSpectrum('lab-spectrum', data.spectrum); } catch (_) {}
  }

  // Description en langage naturel
  updateEvalDesc(data);

  // Historique (max 8)
  labHistory.unshift({ score, params: { ...params }, cats });
  if (labHistory.length > 8) labHistory.pop();
  renderHistory();
}

// ── Descriptions en langage naturel ─────────────────────────────────────────

function makeSpan(text, cls) {
  const s = document.createElement('span');
  s.textContent = text;
  if (cls) s.className = cls;
  return s;
}

function scoreLabel(s) {
  if (s >= 0.80) return ['bonne',       'verdict-ok'];
  if (s >= 0.55) return ['moyenne',     'verdict-warn'];
  return              ['faible',        'verdict-bad'];
}

function updateEvalDesc(data) {
  const el = document.getElementById('eval-desc');
  if (!el) return;

  const score   = data.global;
  const u       = data.uniformite?.score       ?? 0;
  const ind     = data.independance?.score     ?? 0;
  const e       = data.entropie?.score         ?? 0;
  const m       = data.moments?.score          ?? 0;
  const mean    = data.moments?.mean           ?? 0;
  const std     = data.moments?.std            ?? 0;
  const ks_p    = data.uniformite?.ks_p        ?? 0;
  const acf     = data.independance?.acf_max   ?? 0;
  const shannon = data.entropie?.shannon_ratio ?? 0;

  const stdTarget = 1 / Math.sqrt(12);

  const lines = [
    {
      label: 'Uniformité',   score: u,
      detail: ks_p >= 0.05
        ? `Distribution statistiquement uniforme (p = ${ks_p.toFixed(3)} ≥ 0,05)`
        : `Distribution légèrement non-uniforme (p = ${ks_p.toFixed(3)} < 0,05)`,
    },
    {
      label: 'Indépendance', score: ind,
      detail: acf < 0.05
        ? `Valeurs indépendantes (corrélation max = ${acf.toFixed(3)})`
        : `Dépendance temporelle détectée (corrélation max = ${acf.toFixed(3)})`,
    },
    {
      label: 'Entropie',     score: e,
      detail: shannon >= 0.99
        ? `Diversité quasi-maximale (entropie = ${(shannon * 100).toFixed(1)} % du maximum)`
        : `Diversité réduite (entropie = ${(shannon * 100).toFixed(1)} % du maximum)`,
    },
    {
      label: 'Moments',      score: m,
      detail: (Math.abs(mean - 0.5) < 0.02 && Math.abs(std - stdTarget) < 0.01)
        ? `Moyenne (${mean.toFixed(4)}) et écart-type (${std.toFixed(4)}) conformes aux valeurs théoriques`
        : `Moyenne ${mean.toFixed(4)} (cible 0,5000), écart-type ${std.toFixed(4)} (cible ${stdTarget.toFixed(4)})`,
    },
  ];

  // Verdict global
  const [globalLabel, globalCls] = score >= 80 ? ['excellente', 'verdict-ok']
                                 : score >= 60 ? ['correcte',   'verdict-warn']
                                              : ['insuffisante','verdict-bad'];

  el.textContent = '';

  // Ligne résumé
  const summary = document.createElement('div');
  const bold = document.createElement('strong');
  bold.textContent = 'Résumé : ';
  summary.appendChild(bold);
  summary.appendChild(document.createTextNode('qualité '));
  summary.appendChild(makeSpan(globalLabel, globalCls));
  summary.appendChild(document.createTextNode(` — score ${score}/100 sur ${data.n} valeurs générées.`));
  el.appendChild(summary);

  // Lignes de détail
  const details = document.createElement('div');
  details.className = 'eval-detail-lines';
  lines.forEach(({ label, score: s, detail }) => {
    const row = document.createElement('div');
    const [slabel, scls] = scoreLabel(s);
    row.appendChild(makeSpan(label + ' ', 'eval-detail-cat'));
    row.appendChild(makeSpan(slabel, scls));
    row.appendChild(document.createTextNode(' — ' + detail));
    details.appendChild(row);
  });
  el.appendChild(details);

  el.classList.add('visible');
}

function updateSweepDesc(data) {
  const el = document.getElementById('sweep-desc');
  if (!el || !data.points?.length) return;

  const validPts = data.points.filter(p => p.global != null);
  if (!validPts.length) { el.classList.remove('visible'); return; }

  const best   = validPts.reduce((a, b) => a.global > b.global ? a : b);
  const worst  = validPts.reduce((a, b) => a.global < b.global ? a : b);
  const scores = validPts.map(p => p.global);
  const range  = Math.max(...scores) - Math.min(...scores);

  const PARAM_LABELS = {
    noise: 'bruit', pendulums: 'nombre de pendules', m1: 'masse 1', m2: 'masse 2',
    l1: 'longueur 1', l2: 'longueur 2', g: 'gravité', damping: 'amortissement',
  };
  const label = PARAM_LABELS[data.param] || data.param;

  let sensitivity;
  if (range >= 30)      sensitivity = 'très sensible';
  else if (range >= 15) sensitivity = 'modérément sensible';
  else if (range >= 5)  sensitivity = 'peu sensible';
  else                  sensitivity = 'quasiment insensible';

  const trend = scores[scores.length - 1] > scores[0] ? 'croissante' :
                scores[scores.length - 1] < scores[0] ? 'décroissante' : 'stable';

  el.textContent = `La qualité est ${sensitivity} au ${label} (écart de ${range} points). `
    + `Meilleur score : ${best.global}/100 pour ${label} = ${best.param_value}. `
    + `Tendance générale : ${trend}.`;
  el.classList.add('visible');
}

$('#lab-run').addEventListener('click', labEval);

$('#lab-best-restore').addEventListener('click', () => {
  if (!labBest) return;
  Object.entries(labBest.params).forEach(([key, val]) => setPhysicsParam(key, val));
});

// ── Sweep ────────────────────────────────────────────────────────────────────

// Plages par défaut pour chaque paramètre
const SWEEP_DEFAULTS = {
  noise:     [0.0, 1.5],
  pendulums: [1,   10],
  m1:        [0.5, 3.0],
  m2:        [0.5, 3.0],
  l1:        [0.2, 3.0],
  l2:        [0.2, 3.0],
  g:         [1.0, 20.0],
  damping:   [0.900, 1.0],
};

$('#sweep-param').addEventListener('change', (e) => {
  const [lo, hi] = SWEEP_DEFAULTS[e.target.value] || [0, 1];
  $('#sweep-min').value = lo;
  $('#sweep-max').value = hi;
});

$('#sweep-steps').addEventListener('input', (e) => {
  $('#sweep-steps-val').textContent = e.target.value;
});

$('#sweep-run').addEventListener('click', async () => {
  const param   = $('#sweep-param').value;
  const minV    = parseFloat($('#sweep-min').value);
  const maxV    = parseFloat($('#sweep-max').value);
  const steps   = parseInt($('#sweep-steps').value);
  const n       = parseInt($('#sweep-n').value);
  const status  = $('#sweep-status');
  const spinner = $('#sweep-spinner');
  const physics = getPhysics();
  const pendulums = parseInt($('#gen-pendulums').value);
  const noise     = parseFloat($('#gen-noise').value);

  if (minV >= maxV) {
    setStatus(status, 'La borne min doit être < max', 'error');
    return;
  }

  setStatus(status, `Exploration de ${param} sur ${steps} points…`, 'busy');
  spinner.classList.add('visible');
  $('#sweep-run').disabled = true;

  try {
    const res = await fetch('/api/lab/sweep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        param,
        range_min: minV,
        range_max: maxV,
        steps,
        n,
        compute_apen: false,
        pendulums,
        noise,
        ...physics,
      }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const data = await res.json();

    hide('sweep-chart-placeholder');
    show('sweep-chart');
    try { plotSweep('sweep-plot', data); } catch (_) {}
    updateSweepDesc(data);

    setStatus(status, `Exploration terminée — ${data.points.length} points ✓`, 'ok');
  } catch (e) {
    setStatus(status, `Erreur : ${e.message}`, 'error');
  } finally {
    spinner.classList.remove('visible');
    $('#sweep-run').disabled = false;
  }
});

