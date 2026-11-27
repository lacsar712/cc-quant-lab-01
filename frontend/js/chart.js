export function drawCandles(svgEl, bars, width, height) {
  if (!svgEl || !bars || !bars.length) {
    return;
  }
  const pad = 12;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const lows = bars.map((b) => b.低 ?? b.low);
  const highs = bars.map((b) => b.高 ?? b.high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const span = max - min || 1;
  const step = w / bars.length;
  const parts = [];
  bars.forEach((b, i) => {
    const o = b.开 ?? b.open;
    const c = b.收 ?? b.close;
    const hi = b.高 ?? b.high;
    const lo = b.低 ?? b.low;
    const x = pad + i * step + step * 0.15;
    const bw = Math.max(2, step * 0.6);
    const y = (v) => pad + h - ((v - min) / span) * h;
    const up = c >= o;
    const color = up ? "#1a5c47" : "#a63d3d";
    parts.push(
      `<line x1="${x + bw / 2}" y1="${y(hi)}" x2="${x + bw / 2}" y2="${y(lo)}" stroke="${color}" stroke-width="1"/>`
    );
    const top = y(Math.max(o, c));
    const bot = y(Math.min(o, c));
    parts.push(
      `<rect x="${x}" y="${top}" width="${bw}" height="${Math.max(1, bot - top)}" fill="${color}" opacity="0.85"/>`
    );
  });
  svgEl.innerHTML = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">${parts.join("")}</svg>`;
}

export function drawEquityLine(svgEl, points, width, height) {
  if (!svgEl || !points || !points.length) {
    return;
  }
  const pad = 16;
  const vals = points.map((p) => p.净值 ?? p.value ?? 0);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const coords = points.map((p, i) => {
    const x = pad + (i / Math.max(1, points.length - 1)) * w;
    const v = p.净值 ?? p.value ?? 0;
    const y = pad + h - ((v - min) / span) * h;
    return `${x},${y}`;
  });
  const poly = coords.join(" ");
  svgEl.innerHTML = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    <polyline fill="none" stroke="#1a5c47" stroke-width="2" points="${poly}"/>
    <line x1="${pad}" y1="${pad + h}" x2="${width - pad}" y2="${pad + h}" stroke="#c8bfb0"/>
  </svg>`;
}

export function fmtNum(n, digits) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) {
    return "—";
  }
  return Number(n).toLocaleString("zh-CN", {
    minimumFractionDigits: digits ?? 2,
    maximumFractionDigits: digits ?? 2,
  });
}