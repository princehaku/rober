# PC keyboard plain hold-stop summary

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 的 `safe_command_boundary` 新增：
  `keyboard_hold_to_move_plain`、`keyboard_stop_triggers_plain`、`keyboard_pulse_timing_plain`。
- 外部脚本和普通面板现在可以直接展示键盘连续手控的白话边界：必须按住才移动、只启用键盘不发车、松开/失焦/切页/换方向/点停止都会停，以及当前 0.26s/0.24s 短脉冲节奏。
- 前端 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "summary"`
  - `Test Files 1 passed (1)`
  - `Tests 44 passed | 114 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 summary 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回：
    `keyboard_control_status=start_ready`、`keyboard_control_start_ready=true`、
    `keyboard_hold_to_move_plain=必须按住 W/A/S/D 或方向键才会连续低速移动；只启用键盘但不按方向不会发车。`、
    `keyboard_stop_triggers_plain=松开按键、窗口失焦、页面隐藏、切换方向或点击停止都会发送停止请求。`、
    `keyboard_pulse_timing_plain=按住时约每 0.26 秒发送一次 0.24 秒低速脉冲。`、
    `keyboard_stop_triggers=key_released,window_blur,page_hidden,direction_changed,button_stop`、
    `keyboard_control_enabled=false`、`safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补只读安全边界说明，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实键盘连续手控 HIL 验证。
