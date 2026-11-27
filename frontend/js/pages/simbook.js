import { api } from "../api.js";
import { fmtNum } from "../chart.js";

export const SimbookPanel = {
  name: "SimbookPanel",
  data() {
    return { positions: [], trades: [] };
  },
  async mounted() {
    await this.refresh();
  },
  template: `
  <section>
    <h2>仿真簿</h2>
    <button @click="refresh">刷新</button>
    <h3>持仓</h3>
    <table class="data-table">
      <thead><tr><th>品种</th><th>方向</th><th>手数</th><th>开仓价</th><th>浮盈</th></tr></thead>
      <tbody>
        <tr v-for="p in positions" :key="p.id">
          <td>{{ p.代码 }}</td>
          <td>{{ p.方向 }}</td>
          <td class="num">{{ p.手数 }}</td>
          <td class="num">{{ fmt(p.开仓价) }}</td>
          <td class="num">{{ fmt(p.浮盈) }}</td>
        </tr>
      </tbody>
    </table>
    <h3>成交</h3>
    <table class="data-table">
      <thead><tr><th>时间</th><th>品种</th><th>方向</th><th>开平</th><th>手数</th><th>价</th><th>手续费</th><th>回执</th></tr></thead>
      <tbody>
        <tr v-for="t in trades" :key="t.id">
          <td>{{ t.成交时间 }}</td>
          <td>{{ t.代码 }}</td>
          <td>{{ t.方向 }}</td>
          <td>{{ t.开平 }}</td>
          <td class="num">{{ t.手数 }}</td>
          <td class="num">{{ fmt(t.成交价) }}</td>
          <td class="num">{{ fmt(t.手续费) }}</td>
          <td class="num">{{ t.回执号 }}</td>
        </tr>
      </tbody>
    </table>
  </section>
  `,
  methods: {
    fmt: fmtNum,
    async refresh() {
      const pos = await api.positions();
      const tr = await api.trades();
      this.positions = pos.items || [];
      this.trades = tr.items || [];
    },
  },
};