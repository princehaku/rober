# PC 地图彩色工程层

## Sprint 类型

sprint_type: micro

## 实际改动

- 上车 `/api/map/preview` 新增 `color_overlay`：从真实 PGM 解析占用边界点和疑似柱状障碍点，保持只读，不启动 ROS2 runtime、不发送底盘命令。
- PC Node map preview proxy 新增彩色层合同、默认 fail-closed 同形返回和顶层短字段。
- Vue 普通地图和右上角完整态势小窗新增彩色 SVG overlay；`当前画布` 状态条新增 `障碍层` chip。
- 文档同步说明：边界/柱子来自静态 PGM；Nav2 costmap 当前未接入真实 topic 时显示 `not_loaded`，不伪造。

## 验证结果

- 通过：`python3 -m unittest onboard/scripts/test_upper_robot_api_free_roam.py`，15 tests passed。
- 通过：`npm test -- test/catalog.test.ts --run`，196 tests passed。
- 通过：`npm test -- test/App.test.ts --run`，244 tests passed。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 通过；仅保留既有 chunk size 提示。
- 通过：`git diff --check`，无空白错误。
- 通过：远端上车 `ssh root@192.168.1.11 -p 37878 'cd /root/rober && python3 -m unittest onboard/scripts/test_upper_robot_api_free_roam.py'`，15 tests passed。
- 通过：远端 8787 已重启为新脚本，`GET http://192.168.1.11:8787/api/map/preview` 返回 `color_overlay.status=loaded`、`occupied_boundary_count=45`、`pillar_candidate_count=2`、`nav2_costmap_status=not_loaded`。
- 通过：本机 PC 7001 已重启，`GET http://127.0.0.1:7001/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`；`GET /api/robot-control/map/preview` 返回 `map_color_overlay_status=loaded`、边界 45、柱子 2。

## 剩余风险

- Nav2 costmap 真实 topic/artifact 尚未接入 `/api/map/preview`，本轮只把合同和 PC 渲染位留好；页面会明确显示 `nav2_costmap_status=not_loaded`。
