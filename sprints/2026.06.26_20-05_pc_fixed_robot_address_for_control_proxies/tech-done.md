# PC Fixed Robot Address For Control Proxies

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `robotControlFixedProxyQueryBaseUrl()`，Robot Control 固定代理缺省 `baseUrl` 时统一使用 `http://192.168.1.11:8787`。
  - 覆盖 manual/first-jog/stop、feedback samples、operator report、radar/map/Nav2 refresh、Nav2 goal preflight/execute、delivery check/complete、localize reset、map lifecycle、free-roam autonomy start/stop、camera offer/close/first-frame probe。
  - 只替代小车地址输入；固定 endpoint 白名单、请求体白名单、确认项和上车端传感器门禁不变。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增无 query 的 `POST /api/robot-control/free-roam/autonomy/start` 测试，证明 PC Node 会默认转到 `http://192.168.1.11:8787/api/free-roam/autonomy/start`。
  - 测试同时锁定相机首帧未证明时仍返回 `camera_first_frame_not_observed`，不写运动解锁参数。
- `docs/product/pc_tools_workstation.md`
  - 记录固定小车地址默认策略和安全边界。

本轮继续不调用 subagent；CEO 已明确要求去掉 subagent 调用。

## 验证结果

- `npm test -- catalog.test.ts`
  - 103 tests passed。
- `npm test`
  - 238 tests passed。
- `npm run build`
  - TypeScript 与 Vite build passed；保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 53521。
- Live readback：
  - 无 query 的 `POST http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/start` 返回 `source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`，证明固定小车地址已生效。
  - 同一响应仍被上车端以 `camera_first_frame_not_observed` 拒绝，`sets_state_machine_parameters=false`、`motion_unlock_requested=false`、`robot_control_executed=false`。
  - 无 query 的 `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 返回 `source_base_url=http://192.168.1.11:8787`、`shared_capture=true`、`exclusive_camera_claim=false`。

## 剩余风险

- 这轮只修 PC 代理默认地址，不证明 Nav2 完整路线已能跑通。
- 默认地址减少了操作步骤，但自动扫图/手控/导航仍依赖现场确认、上车端 readiness 和真实硬件状态；当前 live camera 仍未证明首帧，wheel raw L/R 仍为 `0/0`。
