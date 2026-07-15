# O7 真实相机关键帧标注流 Epic - Tech Done

## 状态

- `sprint_type: epic`
- Algorithm lane：`implemented_offline_green_live_inventory_blocked_fail_closed`
- Full-stack lane：`implemented_o6_o7_metadata_contract_green_live_manifest_projected_blocked`
- Engineering 状态：`two_owner_implementation_complete_ready_for_product_acceptance`
- 本文记录两个 owner 的实际改动、验证与 live/fixture 边界；Product acceptance 见后续 `side2side_check.md` / `final.md`。

## Algorithm 自主能力目标和本轮抓手

- 目标：以本轮现存 ROS graph 的 `sensor_msgs/msg/Image` publisher 为唯一 live 来源，
  最多捕获一帧，形成可按 `task_id + sha256 + topic + stamp + width + height + encoding`
  复核的 O6/O7 annotation lineage。
- 抓手：冻结 `trashbot.o7.live_camera_keyframe_manifest.v1`；离线锁住 topic 选择、
  encoding/layout、PNG/hash、隐私/binary、timeout/no-retry 与 fixed-false；随后执行最多一次
  daemon-off SSH inventory，gate clean 才允许最多一次 12s capture。
- Vendor 来源：`docs/vendor/VENDOR_INDEX.md`。该入口只用于确认 Orange Pi/USB 与本地 vendor
  camera/WebRTC 参考资料边界；本轮没有从 vendor 资料外推当前实机 camera 型号、设备路径、
  安装或分辨率，live 路径仅允许 ROS topic 自发现。

## Algorithm 实际改动和接口影响

- `onboard/scripts/o7_live_camera_keyframe_capture.py`
  - 新增 `inventory` / `capture-one` 两阶段 CLI。
  - inventory 单 SSH shell source ROS、设置 `ROS2CLI_NO_DAEMON=1`、记录 daemon pid pre/post、
    有界执行 topic list/info 并验证 `rclpy`/`Image` 依赖。
  - 首选 `/camera/image_raw`；canonical 缺席时只允许唯一兼容 Image topic；wrong type、零
    publisher、多个候选、daemon drift 或依赖失败均 fail closed。
  - capture 只订阅首帧，hard subscription timeout `12s`，无 retry，只清理 helper-owned SSH
    process group；不启停 runtime、不写 topic、不执行 action/service/UART/control。
  - 支持 `rgb8/bgr8/rgba8/bgra8/mono8`，严格校验 stamp/dimensions/step/data length，
    生成 canonical RGB PNG 并校验 byte size/SHA-256。
  - JSON 递归拒绝 raw pixels、bytes、base64/data URL、绝对路径、host 与 URL；只允许
    sprint-local `keyframe.png` 作为二进制落盘。
- `onboard/tests/test_o7_live_camera_keyframe_capture.py`
  - 39 个离线测试覆盖 canonical/唯一候选/多候选/wrong type/零 publisher、dependency、
    daemon drift、encoding/layout/padding、transport、stamp/hash/source-count、危险 true、
    privacy/binary 与 timeout/encoding failure 不重试。
  - 对 helper 和测试文件执行中文技术注释比例 `>20%` 断言。
- `docs/vision/o7_live_camera_keyframe_capture.md`
  - 同步两阶段 gate、冻结 schema、lineage、encoding/layout、隐私/binary、运行方式与
    Mission Objective 0 证据边界。
- artifacts：
  - `artifacts/algorithm/read_only_camera_inventory.json`
  - `artifacts/algorithm/live_camera_keyframe_manifest.json`
  - `artifacts/algorithm/live_camera_keyframe_capture_receipt.json`
  - gate blocked，因此没有生成 `artifacts/algorithm/keyframe.png`。
- 接口影响：新增只读 CLI 和 manifest/receipt 文件合同；未修改 launch、hardware config、
  ROS msg/action/service、Full-stack 文件或其他 sprint。

## 离线验证、首轮失败和修复

- `python3 -m py_compile onboard/scripts/o7_live_camera_keyframe_capture.py onboard/tests/test_o7_live_camera_keyframe_capture.py`
  - exit `0`。
- 首轮 targeted unittest：`Ran 39 tests in 0.005s`，功能合同 37 项通过；2 个 subtest
  失败于中文技术注释比例，helper/test 均为约 `5.69%`，不是捕获逻辑失败。
- 修复：补充 inventory、候选选择、capture/no-retry、PNG/layout、redaction、manifest、
  Mission delta 逐项中文设计说明与测试矩阵说明。
- 修复后复验：`Ran 39 tests in 0.003s`，`OK`。
- 最终中文技术注释比例：helper `20.7108%`，test `21%`，均 `>20%`。
- remote shell 本地静态语法：inventory/capture 两段 `bash -n exit 0`。
- 首轮最终 artifact 结构断言因 inventory 缺顶层 `current_run_artifact_delta` 报
  `KeyError`；定位为 inventory emitter 字段遗漏，已补固定 `false` 并同步回归断言，
  不需要也没有重跑 SSH。

## 唯一 live inventory 和 capture gate

- inventory SSH 实际 invocation count：`1`。
- 命令只运行 helper `inventory`，target/port 由 sprint plan 注入；全程 daemon-off，未运行
  最新 `/scan` inventory。
- live 结果：exit `2`，elapsed `0.824s`，`status=blocked_fail_closed`，稳定错误类别
  `inventory_ssh_or_payload_failed`。
- 本地 `bash -n` 已排除 remote script 静态语法错误；由于隐私/安全设计不持久化远端
  stderr、host 或 traceback，本轮不能把根因进一步断言为 SSH 建连、ROS source、CLI、依赖
  或 payload decode 中的任何一个，保持 fail closed。
- daemon pre/post：inventory artifact 没有收到可验证 remote payload，因此仅有本地 fallback
  `process_count=0/0`、`drift=false`；这不是“远端 daemon clean”证明。
- Image publisher：未完成只读确认，`publisher_count_at_inventory=0` 是 blocked fallback，
  不是“现场确认无 publisher”的结论。
- capture gate 不 clean，所以 single-frame capture 实际 invocation count：`0`；没有执行
  capture SSH，没有 retry，没有产生真实 keyframe/PNG。
- 固定 lineage 状态：`source_proof=live_inventory_blocked`、`annotation_ready=false`、
  `media_basename=""`、`media_byte_size=0`、`sha256=""`。

## 数据、样本与调试输出变化

- 新增三个可由 `python3 -m json.tool` 解析的 blocked/fail-closed metadata artifact。
- raw pixels、binary、base64、远端地址、绝对路径、SSH stderr/traceback 均未进入 JSON。
- `keyframe.png` 不存在，避免旧图或 fixture 冒充本轮 live。

## Proof boundary、Mission Objective 0 与固定 false

- proof boundary：`live_camera_keyframe_not_captured_or_not_validated`。
- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- Mission Objective 0 未满足。
- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- 同时不证明 `/initialpose`、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER
  UART、RTC/video、visible content、privacy approval、production annotation/cloud/OSS、
  route/delivery/operator acceptance 或 HIL。

## 剩余风险和下一步建议

- 本 sprint 的 live invocation 上限已经消费：禁止第二次 inventory，capture 因 gate blocked
  保持 `0`，不得用 fixture 或历史 keyframe 补成 live。
- 当前最小 blocker 是唯一 inventory 未形成可解析远端 ROS graph payload；精确子原因未证明。
- 下一次获得新的 Product/CEO 授权窗口时，应先改进安全的结构化失败分层（例如仅记录
  `ssh_nonzero`、`ros_source_failed`、`topic_list_failed`、`payload_decode_failed`，仍不保存 stderr、
  host 或 traceback），再由新 sprint 执行一次 inventory；本 sprint 不重试。
- 即使后续获得真实帧，annotation-ready 仍不等于 visible content 或 privacy approved；需要
  独立的人审/内容质量证据后才能进入更强 annotation action/audit。

## Full-stack 实际改动和接口影响

- `remote_cloud_relay.py` / `test_remote_cloud_relay.py`
  - 在既有 `POST /api/o6/archive/artifact-bundle`、archive/consumer detail 主路径增加
    `trashbot.o6.live_camera_keyframe_annotation_material.v1`，未新增 endpoint 或 wrapper。
  - 对 live、fixture、blocked 三态校验 task/source/count、topic/stamp/dimensions/encoding、SHA、
    redaction、四 delta 与 fixed-false；拒绝 path/URL/query/base64/raw/binary/secret/dangerous true。
  - 本轮真实 blocked manifest 按同一 `task_id`、`source_proof=live_inventory_blocked`、invocation
    `1/0` 投影为 `blocked_not_proven`、`annotation_ready=false`，未伪造 live。
- `o7ConsumerReadAdapter.ts` / `contracts.ts` / `O7FixturePreviewPanel.vue`
  - 在既有 O7 consumer-detail 增加
    `trashbot.pc_tools_workstation.o7_live_camera_keyframe_annotation_ready.v1` 只读 metadata card。
  - UI 明示 `LIVE/FIXTURE/BLOCKED`，不拼媒体路径、不读任意文件、不内联 binary、不增加
    submit/export/control/OSS fetch；本轮真实 readback 显示 `BLOCKED`。
- `catalog.test.ts` / `App.test.ts`：覆盖 fixture/blocked 投影、task/source/count lineage 与 hostile
  path/URL/data URL/raw pixels/hash/stamp/task/source-count fail-closed。
- 同步 `docs/interfaces/o6_cloud_archive_api.md`、`docs/interfaces/o7_cloud_archive_task_api.md`、
  `docs/product/pc_tools_workstation.md`；生成四个 Full-stack JSON 和 `full_stack_validation.log`。

## Full-stack 验证、失败定位和修复

- `py_compile` exit `0`；camera targeted test `1` 项通过；relay 全量 `Ran 202 tests in 91.473s`、`OK`。
- workstation targeted camera test `1` 项通过；全量 `4` files / `530` tests 全通过；build、lint
  PASS，build 只保留既有 Vite `chunk >500 kB` warning。
- 四个 JSON `json.tool`、真实 blocked manifest 到 O6 exact readback、binary/path/URL forbidden scan、
  required `rg` 与 scoped `git diff --check` 全 PASS。
- 新增中文注释比例：Python `20.4748%`，TS/Vue `20.4372%`，均 `>20%`。
- 首轮 targeted unittest 使用错误 class name，在加载测试前失败；改为 canonical dotted path 后通过。
- hostile scanner 首轮把合法 ROS topic 误判为绝对路径；仅对已校验 `topic` 字段允许 `/` 前缀后通过。
- O6 section 第二次 sanitize 首轮把合法 frozen schema 降级；只对白名单 O6 schema 放行 reload，
  其余字段 gate 不变后通过。
- TypeScript build 首轮因 `blockers[0]` 在 `noUncheckedIndexedAccess` 下失败；补安全 fallback 后通过。
- catalog targeted 首轮误用 realtime mock helper 导致 404/schema mismatch；改用既有 O6 consumer
  list/detail mock 后通过。
- 全量 workstation 测试刷新两个历史 DOM 时间戳；已精确恢复，最终无该范围 diff。

## 两 owner 集成事实

- 七个 JSON 均可解析；Algorithm manifest、O6 write/readback、O7 readback 的
  `task_id=task_o7_live_camera_keyframe_annotation_20260715_1158`、source/count `1/0` 一致。
- Algorithm 没有 keyframe/hash/dimensions；Full-stack 只保留 blocked metadata，fixture 仅证明合同。
- 工程 proof boundary 仍为 `live_camera_keyframe_not_captured_or_not_validated`；Product 组合边界由
  `final.md` 定义，Engineer 不在此调整 OKR。
