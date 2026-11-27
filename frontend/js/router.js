export const ROUTES = [
  { key: "overview", title: "研究总览", path: "#/overview" },
  { key: "backtest", title: "回测批", path: "#/backtest" },
  { key: "simbook", title: "仿真簿", path: "#/simbook" },
  { key: "risk", title: "风控尺", path: "#/risk" },
  { key: "pnl", title: "盈亏日结", path: "#/pnl" },
  { key: "rules", title: "规则", path: "#/rules" },
];

export function parseHashRoute() {
  const raw = (window.location.hash || "#/overview").replace(/^#\/?/, "");
  const seg = raw.split("/")[0] || "overview";
  const hit = ROUTES.find((r) => r.key === seg);
  return hit ? hit.key : "overview";
}

export function setHashRoute(key) {
  const item = ROUTES.find((r) => r.key === key) || ROUTES[0];
  window.location.hash = item.path.replace("#", "");
}