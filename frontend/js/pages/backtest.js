import { api } from "../api.js";
import { drawEquityLine, fmtNum } from "../chart.js";

export const BacktestPanel = {
  name: "BacktestPanel",
  props: { symbolId: Number, strategyId: Number },
  emits: ["toast"],
  data() {
    return {
      batches: [],
      equity: [],
      capital: 1000000,
      loading: false,
      selectedBatch: null,
    };
  },
  async mounted() {
    await this.reload();
  },
  template: `
  <section>
    <h2>回测批</h2>
    <div class="sim-bar">
      <label>起始资金<input class="num" type="number" v-model.number="capital" /></label>
      <button :disabled="loading || !symbolId || !strategyId" @click="run">运行回测批</button>
      <span v-if="!symbolId || !strategyId">请先在研究台选择品种与策略</span>
    </div>
    <table class="data-table" style="margin-top:0.75rem">
      <thead>
        <tr><th>批次号</th><th>策略</th><th>品种</th><th>起始</th><th>结束</th><th>胜率</th><th>回撤</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="b in batches" :key="b.id">
          <td class="num">{{ b.批次号 }}</td>
          <td>{{ b.策略名 }}</td>
          <td>{{ b.品种代码 }}</td>
          <td class="num">{{ fmt(b.起始资金) }}</td>
          <td class="num">{{ fmt(b.结束资金) }}</td>
          <td class="num">{{ pct(b.胜率) }}</td>
          <td class="num">{{ pct(b.最大回撤) }}</td>
          <td><button @click="loadCurve(b.id)">曲线</button></td>
        </tr>
      </tbody>
    </table>
    <div class="chart-box" ref="eqBox" style="min-height:220px;margin-top:0.75rem"></div>
  </section>
  `,
  methods: {
    fmt: fmtNum,
    pct(v) {
      if (v === null || v === undefined) return "—";
      return (Number(v) * 100).toFixed(2) + "%";
    },
    async reload() {
      const data = await api.backtestBatches();
      this.batches = data.items || [];
    },
    async run() {
      this.loading = true;
      try {
        const res = await api.runBacktest({
          strategy_id: this.strategyId,
          symbol_id: this.symbolId,
          capital: this.capital,
        });
        this.$emit("toast", `批次 ${res.batch_code} 完成，终值 ${fmtNum(res.end_capital)}`);
        await this.reload();
        await this.loadCurve(res.batch_id);
      } catch (e) {
        this.$emit("toast", e.message);
      } finally {
        this.loading = false;
      }
    },
    async loadCurve(id) {
      this.selectedBatch = id;
      const data = await api.batchEquity(id);
      this.equity = data.points || [];
      drawEquityLine(this.$refs.eqBox, this.equity, 720, 220);
    },
  },
};