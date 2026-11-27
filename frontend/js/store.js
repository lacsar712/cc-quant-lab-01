export function createWorkbenchStore() {
  return {
    selectedSymbolId: null,
    selectedStrategyId: null,
    klines: [],
    positions: [],
    trades: [],
    alerts: [],
    setSymbol(id) {
      this.selectedSymbolId = id;
    },
    setStrategy(id) {
      this.selectedStrategyId = id;
    },
    patchKlines(bars) {
      this.klines = Array.isArray(bars) ? bars.slice() : [];
    },
    patchPositions(items) {
      this.positions = items || [];
    },
    patchTrades(items) {
      this.trades = items || [];
    },
    patchAlerts(items) {
      this.alerts = items || [];
    },
  };
}