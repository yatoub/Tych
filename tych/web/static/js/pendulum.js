/**
 * pendulum.js — Animation canvas du double pendule (Catppuccin Mocha)
 *
 * Reçoit des trajectoires pre-calculées par le backend (theta1, theta2 à chaque frame)
 * et les rejoue sur un <canvas> avec requestAnimationFrame.
 */

const MOCHA = {
  crust:   '#11111b',
  surface0:'#313244',
  text:    '#cdd6f4',
  subtext0:'#a6adc8',
  mauve:   '#cba6f7',
  blue:    '#89b4fa',
  sapphire:'#74c7ec',
  green:   '#a6e3a1',
  peach:   '#fab387',
  red:     '#f38ba8',
  yellow:  '#f9e2af',
  pink:    '#f5c2e7',
};

const PENDULUM_COLORS = [
  { rod: MOCHA.mauve,   ball1: MOCHA.blue,    ball2: MOCHA.sapphire, trail: 'rgba(137,180,250,0.18)' },
  { rod: MOCHA.green,   ball1: MOCHA.green,   ball2: MOCHA.teal,     trail: 'rgba(166,227,161,0.18)' },
  { rod: MOCHA.peach,   ball1: MOCHA.peach,   ball2: MOCHA.yellow,   trail: 'rgba(250,179,135,0.18)' },
  { rod: MOCHA.red,     ball1: MOCHA.red,     ball2: MOCHA.pink,     trail: 'rgba(243,139,168,0.18)' },
  { rod: MOCHA.sapphire,ball1: MOCHA.sapphire,ball2: MOCHA.sky,      trail: 'rgba(116,199,236,0.18)' },
];

const TRAIL_MAX = 120;

class PendulumAnimator {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx    = this.canvas.getContext('2d');
    this.reset();
  }

  reset() {
    this.data      = null;   // { dt, params, pendulums }
    this.frame     = 0;
    this.playing   = false;
    this.speed     = 1;
    this.rafId     = null;
    this.trails    = [];     // trails[pendIdx] = [ [x2,y2], ... ]
    this._clear();
  }

  _clear() {
    const ctx = this.ctx;
    ctx.fillStyle = MOCHA.crust;
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    // Crosshair pivot
    ctx.strokeStyle = MOCHA.surface0;
    ctx.lineWidth = 1;
    const cx = this.canvas.width / 2, cy = this.canvas.height / 2;
    ctx.beginPath(); ctx.moveTo(cx - 8, cy); ctx.lineTo(cx + 8, cy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, cy - 8); ctx.lineTo(cx, cy + 8); ctx.stroke();
  }

  load(data) {
    this.data   = data;
    this.frame  = 0;
    this.trails = data.pendulums.map(() => []);
    this.pause();
    this._drawFrame(0);
  }

  play() {
    if (!this.data) return;
    this.playing = true;
    this._tick();
  }

  pause() {
    this.playing = false;
    if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
  }

  toggle() {
    if (this.playing) this.pause(); else this.play();
  }

  rewind() {
    this.frame = 0;
    this.trails = this.data ? this.data.pendulums.map(() => []) : [];
    this._drawFrame(0);
  }

  setSpeed(v) { this.speed = v; }

  _tick() {
    if (!this.playing) return;
    for (let s = 0; s < this.speed; s++) {
      this.frame = (this.frame + 1) % this.data.pendulums[0].length;
    }
    this._drawFrame(this.frame);
    this.rafId = requestAnimationFrame(() => this._tick());
  }

  _drawFrame(frameIdx) {
    if (!this.data) return;
    const { params, pendulums } = this.data;
    const W = this.canvas.width, H = this.canvas.height;
    const totalLen = params.l1 + params.l2;
    const margin = 18;
    const scale = (Math.min(W, H) / 2 - margin) / totalLen;
    const cx = W / 2, cy = H / 2;
    const ctx = this.ctx;

    ctx.fillStyle = MOCHA.crust;
    ctx.fillRect(0, 0, W, H);

    // Pivot dot
    ctx.fillStyle = MOCHA.surface0;
    ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2); ctx.fill();

    pendulums.forEach((traj, pidx) => {
      const col = PENDULUM_COLORS[pidx % PENDULUM_COLORS.length];
      const [t1, t2] = traj[frameIdx];
      const x1 = cx + params.l1 * scale * Math.sin(t1);
      const y1 = cy + params.l1 * scale * Math.cos(t1);
      const x2 = x1 + params.l2 * scale * Math.sin(t2);
      const y2 = y1 + params.l2 * scale * Math.cos(t2);

      // Trail
      this.trails[pidx].push([x2, y2]);
      if (this.trails[pidx].length > TRAIL_MAX) this.trails[pidx].shift();

      if (this.trails[pidx].length > 1) {
        ctx.beginPath();
        this.trails[pidx].forEach(([tx, ty], i) => {
          const alpha = i / this.trails[pidx].length;
          ctx.strokeStyle = col.trail.replace('0.18', (alpha * 0.55).toFixed(2));
          if (i === 0) ctx.moveTo(tx, ty); else ctx.lineTo(tx, ty);
        });
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Rod 1
      ctx.strokeStyle = col.rod;
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x1, y1); ctx.stroke();

      // Rod 2
      ctx.strokeStyle = col.rod;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();

      // Mass 1
      ctx.fillStyle = col.ball1;
      ctx.beginPath(); ctx.arc(x1, y1, 6, 0, Math.PI * 2); ctx.fill();

      // Mass 2
      ctx.fillStyle = col.ball2;
      ctx.beginPath(); ctx.arc(x2, y2, 5, 0, Math.PI * 2); ctx.fill();
    });

    // Frame counter
    ctx.fillStyle = MOCHA.subtext0;
    ctx.font = '10px monospace';
    ctx.fillText(`frame ${frameIdx + 1}/${pendulums[0].length}`, 8, H - 8);
  }
}

// Singleton multi-canvas — une instance par canvas
const _animators = {};
function getAnimator(canvasId) {
  if (!_animators[canvasId]) _animators[canvasId] = new PendulumAnimator(canvasId);
  return _animators[canvasId];
}

export { PendulumAnimator, getAnimator };
