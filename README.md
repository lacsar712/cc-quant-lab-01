# 衡尺盘模拟研究台（cc-quant-lab）

离线量化交易研究产品线，不接真实交易所 API。

## 技术栈

- 后端：Quart + Hypercorn（ASGI）
- 前端：`frontend/` 目录 Vue 3 CDN 单页，Hash 路由，视图模块在 `frontend/js/pages/`
- 端口：**8800**
- 登录：**admin** / **123456**（Cookie：`hengchi_session`）

## 主链

1. 装载品种与 K 线样本  
2. 登记策略参数匣  
3. 跑回测批（权益点入库）  
4. 仿真开平仓  
5. 风控尺拦截超额  
6. 盈亏日结  

## 本地运行

```bash
cd backend
pip install -r requirements.txt
hypercorn app.main:app --bind 0.0.0.0:8800
```

浏览器打开 http://127.0.0.1:8800/login

## Docker

```bash
docker compose up --build
```

## 测试

```bash
cd backend
pip install -r requirements.txt
pytest ../tests -q
```