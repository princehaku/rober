# PC Nav2 Readback Runtime Autostart Plain

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - Nav2 readback 现在从 `/api/nav2/status` 消费 `lifecycle_running/lifecycle_state` 和 `nav2_lifecycle_not_running`，在图上路线 ready 时把 managed execute 的事实写入 `next_action_plain`、`route_execution_precheck_plain` 和轮速复验下一步。
  - 顶层 `current_fact_plain` 改为优先消费 `readback_summary.nav2.plain_hint`，让普通首屏和外部脚本同时看到“当前状态”和“下一步”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 managed runtime 可启动场景断言，锁定 Nav2 readback 和 `current_fact_plain` 都显示“执行时会自动启动自动驾驶 runtime”。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明该变化只修正只读 summary/首屏文案，不执行 Nav2 goal、不启动 runtime、不发送底盘或自由移动命令。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "managed runtime can start lifecycle|wheel raw|current_fact"`
- 已通过：`npm --prefix pc-tools/workstation test`，结果 `375 passed`。
- 已通过：`npm --prefix pc-tools/workstation run build`，Vite 仍只有既有 chunk size warning。
- 已重启本机 PC API 到 `0.0.0.0:7001`，当前监听进程为 `node` PID `62316`。
- 已只读验证真实上车 `http://192.168.1.11:8787`：
  - `GET /api/robot-control/summary` 的 `readback_summary.nav2.next_action_plain` 返回“勾选行程前安全确认后用 ROS 模式重跑图上路线；执行时会自动启动自动驾驶 runtime，并在同窗口确认轮速 L/R 非零。”
  - `current_fact_plain` 的自动驾驶段也包含同一下一步。
  - `GET /api/robot-control/map/preview` 仍显示地图、图上路线和小车位置已显示，雷达 `radar_overlay_status=not_current`，旧来源点 81 个不贴到当前地图。

## 剩余风险

- 本轮没有执行 Nav2 goal、键盘手控、free-roam start/stop、radar start/stop 或 `/cmd_vel`；真实完整路线 wheel L/R 非零仍需要现场勾选安全确认后执行验证。
- live 相机仍是 UVC 无首帧且不是页面独占；雷达当前 stopped/stale，地图 marker 正确不贴旧点。这两个硬件/运行态缺口仍影响建图验收，不阻止本轮只读文案改进。
