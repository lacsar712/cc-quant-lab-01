import { api } from "../api.js";

export const RulesPanel = {
  name: "RulesPanel",
  data() {
    return { rules: [], draft: {} };
  },
  async mounted() {
    await this.load();
  },
  template: `
  <section>
    <h2>规则键值</h2>
    <table class="data-table">
      <thead><tr><th>键</th><th>值</th><th>说明</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="r in rules" :key="r.键">
          <td class="num">{{ r.键 }}</td>
          <td><input class="num" v-model="draft[r.键]" /></td>
          <td>{{ r.说明 }}</td>
          <td><button @click="save(r)">保存</button></td>
        </tr>
      </tbody>
    </table>
  </section>
  `,
  methods: {
    async load() {
      const data = await api.rules();
      this.rules = data.items || [];
      const d = {};
      this.rules.forEach((r) => {
        d[r.键] = r.值;
      });
      this.draft = d;
    },
    async save(r) {
      await api.saveRule(r.键, this.draft[r.键], r.说明 || "");
      await this.load();
    },
  },
};