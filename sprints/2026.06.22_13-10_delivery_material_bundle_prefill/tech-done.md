# Delivery material bundle prefill

## sprint_type

micro

## 实际改动

- PC 高级诊断的送达材料快捷表单新增“预填送达材料（高级）”。
- 该按钮顺序复用固定代理：
  - `GET /api/robot-control/nav2/goal/execution/latest` 读取最近 Nav2 goal execution `evidence_ref`。
  - `POST /api/robot-control/camera/first-frame/probe` 读取 camera first-frame `sample_path`。
  - `GET /api/robot-control/delivery/latest` 刷新当前 delivery gate 缺口。
- UI 自动预填 `route/map ref`、`delivery_evidence_ref`、`operator evidence ref` 和“送达视频 ref”。
- 不提交 `/api/operator/report`，不调用 `/api/delivery/complete`，不替现场人员勾选送达确认，不声明 observed motion/stop 或 delivery success。
- `pc-tools/workstation/test/App.test.ts` 增加回归，确认一键预填只访问上述固定 latest/probe endpoint，不提交 claim。
- `docs/product/pc_tools_workstation.md` 同步记录组合预填行为和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`104 passed (104)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：三段固定代理均可读取真实上位机材料：
  - Nav2 latest：HTTP 200，`proxy_status=latest_loaded`，`evidence_ref=o11-nav2-goal-execution-1782099547218`，`status=goal_succeeded`，`result_status=succeeded`。
  - Camera first-frame probe：HTTP 200，`proxy_status=probe_forwarded`，`status=frame_read`，`sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782102542240.jpg`，`read_ok=true`，`visible_content_proven=true`，`delivery_success=false`，`robot_control_executed=false`。
  - Delivery latest：HTTP 200，`proxy_status=latest_loaded`，`status=blocked_missing_delivery_material`，`nav2_status=goal_succeeded`，`delivery_success=false`，仍缺 operator report、observed motion/stop、delivery claim、route/map ref 和 external video / visible camera ref 等 gate 材料。

## 剩余风险

- 本轮只减少现场送达材料填写步骤，不证明 delivery success。
- delivery success 仍必须由现场 operator 显式确认 observed motion/stop、route/map ref、画面 ref 和 delivery claim 后，通过上位机 delivery gate 给出。
