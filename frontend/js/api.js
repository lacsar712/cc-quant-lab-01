const JSON_HEADERS = { "Content-Type": "application/json" };

async function parseJson(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.error || res.statusText;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  async me() {
    return parseJson(await fetch("/api/me"));
  },
  async overview() {
    return parseJson(await fetch("/api/overview"));
  },
  async symbolTree() {
    return parseJson(await fetch("/api/symbols/tree"));
  },
  async symbols() {
    return parseJson(await fetch("/api/symbols"));
  },
  async loadSymbol(id) {
    return parseJson(await fetch(`/api/symbols/${id}/load`, { method: "POST" }));
  },
  async klines(id, limit) {
    const q = limit ? `?limit=${limit}` : "";
    return parseJson(await fetch(`/api/symbols/${id}/klines${q}`));
  },
  async strategies() {
    return parseJson(await fetch("/api/strategies"));
  },
  async registerStrategy(payload) {
    return parseJson(
      await fetch("/api/strategies", {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify(payload),
      })
    );
  },
  async updateStrategy(id, payload) {
    return parseJson(
      await fetch(`/api/strategies/${id}`, {
        method: "PUT",
        headers: JSON_HEADERS,
        body: JSON.stringify(payload),
      })
    );
  },
  async backtestBatches() {
    return parseJson(await fetch("/api/backtest/batches"));
  },
  async runBacktest(payload) {
    return parseJson(
      await fetch("/api/backtest/run", {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify(payload),
      })
    );
  },
  async batchEquity(id) {
    return parseJson(await fetch(`/api/backtest/batches/${id}/equity`));
  },
  async positions() {
    return parseJson(await fetch("/api/sim/positions"));
  },
  async trades() {
    return parseJson(await fetch("/api/sim/trades"));
  },
  async simOrder(payload) {
    const res = await fetch("/api/sim/order", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
    return parseJson(res);
  },
  async alerts() {
    return parseJson(await fetch("/api/risk/alerts"));
  },
  async dismissAlert(id) {
    return parseJson(await fetch(`/api/risk/alerts/${id}/dismiss`, { method: "POST" }));
  },
  async riskScan() {
    return parseJson(await fetch("/api/risk/scan", { method: "POST" }));
  },
  async pnlDaily() {
    return parseJson(await fetch("/api/pnl/daily"));
  },
  async pnlSettle(day) {
    return parseJson(
      await fetch("/api/pnl/settle", {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify(day ? { trade_day: day } : {}),
      })
    );
  },
  async rules() {
    return parseJson(await fetch("/api/rules"));
  },
  async saveRule(key, value, note) {
    return parseJson(
      await fetch(`/api/rules/${encodeURIComponent(key)}`, {
        method: "PUT",
        headers: JSON_HEADERS,
        body: JSON.stringify({ value, note }),
      })
    );
  },
  async logout() {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/login";
  },
};