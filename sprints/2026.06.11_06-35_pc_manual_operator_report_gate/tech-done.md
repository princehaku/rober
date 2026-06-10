# PC Manual Operator Report Gate

## sprint_type

micro

## 实际改动

- 在 workstation Node 代理中把 `POST /api/robot-control/base/manual?baseUrl=...` 的非 stop 点动升级为双门禁：`confirm_hil_checklist=true` 后，仍必须短超时读取上位机最新 `GET /api/operator/report`，并从顶层或 `latest_result.operator_report` 消费结构化现场材料。
- 新增 `operator_report_preflight` 响应合同，返回 `/api/operator/report` HTTP、report status、evidence ref、缺失字段、危险字段与材料摘要；材料不满足时本机返回 HTTP 400 `command_rejected` / `failure_reason=operator_report_preflight_required`，不调用远端 `/api/base/manual`。
- 保留 stop fail-safe 路径：`POST /api/robot-control/base/stop?baseUrl=...` 不要求 operator report 材料，响应中显式标记 `operator_report_preflight.status=not_required_for_stop`。
- PC 首屏保持普通用户五卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`，新增普通话术 `现场材料：未满足/已满足`；具体缺失项、HIL/report/preflight/material/manual gate detail 只在默认关闭的 `高级诊断`。
- 同步更新 `docs/product/pc_tools_workstation.md`，硬件边界引用 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 是 UART newline-delimited JSON，vendor Raspberry Pi 默认 `/dev/ttyAMA0 @ 115200`，项目上车 Orange Pi 不能硬编码串口；workstation 只走上位机 HTTP，不直接操作 UART。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite 构建完成。
- `cd pc-tools/workstation && npm run test`：通过，2 个测试文件、87 个用例全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过。
- Browser/DOM smoke：通过，证据 `artifacts/browser_dom_smoke_2026-06-11.json`。关键字段：`title=Rober 小车控制台`、`first_screen_card_count=5`、五张卡片为 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`、`first_screen_forbidden_hits=[]`、`advanced_details_open=false`、高级诊断包含 `operator report preflight`、现场材料与 manual gate detail。
- 真实上位机 no-motion smoke against `http://192.168.1.11:8787`：通过，证据 `artifacts/remote_no_motion_manual_gate_2026-06-11.json`。关键字段：`manual_http_status=400`、`proxy_status=command_rejected`、`failure_reason=operator_report_preflight_required`、`operator_report_preflight.status=blocked`、`operator_report_preflight.request_status=loaded`、`operator_report_preflight.http_status=200`、缺失 `external_video_recorded / visible_content_proven / wheel_feedback_lr_nonzero_proven / physical_motion_lidar_delta_proven`，`remote_http_status=null`，证明本机拒绝且未调用远端 `/api/base/manual`。同时 stop smoke 返回 `stop_http_status=200`，`stop_body.robot_control_executed=false`。

## 剩余风险

- 本轮只硬化 PC Node 代理门禁和 UI/合同；真实非零运动仍未执行，也不能把材料齐全解释为 HIL pass 或 safe-to-control。
- `/api/operator/report` 的现场材料真实性仍依赖真实 operator 上传的视频、相机 artifact、轮速反馈和 LiDAR delta 引用；PC 只做结构化消费与本机拒绝，不验证文件内容本身。
- `real_route_map_proven` 已记录但不阻塞纯手动点动，后续自动导航/路线执行门禁需要单独升级。

## 当前运行时间

2026-06-11 06:43:52 CST
