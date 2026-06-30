# 底盘状态轻量化与尾读优化

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `GET /api/base/status` 默认不再直接向 WAVE ROVER UART 发送 `T=130`，避免普通 PC summary 刷新抢底盘串口；显式轮速采样仍保留在 `/api/base/feedback-request` 与 `/api/base/feedback-samples`。
  - 新增 `direct_feedback_on_get_enabled=false`、`explicit_feedback_request_endpoint` 和 `explicit_feedback_samples_endpoint`，让 PC 和现场脚本能区分轻量状态读与主动 wheel raw L/R 采样。
  - `wave_rover_feedback_debug.jsonl` 改为只从尾部读取最近行，不再全量读入几百 MB JSONL，降低 `/api/base/status` 超时和 OOM 风险。
- `onboard/scripts/test_upper_robot_api_free_roam.py`
  - 新增默认 GET 不发送直接 `T=130` 的单测。
  - 新增 bridge feedback 大日志只扫尾部的单测。
- `docs/product/pc_tools_workstation.md`
  - 同步轻量 base status 合同，并明确依据 `docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER UART JSON 资料：`T=130` 是反馈请求，`T=1001 L/R` 是 wheel raw 材料，但普通页面刷新不得隐式发送。

## 验证结果

- 通过：`python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam.UpperRobotApiFreeRoamTest.test_bridge_feedback_debug_summary_reads_log_tail_only onboard.scripts.test_upper_robot_api_free_roam.UpperRobotApiFreeRoamTest.test_base_status_get_skips_direct_t130_by_default`。
- 通过：`python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`，10 tests passed。
- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "base/status|reads fast endpoints|Robot Control summary proxies Robot API"`，1 file passed，2 tests passed。
- 通过：`git diff --check`。
- 通过：已同步 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py` 并重启 `trashbot-upper-robot-api.service`；服务监听 `0.0.0.0:8787` 且 active。
- 通过：现场只读测速显示 `GET /api/base/status` 从部署前 `curl max-time 8s timeout` 变为 `HTTP 200 time=0.072s`；回包 `direct_feedback_on_get_enabled=false`、`feedback_readback.request.attempted=false`、`sends_commands=false`、`sends_motion_commands=false`。
- 通过：车上 bridge feedback JSONL 当前约 `575MB`，`/api/base/status` 回包显示 `bridge_bytes_read=602515974`、`bridge_bytes_scanned=65536`、`bridge_tail_line_count=80`，证明只扫尾部。
- 通过：PC 7001 只读 summary 返回 `robot_api_connection.status=readable`、`loaded_count=16`、`failed_count=0`，`base_status.request_status=loaded`；键盘连续手控仍 `ready_to_verify`，下一步是现场勾安全确认后按住方向键/WASD 验证同窗口 wheel L/R 非零和松开 stop。

## 剩余风险

- 本轮没有执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`；没有做真实运动 HIL。
- wheel raw L/R 当前仍为 `0/0`，这符合未发车状态；键盘连续控制、完整 Nav2 路线执行、delivery success 仍需现场安全确认后验证。
- 相机首帧、地图当前图、雷达点贴图和建图启动仍未完成，目标继续保持 active。
