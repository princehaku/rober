# Full-Stack Software Engineer Owner Note

## sprint_type

sprint_type: epic owner note

## 用户触点目标和本轮抓手

- Objective: O7 PC 运营调试平台。
- 本轮抓手：验证并收口 PC same-origin `operator-report` 写入/回读链路，让 PC 可以通过现场默认 8787 回读真实上位机 operator report artifact。
- 安全边界：本轮只触达 `/api/operator/report`，不触发 `/api/base/manual`、`/cmd_vel`、串口、ROS2 driver、底盘运动或 LiDAR start。
- evidence_type: `robot_runtime_material` for operator-report artifact readback only；不证明 PC WASD、HIL、ACK、建图、定位或 delivery success。

## 实现和接口影响

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `GET /api/o7/direct-upper/operator-report`，只读回传上位机 latest operator report artifact。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - `operator-report` POST 允许使用现场默认 `http://192.168.1.11:8787`。
  - 新增 `proxyO7DirectUpperOperatorReportReadback()`，方法为 GET，路径固定 `/api/operator/report`。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 首屏文案同步为 radar/report 可使用 field default，base/map/localize 仍需要显式 env 或 fixture。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 operator report POST/GET 使用 field default，同时验证 map/localize 仍 fail closed。
- `docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`
  - 同步 PC direct-upper operator-report POST/GET contract 和安全边界。

## 验证结果

```bash
cd pc-tools/workstation && npm test -- --run
```

```text
3 files / 98 tests passed
```

```bash
cd pc-tools/workstation && npm run build
```

```text
Vite build completed, exit 0
```

```bash
cd pc-tools/workstation && npm run lint
```

```text
exit 0
```

只读 / operator-report smoke:

```bash
curl -i http://192.168.1.11:8787/api/operator/report
```

```text
HTTP/1.1 200 OK
readback_sends_commands=false
sends_base_motion_commands=false
uses_base_uart=false
starts_ros2=false
robot_control_executed=false
safe_to_control=false
```

```bash
git diff --check -- pc-tools/workstation docs/product docs/interfaces sprints/2026.06.04_20-21_runtime-material-followup
```

```text
passed with no output
```

## 失败定位

Full-Stack 验证无失败。当前 diff 没有打开 base/manual、`cmd_vel`、串口或运动链路。

## 剩余风险

- 只证明 O7 operator-report readback 的 PC/8787 artifact 路由可读。
- 不证明 PC WASD 控车、`/api/base/manual`、`/cmd_vel`、robot ACK、`T=1001`、HIL、map/localize runtime 或 delivery success。
- 仍需要 Robot Software 提供 fresh radar/map/localize ROS2 runtime material，Hardware 提供 stop-first HIL 前置条件后，O7 才能进入现场 operator workflow 验收。
