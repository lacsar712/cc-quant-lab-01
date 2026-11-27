import { api } from "../api.js";

export const RiskPanel = {
  name: "RiskPanel",
  data() {
    return { alerts: [], scanning: false };
  },
  async mounted() {
    await this.load();
  },
  template: `
  <section>
    <h2>风控尺</h2>
    <div class="sim-bar">
      <button :disabled="scanning" @click="scan">扫描组合风险</button>
    </div>
    <table class="data-table" style="margin-top:0.75rem">
      <thead><tr><th>级别</th><th>类别</th><th>摘要</th><th>时间</th><th></th></tr></thead>
      <tbody>
        <tr v-for="a in alerts" :key="a.id">
          <td :class="{ 'alert-warn': a.级别==='拦截' }">{{ a.级别 }}</td>
          <td>{{ a.类别 }}</td>
          <td>{{ a.摘要 }}</td>
          <td>{{ a.产生时间 }}</td>
          <td><button @click="dismiss(a.id)">处置</button></td>
        </tr>
      </tbody>
    </table>
  </section>
  `,
  methods: {
    async load() {
      const data = await api.alerts();
      this.alerts = data.items || [];
    },
    async dismiss(id) {
      await api.dismissAlert(id);
      await this.load();
    },
    async scan() {
      this.scanning = true;
      try {
        await api.riskScan();
        await this.load();
      } finally {
        this.scanning = false;
      }
    },
  },
};