# 上车 API 轻量活性探针

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py` 同时暴露 `GET /api/health` 和兼容 `GET /health`，复用轻量 health 回包，避免 PC 只能依赖重聚合 `/api/status` 判断上车 API 是否在线。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 把 `/api/health` 加为第一个 Robot API 只读端点，用于区分“API 进程在线但重状态端点退化”和“API 整体不可达”。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/catalog.test.ts` 和 `onboard/scripts/test_upper_robot_api_free_roam.py` 同步 health readback 合同与测试。
- `docs/product/pc_tools_workstation.md` 记录轻量 health 探针合同；同时确认 PC 地图主工具仍是 `/map` 大地图，ROS2 配套只用于工程观察。

## 验证结果

- 通过：`python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam.UpperRobotApiFreeRoamTest.test_upper_robot_api_exposes_api_health_route_constant`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "reads fast endpoints|7071|Robot Control summary proxies Robot API"`，1 file passed，3 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|map display|ROS2"`，1 file passed，3 tests passed，确认 `/map`、地图显示合同和 RViz2/Foxglove 配套说明仍存在。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：已同步 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py` 并重启 `trashbot-upper-robot-api.service`；上车本机 `GET http://127.0.0.1:8787/api/health` 与 `GET http://127.0.0.1:8787/health` 均返回 `schema=trashbot.upper_robot_api.v1.health`、`status=ready`、`safe_to_control=false`，服务状态 `active`。
- 通过：Mac 侧 `GET http://192.168.1.11:8787/api/health` 返回 `status=ready`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `57099`；`GET http://127.0.0.1:7001/api/health` 返回 PC health，`HEAD http://127.0.0.1:7001/map` 返回 `200`，`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 的第一个 `read_endpoints[0]` 为 `{id: health, endpoint: /api/health, http_status: 200, request_status: loaded, schema: trashbot.upper_robot_api.v1.health}`，地图合同仍为 `/map`、默认 `100%`、最高 `2400%`、ROS2 tools 为 `rviz2,foxglove`、`sends_motion=false`、`starts_ros2=false`。

## 剩余风险

- 本轮没有执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`；真实运动闭环仍需现场安全确认后验证。
- `/api/health` 已部署并通过上车本机与 PC 7001 smoke；PC summary 连接总状态仍为 `degraded`，说明还有重状态/部分证明端点需要后续继续定位，并需持续观察 8787 后续是否再出现 OOM/restart。
- 相机首帧、真实地图刷新质量、自动驾驶同窗口 wheel L/R 非零和 delivery success 仍是后续现场验收项。
