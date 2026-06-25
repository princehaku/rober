# PC 扫地式建图向导 Micro Sprint

- sprint_type: micro
- owner: full-stack-software-engineer
- started_at: 2026-06-25 15:29 CST
- finished_at: 2026-06-25 15:32 CST
- scope: PC 普通用户首屏新增“扫地式建图”向导，把建图启动、键盘低速扫图、停止和保存串成可理解流程；不新增无人值守自动运动。

## 设计边界

- 设计文档：[pc_free_roam_mapping_design.md](../../docs/product/pc_free_roam_mapping_design.md)
- 本轮实现“受控扫图向导”，不是无人值守自动探索。
- 启动建图仍只走固定 `/api/robot-control/map/start`。
- 保存地图仍只走固定 `/api/robot-control/map/save`。
- 移动仍复用既有键盘连续手控 gate，保持低速、短时、按住才走、松开即停。
- 停止按钮继续走固定 `/api/robot-control/base/stop`，不依赖扫图确认勾选。
- 浏览器不新增 `/cmd_vel`、任意 Robot API 代理、串口、ROS 参数或自动 Nav2 目标入口。

## 实际改动

- `docs/product/pc_free_roam_mapping_design.md`
  - 新增 PC 扫地式建图向导设计，写清当前阶段、用户流程和后续全自动探索要求。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通用户首屏新增“扫地式建图”卡片。
  - 新增安全确认勾选；未勾选时建图启动和保存不可用。
  - 新增建图启动、启用键盘扫图、停止、保存当前地图四个动作入口。
  - 卡片状态根据连接、建图动作、保存动作和键盘 gate 显示“待确认 / 可开始 / 扫图中 / 待手控 / 已保存”等普通用户文案。
- `pc-tools/workstation/test/App.test.ts`
  - 更新首屏卡片数量断言为 6。
  - 增加扫地式建图卡片存在、未勾选时启动不可用、页面加载不调用 `/api/robot-control/map/start` 的断言。

## 验证结果

- `cd pc-tools/workstation && npm test`
  - 通过：2 个 test files，154 个用例全部通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过：ESLint 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部通过。
- PC 端 `screen -dmS rober-pc-7001 ... npm run api:public`
  - 通过：Node API 监听 `0.0.0.0:7001`，最终进程 PID 为 `49712`。
- 浏览器 DOM smoke：`http://127.0.0.1:7001`
  - 通过：普通用户首屏加载成功，默认小车地址为 `192.168.1.11:8787`。
  - 通过：“扫地式建图”卡片可见。
  - 通过：未勾安全确认时，“开始扫地式建图”“启用键盘扫图”“保存当前地图”均为 disabled。
  - 通过：停止按钮可见且保持可用；本轮没有点击它。
  - 通过：真实地图仍显示为“地图可见”。

## 剩余风险

- 本轮没有触发真实 `/api/map/start`、`/api/base/manual`、`/api/base/stop`、`/cmd_vel` 或无人值守自动探索。
- 真正“像扫地机一样自己跑”的全自动探索仍需要上车端状态机、LiDAR 避障、watchdog、覆盖策略、运行 artifact 和 HIL 验证。
- 当前 PC 向导把用户流程串起来，但移动能力仍依赖既有键盘连续手控 gate 是否满足。
