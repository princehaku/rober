# PC 慢底盘反馈读数保留

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `/api/base/status` 继续使用 2.4 秒 summary 短窗口，避免 fresh 串口读数拖住普通首屏。
  - `/api/base/feedback-samples/latest` 改用 8 秒 summary 窗口；该端点只读 `/esp32_bridge` 已落盘反馈样本，不发送控制，适合作为 wheel raw L/R 慢读证据。
  - 只读端点顺序调整为先读 `base_feedback_samples_latest`、再读 `base_status`，避免真实上位机单 worker 先卡 fresh `base/status`，导致已落盘 latest samples 排队到 8 秒超时。
- `pc-tools/workstation/src/server/index.ts`
  - HTTP `/api/robot-control/summary` 显式传入 2.4 秒全局快预算，保持普通首屏响应；慢读证据只留给内部 builder/独立刷新路径。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增慢读回归：`base/status` 3 秒超时仍为 `fetch_failed`，但 `feedback-samples/latest` 3 秒返回后必须进入 base summary，并显示 wheel raw L/R、T=1001 计数和 `feedback_link_status`。
- `docs/product/pc_tools_workstation.md`
  - 同步说明慢读边界：读得慢不等于没有 wheel 证据；latest samples 只读不发车。

## 验证结果

- `npm test -- test/catalog.test.ts -t "slow feedback samples available|derives latest wheel L/R"`：通过，2 passed。
- `npm test -- test/catalog.test.ts -t "summary route caps slow base readback|slow feedback samples available"`：通过，2 passed。
- `npm test -- --run`：通过，2 个测试文件、394 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BrleZEDU.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- live 7001 HTTP 首屏 summary：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 HTTP 200，`console_status=loaded_fail_closed_summary`、`connection=degraded`、`base_status=fetch_failed(fetch_timeout_2400ms)`、`feedback_latest=loaded`、`safe_to_control=false`。
- live 内部慢读 builder：`base_status=fetch_failed(fetch_timeout_2400ms)`、`feedback_latest=loaded`、`latest_feedback_status=loaded`、真实样本 `latest_t1001_observed_count=0`、`wheel_feedback_lr_nonzero_proven=false`、`feedback_link_status=not_observed`、`safe_to_control=false`。
- 7001 重启：最新代码已监听 `0.0.0.0:7001`。

## 剩余风险

- 本轮只改 PC Node summary 的只读聚合窗口，不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- 若真实 `/api/base/feedback-samples/latest` 超过 8 秒仍未返回，PC 仍会显示 fetch timeout，需要继续查上车端 artifact 读取性能或拆成缓存化端点。
