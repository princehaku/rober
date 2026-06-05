# Tech Plan: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：O9，约 18%。
2. 本 sprint 是否针对最低 Objective：是。
3. 理由：本轮直接推进 O9 的两个真实材料断点：PC same-origin live smoke 和 SLAM `/map` lifecycle runtime proof；不消费 O5/O6 支线，不继续 Micro-only status/readback。

## 最近两轮 blocker 防重复

| 最近 sprint | 已消费 blocker | 本轮处理方式 |
| --- | --- | --- |
| `05-06_o9-narrow-runtime-material-epic` | PC 缺 live smoke；Robot 缺 continuous radar 和 SLAM `/map` artifact。 | Full-stack 必须交 8788 live curl；Robot Software + Algorithm 必须交 `/map` lifecycle proof 或更窄 root cause。 |
| `06-07_o9-pc-slam-runtime-epic` | PC blocked at `tsx_ipc_pipe_enotsup`；远端 ROS graph 无常驻 LiDAR/SLAM runtime，map proof artifact missing。 | Full-stack 首先验证 `TMPDIR=/tmp`；Robot Software + Algorithm 直接执行 no-motion LiDAR+SLAM proof，不再只查 `/api/radar/status`。 |

红线判断：本轮不是第三次复述旧 blocker，而是按上一轮 root cause 做修复和 runtime proof。若本轮仍失败，`final.md` 必须判断是否升级 CEO 决策或切换 O9 抓手。

## 并行执行结构

本轮是 2 条真实并行工作：

1. Full-stack 单线闭环 PC live smoke。
2. Robot Software 主责 + Robot Algorithm 配合的 no-motion `/map` lifecycle proof。

两个 owner 文件范围互不重叠，验收证据可独立产出，必须并行启动；主节点和 Product 不改产品代码。

## Owner 1: Full-stack Software Engineer

### 目标

修 PC `npm run api` live smoke 启动问题，并完成 `8788 -> 8787` same-origin scan-proof refresh curl 证据。

### 允许文件范围

- `pc-tools/workstation/package.json`
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md`

### 实现约束

- 首选验证 `TMPDIR=/tmp` 是否解决 `tsx_ipc_pipe_enotsup`。
- 如果 `TMPDIR=/tmp` 不解决，允许补一个不依赖 Windows temp IPC pipe 的 API smoke 启动脚本或命令，但不得扩大 UI 功能面。
- 必须保留 fresh proof 与 continuous not_proven 的分离，不得把 once proof 包装成 continuous radar ready。
- 技术注释如需新增，必须使用中文，并解释为什么这样处理 WSL/tsx/IPC 边界。

### 验收命令

```bash
cd pc-tools/workstation && npm run build
```

```bash
cd pc-tools/workstation && npm test -- --run test/App.test.ts
```

```bash
cd pc-tools/workstation && TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

在 8788 API 启动后，另一个 shell 运行：

```bash
curl -fsS -X POST http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/refresh
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
```

### 必须产出的证据

- `npm run api` 是否仍触发 `tsx_ipc_pipe_enotsup`。
- 8788 same-origin refresh curl 结果。
- 8787 upper target：`http://192.168.1.11:8787`。
- fresh proof、hz、TF、`runtime_summary_fallback_used`、`continuous_scan_status=not_proven`、blockers。
- 若失败，必须给出新的 root cause 和下一步 patch 入口。

## Owner 2: Robot Software Engineer + Robot Algorithm Engineer

### 目标

执行 no-motion LiDAR+SLAM `/map` lifecycle proof，目标是 `/map` once、map artifact、metadata、`runtime/map_lifecycle_latest.json` 和 `/api/map/proof/latest` readback。

### Robot Software 允许文件范围

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o3_map_lifecycle_proof.py`
- `onboard/scripts/`
- `onboard/src/ros2_trashbot_bringup/`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `docs/navigation/`
- `sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md`

### Robot Algorithm 允许文件范围

- `onboard/src/ros2_trashbot_nav/`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `docs/navigation/`
- `sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md`

### 实现约束

- 必须 no base motion。
- 禁止发布 `/cmd_vel`。
- Proof 必须包含 `safe_to_control=false`。
- Proof 必须包含 `sends_base_motion_commands=false` 和 `robot_control_executed=false`。
- 不得宣称 AMCL/Nav2 ready、map 可导航或 fixed-route 可跑。
- 如果需要 mock/stub，只能用于上层 API/readback，不得替代真实 `/map` once 的 runtime 目标；若真实 `/map` 失败，必须明确写成 `blocked_with_root_cause`。
- 技术注释如需新增，必须使用中文，解释为什么 no-motion、为什么不控车、为什么证据不能外推。

### 远端验收命令

先采集现场基线：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; ros2 topic list; curl -fsS http://127.0.0.1:8787/api/map/list || true; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest || true; echo'
```

执行 no-motion map lifecycle proof：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; timeout 8 ros2 topic echo --once /scan || true; timeout 12 ros2 topic echo --once /map || true; curl -fsS -X POST http://127.0.0.1:8787/api/map/proof/refresh || true; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest || true; echo; test -f /root/rober/onboard/runtime/map_lifecycle_latest.json && cat /root/rober/onboard/runtime/map_lifecycle_latest.json || true; find /root/rober/onboard/runtime/maps -maxdepth 2 -type f 2>/dev/null | sort | tail -n 20 || true'
```

本地软件护栏：

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

```bash
python3 -m unittest discover -s onboard/scripts -p 'test_*.py'
```

### 必须产出的证据

- `ros2 topic list` 中 `/scan`、`/map` 是否存在。
- `/scan` once 和 `/map` once 的结果或失败日志。
- map artifact 路径和 metadata。
- `runtime/map_lifecycle_latest.json` 内容。
- `/api/map/proof/latest` readback。
- 安全字段：`safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`。
- 若失败，必须归因到 LiDAR、SLAM、TF、map saver、upper API、文件路径、权限、ROS install/source、launch 或 topic remap 中的具体一项或多项。

## 接口影响

| 接口 | 本轮期望 | 边界 |
| --- | --- | --- |
| `POST /api/o7/direct-upper/radar/scan-proof/refresh` | PC 8788 same-origin 调 8787 成功或更窄失败 root cause。 | 不证明 continuous radar ready。 |
| `GET /api/o7/direct-upper/radar/scan-proof/latest` | PC 8788 readback latest proof。 | 不证明 PC 按钮 UI 已人工验收，除非 Full-stack 给浏览器材料。 |
| `POST /api/map/proof/refresh` | 上位机触发 no-motion map proof。 | 不发 `/cmd_vel`。 |
| `GET /api/map/proof/latest` | readback `runtime/map_lifecycle_latest.json`。 | 不证明 map 可导航。 |

## 证据边界

可计：

- `robot_runtime_material`：真实上位机 ROS2 runtime 中 `/map` once、artifact、metadata、proof latest。
- `software_guard`：PC live API smoke、same-origin refresh/readback、本地测试/build。
- `blocked_with_root_cause`：失败但 root cause 更窄且有日志。

不可声明：

- continuous radar ready。
- SLAM map usable for navigation。
- AMCL/Nav2 ready。
- PC WASD 已控车。
- WAVE ROVER ACK。
- HIL pass。
- `safe_to_control=true`。
- 真实送达或真实电梯识别。

## 风险

| 风险 | 影响 | 处理 |
| --- | --- | --- |
| `TMPDIR=/tmp` 仍无法修复 `tsx_ipc_pipe_enotsup` | PC 8788 live smoke 仍 blocked。 | Full-stack 必须给替代启动脚本或明确 Node/tsx/WSL root cause。 |
| 远端 ROS graph 仍没有 `/scan` | `/map` proof 无法启动。 | Robot Software 必须定位 LiDAR launch/runtime/source 问题，不能跳到 mock map。 |
| `/scan` 有但 `/map` 没有 | SLAM 或 TF lifecycle blocked。 | Algorithm 定位 SLAM package、TF、topic remap 或 launch 参数。 |
| map artifact 生成但 API latest 404 | upper API/readback 合同断。 | Robot Software 修 API route 或 latest JSON 写入路径。 |
| Proof 缺安全字段 | 证据不可验收。 | 必须补 `safe_to_control=false` 等字段再收口。 |

## Product 收口命令

计划阶段验收：

```bash
test -f sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/pre_start.md && test -f sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/prd.md && test -f sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-plan.md
```

```bash
grep -n "sprint_type: epic\|OKR 最低优先级核对\|O9\|PC\|same-origin\|TMPDIR\|SLAM\|/map\|root@192.168.1.11\|safe_to_control=false" sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/*.md
```

```bash
git diff --check -- sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic
```

实现收口时追加：

```bash
grep -n "8788\\|8787\\|same-origin\\|TMPDIR\\|tsx_ipc_pipe_enotsup\\|/map\\|map_lifecycle_latest.json\\|/api/map/proof/latest\\|safe_to_control=false" sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/side2side_check.md sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/final.md
```
