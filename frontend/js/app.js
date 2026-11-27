import { api } from "./api.js";
import { drawCandles, drawEquityLine, fmtNum } from "./chart.js";
import { OverviewPanel } from "./pages/overview.js";
import { BacktestPanel } from "./pages/backtest.js";
import { SimbookPanel } from "./pages/simbook.js";
import { RiskPanel } from "./pages/risk.js";
import { PnlPanel } from "./pages/pnl.js";
import { RulesPanel } from "./pages/rules.js";

const MENU = [
  { hash: "#/overview", label: "研究总览", key: "overview" },
  { hash: "#/backtest", label: "回测批", key: "backtest" },
  { hash: "#/simbook", label: "仿真簿", key: "simbook" },
  { hash: "#/risk", label: "风控尺", key: "risk" },
  { hash: "#/pnl", label: "盈亏日结", key: "pnl" },
  { hash: "#/rules", label: "规则", key: "rules" },
];

const { createApp } = Vue;

const App = {
  components: {
    OverviewPanel,
    BacktestPanel,
    SimbookPanel,
    RiskPanel,
    PnlPanel,
    RulesPanel,
  },
  data() {
    return {
      menu: MENU,
      route: "overview",
      me: null,
      tree: [],
      strategies: [],
      selectedSymbol: null,
      selectedStrategy: null,
      klines: [],
      positions: [],
      trades: [],
      alerts: [],
      rightTab: "pos",
      overview: {},
      activity: [],
      toast: "",
      sim: { direction: "多", offset: "开", lots: 1, price: "" },
      loadingKline: false,
      lastBatchEquity: [],
    };
  },
  computed: {
    activeMenu() {
      return this.menu.find((m) => m.key === this.route) || this.menu[0];
    },
    panelComponent() {
      const map = {
        overview: "OverviewPanel",
        backtest: "BacktestPanel",
        simbook: "SimbookPanel",
        risk: "RiskPanel",
        pnl: "PnlPanel",
        rules: "RulesPanel",
      };
      return map[this.route] || "OverviewPanel";
    },
  },
  watch: {
    selectedSymbol() {
      this.fetchKlines();
    },
  },
  async mounted() {
    window.addEventListener("hashchange", this.parseRoute);
    this.parseRoute();
    try {
      this.me = await api.me();
    } catch (e) {
      window.location.href = "/login";
      return;
    }
    await this.bootstrap();
  },
  methods: {
    fmt: fmtNum,
    parseRoute() {
      const h = (window.location.hash || "#/overview").replace("#/", "");
      const key = h.split("/")[0] || "overview";
      this.route = MENU.some((m) => m.key === key) ? key : "overview";
    },
    navigate(item) {
      window.location.hash = item.hash.replace("#", "");
      this.route = item.key;
    },
    async bootstrap() {
      const [tree, strat, ov, pos, tr, al] = await Promise.all([
        api.symbolTree(),
        api.strategies(),
        api.overview(),
        api.positions(),
        api.trades(),
        api.alerts(),
      ]);
      this.tree = tree.tree || [];
      this.strategies = strat.items || [];
      this.overview = ov;
      this.activity = ov.activity || [];
      this.positions = pos.items || [];
      this.trades = tr.items || [];
      this.alerts = al.items || [];
      if (!this.selectedSymbol && this.strategies.length) {
        this.selectedStrategy = this.strategies[0].id;
      }
      for (const g of this.tree) {
        for (const c of g.children || []) {
          if (!this.selectedSymbol) {
            this.selectedSymbol = c.id;
          }
        }
      }
      await this.fetchKlines();
      this.$nextTick(() => this.paintCharts());
    },
    selectSymbol(sym) {
      this.selectedSymbol = sym.id;
    },
    selectStrategy(s) {
      this.selectedStrategy = s.id;
    },
    async loadSamples(sym) {
      try {
        const r = await api.loadSymbol(sym.id);
        this.toast = `已装载 ${sym.代码}，新增 ${r.loaded_bars} 根K线`;
        await this.bootstrap();
      } catch (e) {
        this.toast = e.message;
      }
    },
    async fetchKlines() {
      if (!this.selectedSymbol) {
        return;
      }
      this.loadingKline = true;
      try {
        const data = await api.klines(this.selectedSymbol, 80);
        this.klines = data.bars || [];
        this.$nextTick(() => this.paintCharts());
      } finally {
        this.loadingKline = false;
      }
    },
    paintCharts() {
      const kbox = this.$refs.klineBox;
      if (kbox) {
        drawCandles(kbox, this.klines, kbox.clientWidth || 640, 200);
      }
      if (this.lastBatchEquity.length && this.$refs.miniEq) {
        drawEquityLine(this.$refs.miniEq, this.lastBatchEquity, 640, 120);
      }
    },
    async submitSim() {
      if (!this.selectedSymbol) {
        this.toast = "请先选择品种";
        return;
      }
      try {
        const payload = {
          symbol_id: this.selectedSymbol,
          direction: this.sim.direction,
          offset: this.sim.offset,
          lots: this.sim.lots,
        };
        if (this.sim.price) {
          payload.price = Number(this.sim.price);
        }
        const res = await api.simOrder(payload);
        if (res.ok) {
          this.toast = `成交 ${res.ticket} @ ${res.price}`;
        } else {
          this.toast = res.error || "下单失败";
        }
        const pos = await api.positions();
        const tr = await api.trades();
        const al = await api.alerts();
        this.positions = pos.items || [];
        this.trades = tr.items || [];
        this.alerts = al.items || [];
      } catch (e) {
        this.toast = e.message;
      }
    },
    onToast(msg) {
      this.toast = msg;
    },
    async quickBacktest() {
      if (!this.selectedSymbol || !this.selectedStrategy) {
        this.toast = "请选择品种与策略";
        return;
      }
      try {
        const res = await api.runBacktest({
          strategy_id: this.selectedStrategy,
          symbol_id: this.selectedSymbol,
        });
        this.toast = `回测完成 ${res.batch_code}`;
        const eq = await api.batchEquity(res.batch_id);
        this.lastBatchEquity = eq.points || [];
        this.$nextTick(() => this.paintCharts());
      } catch (e) {
        this.toast = e.message;
      }
    },
  },
  template: `
  <div id="app-root">
    <header class="top-menu">
      <span class="brand">衡尺盘</span>
      <button v-for="m in menu" :key="m.key"
        class="menu-link"
        :class="{ active: route === m.key }"
        @click="navigate(m)">{{ m.label }}</button>
      <span class="num" style="font-size:0.82rem;margin-left:0.5rem">{{ me && me.user }}</span>
      <button class="logout-btn" @click="api.logout()">退出</button>
    </header>
    <section v-if="route === 'overview'" class="workspace">
      <aside class="col">
        <h3>品种树</h3>
        <div v-for="g in tree" :key="g.exchange" class="tree-group">
          <div class="tree-title">{{ g.exchange }}</div>
          <button v-for="s in g.children" :key="s.id"
            class="tree-item"
            :class="{ sel: selectedSymbol === s.id }"
            @click="selectSymbol(s)">
            {{ s.代码 }}
            <span v-if="s.已装载">·已装</span>
          </button>
          <button class="tree-item" v-for="s in g.children" :key="'load'+s.id" style="font-size:0.75rem" @click="loadSamples(s)">装载 {{ s.代码 }} 样本</button>
        </div>
        <h3>策略列表</h3>
        <button v-for="st in strategies" :key="st.id"
          class="strategy-item"
          :class="{ sel: selectedStrategy === st.id }"
          @click="selectStrategy(st)">
          {{ st.名称 }} <span class="num">[{{ st.状态 }}]</span>
        </button>
      </aside>
      <main class="col">
        <h3>K线（简易）</h3>
        <div class="chart-box" ref="klineBox" style="min-height:200px"></div>
        <h3>回测曲线区</h3>
        <div class="chart-box" ref="miniEq" style="min-height:120px"></div>
        <button @click="quickBacktest">快速回测当前组合</button>
        <h3>下单仿真条</h3>
        <div class="sim-bar">
          <label>方向<select v-model="sim.direction"><option>多</option><option>空</option></select></label>
          <label>开平<select v-model="sim.offset"><option>开</option><option>平</option></select></label>
          <label>手数<input class="num" type="number" v-model.number="sim.lots" min="1"/></label>
          <label>限价<input class="num" v-model="sim.price" placeholder="空=市价"/></label>
          <button @click="submitSim">仿真下单</button>
        </div>
        <p v-if="toast" class="num" style="color:var(--green)">{{ toast }}</p>
      </main>
      <aside class="col">
        <div class="tabs">
          <button class="tab-btn" :class="{ on: rightTab==='pos' }" @click="rightTab='pos'">仓位</button>
          <button class="tab-btn" :class="{ on: rightTab==='tr' }" @click="rightTab='tr'">成交</button>
          <button class="tab-btn" :class="{ on: rightTab==='al' }" @click="rightTab='al'">告警</button>
        </div>
        <table v-show="rightTab==='pos'" class="data-table">
          <thead><tr><th>品种</th><th>方向</th><th>手</th><th>浮盈</th></tr></thead>
          <tbody>
            <tr v-for="p in positions" :key="p.id">
              <td>{{ p.代码 }}</td><td>{{ p.方向 }}</td><td class="num">{{ p.手数 }}</td><td class="num">{{ fmt(p.浮盈) }}</td>
            </tr>
          </tbody>
        </table>
        <table v-show="rightTab==='tr'" class="data-table">
          <tbody>
            <tr v-for="t in trades.slice(0,12)" :key="t.id">
              <td>{{ t.代码 }}</td><td>{{ t.开平 }}</td><td class="num">{{ t.成交价 }}</td>
            </tr>
          </tbody>
        </table>
        <table v-show="rightTab==='al'" class="data-table">
          <tbody>
            <tr v-for="a in alerts" :key="a.id">
              <td :class="{ 'alert-warn': a.级别==='拦截' }">{{ a.级别 }}</td>
              <td>{{ a.摘要 }}</td>
            </tr>
          </tbody>
        </table>
      </aside>
    </section>
    <main v-else class="full-panel">
      <component :is="panelComponent"
        :overview="overview"
        :activity="activity"
        :symbol-id="selectedSymbol"
        :strategy-id="selectedStrategy"
        @toast="onToast"
      />
      <p v-if="toast" class="num">{{ toast }}</p>
    </main>
  </div>
  `,
};

createApp(App).mount("#app-root");