import { fmtNum } from "../chart.js";

export const OverviewPanel = {
  name: "OverviewPanel",
  props: {
    overview: { type: Object, default: () => ({}) },
    activity: { type: Array, default: () => [] },
  },
  template: `
  <section>
    <h2>研究总览</h2>
    <div class="panel-grid">
      <div class="stat-card" v-for="(v,k) in overview.counts || {}" :key="k">
        <div class="label">{{ k }}</div>
        <div class="value num">{{ v }}</div>
      </div>
      <div class="stat-card">
        <div class="label">未处置告警</div>
        <div class="value num" :class="{ 'alert-warn': overview.open_alerts > 0 }">{{ overview.open_alerts || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="label">收盘权益</div>
        <div class="value num">{{ fmt(overview.pnl && overview.pnl.equity) }}</div>
      </div>
    </div>
    <h3 style="margin-top:1rem">主链进度</h3>
    <ol>
      <li v-for="step in overview.main_chain || []" :key="step">{{ step }}</li>
    </ol>
    <h3>最近活动</h3>
    <table class="data-table">
      <thead><tr><th>类型</th><th>标记</th><th>时刻</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="(row,i) in activity" :key="i">
          <td>{{ row.类型 }}</td>
          <td class="num">{{ row.标记 }}</td>
          <td>{{ row.时刻 }}</td>
          <td>{{ row.状态 }}</td>
        </tr>
      </tbody>
    </table>
  </section>
  `,
  methods: { fmt: fmtNum },
};