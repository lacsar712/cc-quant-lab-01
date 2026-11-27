import { api } from "../api.js";
import { fmtNum } from "../chart.js";

export const PnlPanel = {
  name: "PnlPanel",
  data() {
    return { rows: [], settling: false };
  },
  async mounted() {
    await this.load();
  },
  template: `
  <section>
    <h2>盈亏日结</h2>
    <button :disabled="settling" @click="settle">生成当日日结</button>
    <table class="data-table" style="margin-top:0.75rem">
      <thead>
        <tr><th>交易日</th><th>实现盈亏</th><th>浮动盈亏</th><th>手续费</th><th>净盈亏</th><th>收盘权益</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id">
          <td>{{ r.交易日 }}</td>
          <td class="num">{{ fmt(r.实现盈亏) }}</td>
          <td class="num">{{ fmt(r.浮动盈亏) }}</td>
          <td class="num">{{ fmt(r.手续费合计) }}</td>
          <td class="num">{{ fmt(r.净盈亏) }}</td>
          <td class="num">{{ fmt(r.收盘权益) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
  `,
  methods: {
    fmt: fmtNum,
    async load() {
      const data = await api.pnlDaily();
      this.rows = data.items || [];
    },
    async settle() {
      this.settling = true;
      try {
        await api.pnlSettle();
        await this.load();
      } finally {
        this.settling = false;
      }
    },
  },
};