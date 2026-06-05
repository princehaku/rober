# Side2Side Check: O10 Delivery Readiness Path Contract Epic

## 验收时间

- 2026-06-05 12-13 CST

## PRD 对照

| PRD 验收项 | 本轮证据 | 判定 |
| --- | --- | --- |
| 路径契约：refresh/latest 读写同一个 canonical path，暴露 legacy/compat 边界 | 8787 `POST /api/map/proof/refresh` 与 `GET /api/map/proof/latest` 均指向 `/root/rober/onboard/runtime/map_lifecycle_latest.json`；legacy `/root/rober/runtime/map_lifecycle_latest.json` 仅作为 `legacy_exists=true` / compatibility。 | Pass |
| 本地护栏：upper API/map proof 相关 unittest、compileall、diff-check | Robot Software 35 tests OK、compileall 通过、diff-check 通过；指定的 `test_o3_map_lifecycle_proof.py` 不存在，已记录为验证缺口。 | Partial Pass |
| 远端 readback：同一链路显示 canonical latest、latest endpoint、map artifact | 远端 8787 refresh/latest HTTP 200，latest proof `map_once_artifact_metadata_observed`，canonical map artifacts 在 `/root/rober/onboard/runtime/maps`。 | Pass |
| PC 消费边界：PC API/按钮契约显示 latest/path/fail-closed | 新增 `GET /api/o7/direct-upper/map/proof/latest`，8788 status/scan latest/map latest curl 通过；未做浏览器点击/Playwright。 | Partial Pass |
| HIL/elevator 边界：无现场安全/图片材料时只写 blocker | Algorithm 写明 AMCL/Nav2 和电梯 field eval blocked；Hardware 写明 stop-first HIL blocked。 | Pass |

## O10 Delivery-Readiness Chain

| Chain 段 | 当前状态 | 证据边界 | 下一步 |
| --- | --- | --- | --- |
| Path Contract Lock | pass | `robot_runtime_material`：canonical latest JSON `/root/rober/onboard/runtime/map_lifecycle_latest.json`，canonical map artifacts `/root/rober/onboard/runtime/maps`，legacy only compatibility。 | 用 canonical latest 指向的真实 map artifact 进入 map quality 与 AMCL/Nav2 readiness。 |
| AMCL/Nav2 Readiness | blocked | no-motion `/map` once 与 PGM/YAML 是前置材料；尚无 AMCL `/initialpose`、lifecycle active、planner/controller 或 route dry-run。 | 准备同一 `map` frame waypoint manifest，先跑 map quality，再做 no-motion AMCL/Nav2。 |
| PC Button Workflow | partial | same-origin API readback 已过，浏览器点击/Playwright 未做；仍是 software guard/API readback。 | 用浏览器按钮触发 map proof latest/refresh/localize 控件并截图或日志留证。 |
| Elevator Image Eval | blocked | 只有 fixture/template/blocker，没有真实/受控图片 manifest。 | 采集真实/受控电梯图片 manifest，跑 OpenCV field eval。 |
| Stop-First HIL Gate | blocked | 缺现场看护、净空、急停/断电和 CEO/现场授权；`safe_to_control=false`。 | CEO/现场确认安全前提后再做低速 pulse + stop/post-status。 |

## 不可外推项

- `map_once_artifact_metadata_observed` 不等于地图可导航。
- canonical path contract 不等于 AMCL/Nav2 ready。
- PC API curl 通过不等于 browser/user acceptance，也不等于 PC WASD 控车。
- `legacy_exists=true` 只代表旧文件仍存在，不代表 latest readback 继续依赖旧路径。
- 本轮没有 HIL、robot ACK、`T=1001` 同场材料、真实电梯图片、真实送达或 production cloud。

## Product 判定

本轮达到 O10 第一段 readiness 前置条件：Path Contract 已从 08-09 的路径漂移风险变成 canonical onboard runtime 合同。它可以作为下一轮 AMCL/Nav2 readiness、PC browser workflow 和 delivery-readiness chain 的起点。

本轮未达到用户验收材料：无浏览器点击、无真实手机/PC 操作验收、无现场低速 HIL、无真实电梯图片、无送达任务。因此 O10 只能小幅从 0% 调到约 7%，不能写成 delivery ready 或 delivery success。
