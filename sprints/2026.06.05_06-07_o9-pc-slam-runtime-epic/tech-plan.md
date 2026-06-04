# Tech Plan: O9 PC + SLAM Runtime Epic

## sprint_type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：O9，约 18%。
2. 本 sprint 是否针对最低 Objective：是。
3. 理由：本轮直接推进 O9 的 PC 同源 fresh proof 可读性和 SLAM `/map` / continuous radar runtime root cause，不消费 O5/O6 支线。

## 最近两轮 blocker 防重复

- `04-05`：Product 已判定不能继续 Micro-only status/readback。
- `05-06`：PC 缺 hz、TF、`runtime_summary_fallback`、continuous not_proven 全字段展示和 live smoke；Robot Software 缺 continuous radar 和 SLAM `/map` artifact。
- 本轮防重复：不得只重复 05-06 `/api/radar/status` / latest proof；必须交新字段展示、live smoke、map/radar runtime evidence 或 root cause。

## 并行 owner 与文件范围

### Full-stack Software Engineer

允许改动：
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/tech-done.md`

验收命令范围：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm test -- --run test/App.test.ts
PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
curl -fsS -X POST http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/refresh
```

最低证据：PC same-origin response/UI 显示 hz、TF、`runtime_summary_fallback_used`、fresh proof、`continuous_scan_status=not_proven`、blockers；live smoke 失败也必须写 root cause。

### Robot Software Engineer

允许改动：
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/src/ros2_trashbot_bringup/`
- `onboard/src/ros2_trashbot_nav/`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `docs/navigation/`
- `sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/tech-done.md`

验收命令范围：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; curl -fsS -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh; echo; curl -fsS http://127.0.0.1:8787/api/radar/status; echo; curl -fsS http://127.0.0.1:8787/api/map/list || true; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest || true; echo; timeout 5 ros2 topic echo --once /map || true; timeout 5 ros2 topic echo --once /scan || true'
python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
python3 -m compileall -q onboard/scripts onboard/src
```

最低证据：新的 SLAM `/map` lifecycle / map artifact / radar continuity evidence，或明确 root cause；不能只复读 05-06 latest proof。

## 证据边界

- 可计：`robot_runtime_material`、`software_guard`、`blocked_with_root_cause`。
- 不可声明：continuous radar ready、SLAM map usable、AMCL/Nav2 ready、PC WASD、WAVE ROVER ACK、HIL、`safe_to_control=true`、真实送达。

## 本阶段 Product 验收命令

```bash
test -f sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/pre_start.md && test -f sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/prd.md && test -f sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/tech-plan.md
```

```bash
grep -n "sprint_type: epic\|OKR 最低优先级核对\|O9\|PC 同源\|runtime_summary_fallback\|SLAM\|/map\|root@192.168.1.11" sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/*.md
```

```bash
git diff --check -- sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic
```
