# O1/O5 90% Evidence Boundary

## Scope

本文定义 sprint `sprints/2026.05.27_46-50_okr-90-software-acceleration` Task E 的硬件和外部云材料边界。目标不是提升 OKR 数字，而是写清 Objective 1 和 Objective 5 从 software proof / mock 走到 90% 以上时必须补齐的真实材料、采集命令、证据路径和 fail-closed 判断规则。

本轮不改硬件配置、不改 production 凭证、不改 launch 默认值、不实现云代码。所有真实材料进入仓库前只能是脱敏摘要或安全 artifact；`.env`、真实密钥、Authorization header、OSS AK/SK、DB/queue URL、credential-bearing URL、证书私钥和 root password 不得入仓库。

## Sources Read

硬件事实已按 `AGENTS.md` 和 `docs/vendor/VENDOR_INDEX.md` 要求核对本地 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`

Orange Pi 两个 PDF 本轮只确认为必读本地来源；当前环境没有 `pdftotext`，未抽取 PDF 正文。因此本文不新增 Orange Pi 引脚、电压或机械尺寸结论，只把它们列为真实上车前必须二次核查的材料来源。

## Objective 1 90% Boundary

Objective 1 超过 90% 不能只依赖 mock、虚拟串口、Docker build 或 synthetic fixture。必须拿到同一台真实 WAVE ROVER + ESP32 + Orange Pi 的 HIL packet，并且 packet 内每个文件共享同一个 safe `evidence_ref`。

已证实的 vendor 硬件结论：

- WAVE ROVER 上下位机链路是 UART 上的一行一个 UTF-8 JSON object，并以 `\n` 结束；来源是 `base_ctrl.py` 的 `json.dumps(data) + '\n'` 和 `readline()` 读取方式。
- vendor Raspberry Pi 示例默认串口为 `/dev/ttyAMA0`、备用注释为 `/dev/serial0`，波特率 `115200`；Orange Pi 真实串口路径必须在目标机现场确认，不能照抄 Raspberry Pi 路径。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`；`movtion_module.h` 中 `setGoalSpeed()` 对不同 `mainType` 有不同处理，真实轮向和速度映射必须用低速 HIL 验证。
- `json_cmd.h` 定义 `CMD_ROS_CTRL=13`，示例 `{"T":13,"X":0.1,"Z":0.3}`，注释为 m/s 和 rad/s，且注明不适用于无编码器产品；项目只有在 HIL 证明该固件/底盘行为正确后才能把它当默认控制模式。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143`，`uart_ctrl.h` 按 `T` 分发这些命令。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001` 和 `FEEDBACK_IMU_DATA=1002`；Objective 1 的 base feedback 证据必须至少包含真实 `T=1001` 帧。
- `IMU_ctrl.h` 的 IMU 输出字段包括 `r,p,y,ax,ay,az,gx,gy,gz,mx,my,mz,temp`；`battery_ctrl.h` 使用 INA219 并计算 `loadVoltage_V`、`busVoltage_V`、`current_mA`、`power_mW`，但项目 `/battery` 是否只发布电压仍以 ROS bridge 和 HIL 对齐为准。
- `movtion_module.h` 中 `mm_settings()` 给 `mainType=1/2/3` 设置不同 `WHEEL_D`、`ONE_CIRCLE_PLUSES`、`TRACK_WIDTH` 和 `SET_MOTOR_DIR`。WAVE ROVER 实车的 `mainType`、轮距、轮向和编码器行为不能从照片推断。

2026-06-01 23-24 的最新 O1 probe 已解除上一轮远端 SSH `No route to host` blocker，并通过 `ssh root@192.168.1.11 -p 37878` 在上位机上运行 stdin probe。结果证明 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 可打开、`pyserial.available=true`、显式 `--request-base-feedback` 可发送 vendor `{"T":130}\n` 且 `write_error=null`；5 秒和 15 秒读取窗口均为 `read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`。该状态只能归类为 `serial_open_t130_feedback_request_observed_without_t1001`，仍不满足下面的真实 `T=1001` HIL packet 要求，也不能替代 `feedback_T1001.log`、ROS `/imu/data`、`/battery` 或 `/odom` 同源材料。

O1 必需真实材料路径约定：

```text
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/command.txt
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/serial.log
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/feedback_T1001.log
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/odom_once.jsonl
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/imu_once.jsonl
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/battery_once.jsonl
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/operator_hil_report.json
field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/hil_evidence_packet_gate.json
```

`field-evidence/` 是现场材料目录约定，不要求本轮创建。若未来需要提交到仓库，只允许提交脱敏 summary；原始 `serial.log` 可保留在现场安全存储或 artifact 系统中。

O1 采集命令模板：

```bash
python3 onboard/scripts/hardware_smoke_wave_rover.py --status

python3 onboard/scripts/hardware_smoke_wave_rover.py \
  --move-test \
  --serial-port <orange-pi-confirmed-uart-device> \
  --baudrate 115200 \
  --feedback-interval-ms 100 \
  --test-speed 0.05 \
  --test-duration-s 0.30 \
  --evidence-ref <safe_evidence_ref> \
  2>&1 | tee field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/serial.log

python3 onboard/scripts/hil_evidence_packet_gate.py \
  field-evidence/o1_wave_rover_hil/<safe_evidence_ref> \
  --evidence-ref <safe_evidence_ref> \
  --output field-evidence/o1_wave_rover_hil/<safe_evidence_ref>/hil_evidence_packet_gate.json

python3 pc-tools/evidence/wave_rover_hil_packet_intake.py \
  field-evidence/o1_wave_rover_hil/<safe_evidence_ref> \
  --evidence-ref <safe_evidence_ref> \
  --summary-output /tmp/wave_rover_hil_packet_intake_summary.json \
  --once-json
```

O1 不能被 mock 替代的判断规则：

- `serial.log` 必须显示真实串口成功打开、`T=143 -> T=142 -> T=131` 配置顺序、至少两帧真实 `T=1001`，并且不能包含 `pyserial_missing`、`could not open port`、`no_serial_candidates_found`、`permission denied`、`blocked` 等串口失败模式。
- `feedback_T1001.log` 必须包含 JSON object，`T=1001`，且字段至少覆盖 `L,R,r,p,y,v`；这些值必须来自同一 `serial.log` 对应的实车 run。
- `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 必须来自同一 ROS runtime 与同一 `evidence_ref`，不能用 fixture、历史 replay、synthetic JSON 或手写样本替代。
- `operator_hil_report.json` 必须明确 `robot_id`、operator、run 时间、真实串口可见性、停止路径、轮向/低速运动结果、IMU/battery 对齐结论和 `result_boundary=hil_pass_candidate` 或更保守状态。
- 若只证明 `/odom` 是命令积分，不能把它写成实测里程计；若未证明编码器闭环，O1 仍保留 `real_odom_not_proven`。
- `T=13` 只能作为附加验证项；未完成 `T=13` 方向和停止验证时，默认控制模式仍不能因此升级。
- Orange Pi 引脚、电压、UART header、供电和机械安装若进入验收，必须再次打开 Orange Pi 用户手册、电路图以及 WAVE ROVER PDF/DXF/STL，并在 operator report 中记录引用材料；没有这一步不得声明 wiring/mechanical pass。

## Objective 5 90% Boundary

Objective 5 超过 90% 需要真实公网/4G/production/OSS/CDN/live traffic 证据。Docker/local preflight、SQLite proof、manifest proof、mock HTTP HEAD、local browser、local relay 和 synthetic external evidence intake 都只能保持 `not_proven`。

## Objective 5 90% Mock/Software Boundary

Sprint `sprints/2026.05.28_00-04_mock-okr-90-acceptance` Task B 允许把 Objective 5 写成 `90%+ mock/software completion`。该状态只代表本地/mock control plane 已经覆盖 commands/status/ack、bearer/env credential、mock 4G 中断恢复、mock DB/queue artifact、mock OSS/CDN 对象引用和 graceful degradation。

本轮可复验命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
```

有效 mock/software proof 必须同时满足：

- `trashbot.remote.v1` 的 `/robots/<robot_id>/commands`、`/commands/next`、`/status`、`/commands/<command_id>/ack` 在本地 HTTP relay 上完成一轮 envelope 对账。
- bearer token 只通过测试环境变量或进程参数注入；未带 bearer 的写入口返回 401。
- mock 4G 中断只使用本地 unreachable 等价故障和 network recovery drill，证明 ACK failure 不等于 delivery success，恢复后同一 command 可重新对账。
- mock DB/queue 只使用 file/SQLite proof store 和 production store/queue artifact，证明 envelope、排序和 fail-closed 摘要形态，不证明 production DB/queue 已连接。
- mock OSS/CDN 只证明 bucket/region/prefix/CDN URL 的对象引用规则和 preflight 消费；真实 OSS upload、STS issuance、CDN origin fetch 和 CDN live traffic 继续 `not_proven`。
- preflight 在缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 时必须保持 `production_ready=false` 或 blocked/warning，不允许显示真实生产 ready。
- `pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs` 可作为外部/上位机视角
  的只读 live probe 入口，输出 `trashbot.o5_o6.external_live_probe.v1` 并检查 O5
  readiness、O6 archive 和 PC aggregate health 的可达性、schema、安全 false 字段和
  fail-closed 分类。它只发固定 GET，不 POST、不访问 `/robots/*`、不读取硬件、不回显
  bearer；网络不通或服务未配置时也只形成 fail-closed 软件证据。该脚本不能替代下面的
  公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic 或真实
  phone/browser 材料。
- `cloud-relay/scripts/o5_o6_external_live_probe.py` 是同一 schema 的 Python stdlib
  runner，额外输出 `runner=python_stdlib`，用于 Orange Pi / 上位机缺 Node.js 时采集
  同类 fail-closed 软件证据。它可通过 `python3 -s - --once-json < script.py` 的 stdin
  形态运行，并支持 `--output /safe/runtime/o5-o6-external-live-probe.json` 把同一份
  脱敏 JSON 落盘给 PC workstation 读取；仍只 GET O5/O6 health 和可选 PC aggregate，
  不 POST、不访问 `/robots/*`、不读取硬件、不回显 bearer；任何 `safe_to_control`、`sends_commands`、
  `robot_control_executed`、`reads_hardware`、`delivery_success` 等危险 true 字段都会
  被分类为 contract drift。
- `GET /api/o5-o6/external-probe-artifact` 是 PC workstation 运维摘要入口，只读取
  `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 或 `.workstation-runtime/o5-o6-external-live-probe.json`
  中的最近 probe artifact，并产品化展示 `probe_status`、endpoint reachability、
  blocked reasons、fail-closed safety fields 和更新时间。它不执行 probe、不发网络请求、
  不访问 `/robots/*`、不读取硬件、不回显 bearer/token/raw URL/artifact path/traceback。

Objective 5 在该 mock 口径下可以记录为 `90%+ mock/software completion; real material not_proven`。不得把该状态写成真实公网、真实 4G、production DB/queue、OSS/CDN live traffic、真实手机/browser 或真实送达完成。

O5 必需真实材料路径约定：

```text
field-evidence/o5_cloud_external/<safe_evidence_ref>/public_https_tls_probe.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/four_g_sim_robot_polling.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/production_db_queue_probe.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/production_worker_cutover_drain.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/oss_upload_sts_result.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/cdn_live_probe_result.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/real_phone_browser_result.json
field-evidence/o5_cloud_external/<safe_evidence_ref>/redaction_review.md
field-evidence/o5_cloud_external/<safe_evidence_ref>/external_evidence_intake_summary.json
```

O5 采集命令模板：

```bash
curl -fsS https://<public-cloud-host>/healthz
curl -fsS https://<public-cloud-host>/readyz
curl -fsS https://<public-cloud-host>/preflightz

curl -fsS -H "Authorization: Bearer $TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN" \
  https://<public-cloud-host>/robots/<robot_id>/commands/next

PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_PUBLIC_INGRESS_TLS_STATUS=redacted_summary_received \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_OSS_CDN_STATUS=redacted_summary_received \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_DB_QUEUE_STATUS=redacted_summary_received \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_4G_SIM_STATUS=redacted_summary_received \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json

python3 pc-tools/evidence/cloud_external_evidence_review_decision.py \
  --intake-json /tmp/trashbot_external_evidence_intake.json \
  --expected-evidence-ref <safe_evidence_ref> \
  --output /tmp/trashbot_cloud_external_evidence_review_decision.json \
  --summary-output /tmp/trashbot_cloud_external_evidence_review_decision_summary.json
```

O5 不能被 mock 替代的判断规则：

- `public_https_tls_probe.json` 必须来自公网 HTTPS endpoint，记录 TLS、DNS、公网入口和 `/healthz`、`/readyz`、`/preflightz` 的脱敏结果；本地 `127.0.0.1`、Docker bridge、HTTP 或内网-only URL 不算。
- `four_g_sim_robot_polling.json` 必须来自机器人通过真实 4G/SIM outbound polling 云端的记录，包含运营商/信号/断网恢复的脱敏摘要；WiFi、USB tethering、local network 或 mock carrier 不算。
- `production_db_queue_probe.json` 必须证明 production DB/queue 已连接、迁移/worker/ordering/transaction/backup 最小探测通过；file store、SQLite proof store 和单机 Docker 不算。
- `production_worker_cutover_drain.json` 必须证明真实 production worker/cutover/drain 对 command/status/ack envelope 生效；本地 drain rehearsal 不算。
- `oss_upload_sts_result.json` 必须证明 STS 或受限 AK 上传到 bucket `bytegallop`、region `oss-cn-hangzhou`、prefix `rober/<robot_id>/<date>/<task_id>/`；manifest shape 或本地对象引用不算。
- `cdn_live_probe_result.json` 必须证明 `https://cdn.bytegallop.com/rober/` 下真实对象可被 CDN 回源/读取；mock HEAD、本地 HTTP 2xx 或只保存 object key hash 不算。
- `real_phone_browser_result.json` 必须来自真实手机或真实 browser 访问公网云端，不是 unit test、Playwright local-only 或 API fixture。
- 所有 O5 原始材料必须先脱敏再进入 intake/review。凭证、token、Authorization header、OSS AK/SK、签名 URL、DB/queue URL、证书私钥、cookie、root password、完整响应体和 trace 不得入仓库。

## 90% Acceptance Rule

O1/O5 任一项如果缺少上述真实材料，只能写 `not_proven` 或 `blocked_pending_real_material`。可接受的软件侧状态包括 `software_proof_ready`、`ready_for_real_hil_collection_not_proven`、`external_evidence_intake_ready_not_proven`，但这些状态不得推动真实完成度到 90% 以上。

90% 以上的最小条件：

- O1：真实 WAVE ROVER HIL packet 通过 intake/review，operator report 没有串口、停止路径、轮向、反馈、IMU/battery 或 `/odom` 边界阻断项。
- O5：公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS upload、CDN live traffic 和真实 phone/browser 至少各有一份脱敏真实材料，并通过 external evidence review。
- 两者都必须保留 `delivery_success=false`，除非另有真实路线/送达闭环材料；O1/O5 90% 只代表对应 Objective 的材料边界满足，不代表整车送达成功。
