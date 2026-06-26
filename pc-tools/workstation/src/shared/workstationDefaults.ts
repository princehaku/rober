// Node/Express 是现场访问入口，必须避开 Clash 常用端口并固定给局域网使用。
export const WORKSTATION_PUBLIC_HOST = "0.0.0.0";
export const WORKSTATION_NODE_PORT = 7001;

// Vite 只服务开发热更新页；单独占 7002，避免和正式 Node 入口抢同一个端口。
export const WORKSTATION_DEV_PORT = 7002;
export const WORKSTATION_DEV_API_PROXY_TARGET = `http://127.0.0.1:${WORKSTATION_NODE_PORT}`;
