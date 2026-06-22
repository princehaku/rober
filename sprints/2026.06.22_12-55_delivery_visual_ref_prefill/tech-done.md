# Delivery visual ref prefill

## sprint_type

micro

## 实际改动

- PC 高级诊断的送达材料快捷表单新增“使用最近画面 ref”。
- 该按钮优先使用当前页面已有的 camera first-frame probe `probe_key_values.sample_path`；没有现成结果时，复用固定 `POST /api/robot-control/camera/first-frame/probe?baseUrl=...` 采集一次样张，然后预填 `deliveryOperatorVideoRef`。
- 不新增后端任意代理，不提交 operator report，不调用 delivery gate，不自动勾选现场确认，不声明 observed motion/stop 或 delivery success。
- `pc-tools/workstation/test/App.test.ts` 增加 UI 回归，确认按钮只 POST 固定 camera probe，并且不会调用 `/api/robot-control/operator/report` 或 `/api/robot-control/delivery/complete`。
- `docs/product/pc_tools_workstation.md` 同步记录该预填行为与安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`103 passed (103)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：`POST /api/robot-control/camera/first-frame/probe?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`proxy_status=probe_forwarded`，`remote_http_status=200`，`status=frame_read`，`read_ok=true`，`sample_write_ok=true`，`visible_content_candidate=true`，`visible_content_proven=true`，`sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782102340468.jpg`，`delivery_success=false`，`robot_control_executed=false`。

## 剩余风险

- 本轮只降低送达材料 ref 填写成本，不证明 delivery success。
- 真实 delivery gate 仍要求 operator 显式确认 observed motion/stop、delivery claim、route/map ref 和外部视频或可见相机 ref。
- camera first-frame sample path 只能作为可追溯画面材料候选，不等价于投放完成或送达成功。
