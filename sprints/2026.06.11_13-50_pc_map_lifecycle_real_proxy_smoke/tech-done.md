# PC Map Lifecycle Real Proxy Smoke

sprint_type: micro

## 实际改动

本轮未改 PC 产品代码、测试代码、普通首屏组件、样式、onboard 产品代码或硬件配置。新增/更新内容：

- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/run_map_lifecycle_smoke.mjs`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/pc_plain_user_home_dom_smoke.test.ts`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/vitest.dom-smoke.config.ts`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/*.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/cleanup_ssh_process_device_check.txt`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/hardware/board_sensor_stack_smoke.md`

用户旅程变化：普通用户首屏不变，仍是 `Rober 小车控制台` 和五张普通卡片；高级诊断里的固定 map lifecycle 入口已由真实上位机代理 smoke 证明可以触发 list/start/save/list，不再只是静态入口。

## 真实 PC Proxy Smoke

临时 workstation API：`http://127.0.0.1:18790`

真实上位机：`http://192.168.1.11:8787`

map_name：`pc_map_lifecycle_20260611_1350`

执行结果：

- `01_map_list_before.json`：HTTP 200，`proxy_status=lifecycle_forwarded`，远端 `/api/map/list`，`remote_http_status=200`，`map_count=22`。
- `02_map_start.json`：HTTP 200，远端 `/api/map/start`，body 只有 `map_name`，`command_result.mode=map_lifecycle_proof_helper`，`executed=true`，`ok=true`。
- `03_map_save.json`：HTTP 200，远端 `/api/map/save`，同一 `map_name`，`command_result.executed=true`，`ok=true`。
- `04_map_list_after.json`：HTTP 200，`map_count=24`，包含 `pc_map_lifecycle_20260611_1350.yaml`。
- `05_map_save_unknown_field_reject.json`：HTTP 400，`proxy_status=lifecycle_rejected`，`failure_reason=request_body_unknown_fields:arbitrary_endpoint`，`remote_http_status=null`。
- `06_map_reset_not_attempted.json`：reset 记录为 `not_attempted_by_safety_boundary`，未做 destructive reset。

固定代理结论：浏览器/请求不能任意路径透传；未知字段没有到达上位机。`/api/base/manual` 未调用，`/cmd_vel` 未发布。

## 首屏边界验证

命令：

```bash
./pc-tools/workstation/node_modules/.bin/vitest run --config sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/vitest.dom-smoke.config.ts
```

结果：

```text
Test Files  1 passed (1)
Tests  1 passed (1)
```

artifact：`artifacts/pc_plain_user_home_dom_smoke.json`

结论：`.simple-user-console` 存在，标题包含 `Rober 小车控制台`，五卡片为 `小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。默认可见首屏未出现 `开始建图`、`保存地图`、`HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`检查路径`。高级诊断保持默认关闭，并保留 `开始建图（高级）`、`保存地图`、`地图列表`。

## 安全边界

本轮是 no-motion map lifecycle evidence capture：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `sends_motion_commands=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

硬件资料来源：`docs/vendor/VENDOR_INDEX.md`。本轮只记录真实上位机 readback 中的 `/dev/ttyS5` 和 `/dev/ttyACM0`；不把它们外推为 Orange Pi 通用默认，不改串口、波特率、WAVE ROVER 或 ESP32 配置。

## Cleanup

- 已停止本轮临时 workstation API，`127.0.0.1:18790` 无监听。
- 上位机 `/api/status` 可读，`upper_robot_api.py --port 8787` active。
- SSH 只读检查 `root@192.168.1.11:37878` 未发现长期 map/slam/Nav2/helper 残留；匹配输出只包含本次检查命令自身。
- `/dev/ttyS5` 和 `/dev/ttyACM0` 的 `fuser` 无占用输出。

## 验证结果

- `git diff --check`：通过。
- 未改 PC 产品代码/测试代码，因此未运行 `npm run build`、`npm run test -- --run`、`npm run lint`。
- 真实 PC proxy map lifecycle smoke：通过，原始响应见 `artifacts/01_map_list_before.json` 到 `artifacts/05_map_save_unknown_field_reject.json`，汇总见 `artifacts/map_lifecycle_smoke_summary.json`。
- 首屏 DOM smoke：通过，见 `artifacts/pc_plain_user_home_dom_smoke.json`。
- Cleanup：通过，见 `artifacts/cleanup_summary.json` 和 `artifacts/cleanup_ssh_process_device_check.txt`。

## 剩余风险

本轮不证明地图质量、AMCL 定位、Nav2 可行驶、真实路线执行、真实运动、HIL pass、delivery success 或普通用户可以安全发车。`start/save` 的 `executed=true` 只代表上位机 no-motion map lifecycle helper 执行并产出地图材料；reset 未测是刻意安全边界。
