# PC 默认地址与键盘手控门禁

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将 PC 控制台小车地址默认固定为 `http://192.168.1.11:8787`，页面加载后直接读取默认上位机 summary。
  - 在高级诊断“现场点动设置 / 控制边界”增加键盘连续手控：W/A/S/D 与方向键按住后按 240ms 短脉冲重复调用固定 PC proxy，松开、失焦、页面隐藏或切换地址时发送 stop。
  - 键盘非 stop 点动复用现有 `canSendManualMotion` 门禁；operator HIL material 或 checklist 不满足时不发送 `/api/robot-control/base/manual`。
  - 修正 base feedback samples fallback 字段，失败态也包含 `wheel_feedback_lr_nonzero_proven`、左右轮速和来源字段。
- `pc-tools/workstation/src/styles.css`
  - 增加键盘手控状态样式，保持普通首屏不新增工程控制面板。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认地址、默认 summary query、键盘材料不全不发 manual、材料齐全按键发 240ms manual pulse、松开发 stop。
- `docs/product/pc_tools_workstation.md`
  - 同步记录默认地址、键盘手控门禁、真实 smoke 结果和未完成边界。

## 验证结果

- `cd pc-tools/workstation && npm test`
  - 通过，`Test Files 2 passed (2)`，`Tests 99 passed (99)`。
- `cd pc-tools/workstation && npm run build`
  - 通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- 真实 PC proxy smoke，默认上位机 `http://192.168.1.11:8787`：
  - summary：`normalized_base_url=http://192.168.1.11:8787`，`robot_api_connection.status=degraded`，`failed_count=1`，原因 `camera_health:fetch_timeout_4000ms`，`delivery_success=false`。
  - map list：`proxy_status=lifecycle_forwarded`，`map_usable_for_navigation=true`，`usable_map_count=1`。
  - base feedback samples：`completed_sample_count=3`，`t1001_observed_count=3`，`sends_motion_commands=false`，`wheel_feedback_lr_nonzero_proven=false`，`wheel_feedback_latest_left_speed=0`，`wheel_feedback_latest_right_speed=0`。
  - nav2 goal preflight：`preflight_status=preflight_rejected`，缺 `localization_runtime_or_reset_not_observed`、`path_generation_not_observed`、`path_point_count_not_positive`、`operator_report_preflight_required`，`robot_control_executed=false`，禁止端点未调用。
  - stop：`proxy_status=command_forwarded`，`status=stopped`，`robot_control_executed=false`。

## 剩余风险

- wheel raw L/R 非零仍未证明；当前真实只读样本继续显示左右轮速 `0/0`。本轮依据 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料，只读取 `T=130/T=1001` 反馈，不改串口或底盘协议。
- 完整 Nav2 路线执行仍未完成；当前预检缺定位 runtime/reset、路径生成、正路径点数和 operator report。
- delivery success 仍未证明；PC 顶层 `delivery_success=false`、`primary_actions_enabled=false` 保持不变。
- `ssh root@192.168.1.11 -p 37878` 可达，但本轮仅做 PC proxy smoke，未做 HIL 实车完整路线。
