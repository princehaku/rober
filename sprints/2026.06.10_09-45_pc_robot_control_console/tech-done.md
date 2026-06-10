# 2026-06-10 09:45 PC Robot Control Console

## sprint_type

micro

## 本轮目标

为 Full-Stack Engineer 定义 PC Robot Control Console 第一版实现边界，让
`pc-tools/workstation` 从 PC-only Node/Vue 只读 proof workstation，推进到可以消费
上位机 Robot API 状态、展示真实上车 evidence capture 入口，并保留清晰的安全锁。

本轮只做产品边界和 sprint 留档，不写产品代码、不改测试、不改硬件配置。第一版目标是
PC 页面开始展示 Robot API connection、雷达/LiDAR、建图/地图、定位/Nav2、手动移动/Base、
实时图传/Camera 和安全边界，不放开真实运动。

采用的当前事实：

- `pc-tools/workstation` 现状是 PC-only Node/Vue proof workstation，当前以只读 proof、
  fixture、route/evidence/labeling 等面板为主。
- `onboard/scripts/upper_robot_api.py` 已提供 `/api/camera/*`、`/api/radar/*`、
  `/api/map/*`、`/api/nav2/*`、`/api/base/*` 和 unified status 入口。
- 第一版 PC 控制台必须 fail-closed：Robot API 不可达、状态字段缺失、proof 未通过或
  safety lock 未开启时，所有会导致真实运动或启动运行时的按钮都必须禁用。

## PC Robot Control Console 第一版设计

### 页面入口

在 `pc-tools/workstation` 新增或扩展一个顶层 tab：`Robot Control`。该页面是操作员
上车 evidence capture 的 PC 主控台，不替代手机端，不声明交付成功，不绕过
`upper_robot_api.py` 的安全 guard。

首屏必须显示：

- Robot API connection：Robot API base URL、连接状态、最后刷新时间、schema/status、
  unified status 摘要、`safe_to_control`、`primary_actions_enabled`、
  `delivery_success`、`hil_pass` 或等价 guard 字段。
- 全局安全边界：`PC console V1 = status/proof first`，默认不发送 `/cmd_vel`，
  默认不调用 `/api/base/manual`，默认不启动 Nav2 goal。
- 一键刷新：只允许刷新 unified status 和各区块 read-only/proof readback。

### Robot API connection

功能点：

- 支持在 PC 页面配置 Robot API base URL，默认可用 `http://127.0.0.1:8787` 或
  局域网上位机地址，具体配置方式由 Full-Stack Engineer 结合现有 workstation pattern
  选择。
- Node server 侧应代理 Robot API，避免 Vue 直接跨域访问上位机；代理失败必须在 UI
  显示 `unreachable` 和错误摘要。
- 页面加载时调用 Robot API root 或 `/api/status`/unified status，展示 routes 列表和
  guard flags。

允许按钮：

- `Refresh status`：调用 Robot API root 或 unified status，只读。
- `Refresh all proofs`：第一版只聚合读取 latest/status；不要默认触发会启动 runtime 的
  refresh，除非按钮名称明确标注 proof refresh 且属于下方允许项。

锁定按钮：

- `Connect and arm robot` 不做。
- `Enable real motion` 不做。
- 任何会改变机器人运行态的动作必须进入 safety lock/HIL gate，第一版默认禁用。

### 雷达/LiDAR

展示内容：

- `/api/radar/status` 摘要：设备、ROS topic、latest proof 状态、scan count/rate、
  blocked reasons、artifact path。
- `/api/radar/scan-proof/latest` 和 `/api/radar/raw-packet-proof/latest` 摘要。

允许按钮：

- `Refresh LiDAR status`：GET `/api/radar/status`。
- `Read latest scan proof`：GET `/api/radar/scan-proof/latest`。
- `Read latest raw packet proof`：GET `/api/radar/raw-packet-proof/latest`。
- `Run scan proof refresh`：POST `/api/radar/scan-proof/refresh` 可作为显式按钮，
  但必须标注 no-motion/proof refresh，并在 UI 上展示返回的 guard 字段。

锁定或 gated 按钮：

- `/api/radar/start`、`/api/radar/stop` 默认禁用；只有 safety lock + HIL gate 明确开启
  后才可调用。
- 禁止从 PC 前端直接打开串口或绕过 Robot API。

### 建图/地图

展示内容：

- `/api/map/list` 地图列表：yaml/pgm 路径、更新时间、是否可加载。
- `/api/map/proof/latest` 最新 map proof：map artifact、tf/map readiness、blocked reasons。
- 地图区第一版可先显示文本/表格，不强制做 canvas 地图渲染。

允许按钮：

- `Refresh map list`：GET `/api/map/list`。
- `Read latest map proof`：GET `/api/map/proof/latest`。
- `Run map proof refresh`：POST `/api/map/proof/refresh` 可作为显式按钮，必须标注
  no-motion/readiness proof，且不得自动调用 `/api/map/start`。

锁定或 gated 按钮：

- `/api/map/start`、`/api/map/reset`、`/api/map/save`、`/api/map/load` 默认禁用。
- 如果实现只做 UI 占位，按钮文案必须显示 `Locked: requires safety lock/HIL gate`。

### 定位/Nav2

展示内容：

- `/api/nav2/status`：AMCL/Nav2 readiness、map inputs、path/proof 状态、blocked reasons。
- `/api/nav2/proof/latest`：最新 no-motion localization/path proof 摘要。
- 如 unified status 提供 localize proof，显示 `/api/localize/proof/latest` 摘要。

允许按钮：

- `Refresh Nav2 status`：GET `/api/nav2/status`。
- `Read latest Nav2 proof`：GET `/api/nav2/proof/latest`。
- `Run Nav2 proof refresh`：POST `/api/nav2/proof/refresh` 可作为显式按钮；第一版必须按
  no-motion proof/readiness 处理，不发送 goal，不启动 `/cmd_vel`。
- `Read latest localization proof`：GET `/api/localize/proof/latest`，若 API route 存在。

锁定或 gated 按钮：

- `/api/nav2/start`、`/api/nav2/stop` 默认禁用。
- `Set initial pose`、`Send goal`、`Navigate to point`、`Follow route` 第一版只做 locked
  占位，不调用 ROS action，不发布 `/initialpose`，不发布 `/cmd_vel`。

### 手动移动/Base

展示内容：

- `/api/base/status` 摘要：base availability、feedback ack、guard flags、latest samples。
- `/api/base/feedback-samples/latest` 摘要：左右轮反馈、ACK、采样窗口、blocked reasons。
- 页面必须显式显示：第一版不放开真实手动移动。

允许按钮：

- `Refresh base status`：GET `/api/base/status`，但 UI 必须标注它可能触发 Robot API 内部
  的非运动反馈 readback；不得把它描述为纯文件读取。
- `Read latest feedback samples`：GET `/api/base/feedback-samples/latest`。
- `Request feedback samples`：POST `/api/base/feedback-samples` 可作为显式 proof 按钮，
  必须标注 non-motion feedback evidence，不得发送 `T=1`、`T=13` 或 `/cmd_vel`。

锁定或 gated 按钮：

- `/api/base/manual` 默认禁用。任何前进、后退、左转、右转、速度 slider、摇杆、键盘控制
  第一版都只能显示 locked 状态。
- `/api/base/stop` 可以显示为 locked emergency-stop placeholder；第一版若未经过真实 HIL
  验收，不应让 PC 页面声称它是可靠急停。后续放开前必须由 Hardware/Robot Software
  Engineer 明确验收。
- 禁止 PC 页面直接生成 `/cmd_vel` 或直接写 WAVE ROVER UART。

### 实时图传/Camera

展示内容：

- `/api/camera/health`：camera service、selected device、frame readiness、visible content
  相关字段。
- `/api/camera/devices`：`/dev/video*` 枚举和可用性。
- Camera 区第一版优先显示 health/devices 和 WebRTC offer 入口状态；若已有
  `/api/camera/offer` 可用，允许接入预览，但必须保留连接失败状态。

允许按钮：

- `Refresh camera health`：GET `/api/camera/health`。
- `Refresh camera devices`：GET `/api/camera/devices`。
- `Start preview`：允许调用 `/api/camera/offer` 建立实时图传预览；该动作不得发送底盘、
  Nav2、map 或 LiDAR 控制命令。
- `Close preview`：允许调用 `/api/camera/peers/{peer_id}/close` 关闭图传 peer。

锁定或 gated 按钮：

- 任何相机参数写入、设备重绑定、重启系统服务、改 v4l2 持久配置，第一版不做。

### 安全边界

第一版必须在 UI 和 server contract 中显式实现这些边界：

- 默认 `safe_to_control=false`，页面不得因为 PC UI 存在而把 `primary_actions_enabled` 置真。
- 所有真实运动入口都需要 safety lock + HIL gate；本轮实现不要求放开该 gate。
- 禁止直接发布 `/cmd_vel`、直接调用 ROS action、直接写 `/dev/ttyS5` 或任何 WAVE ROVER
  UART。
- 允许调用的 POST 仅限明确的 proof/readback/preview 类入口，并且按钮文案必须让操作员
  看出该动作是否会启动 runtime。
- Robot API 返回 `status=not_proven`、`safe_to_control=false`、`hil_pass=false`、
  `delivery_success=false` 或网络错误时，控制按钮必须保持 disabled。
- 页面所有状态都必须保留来源字段：Robot API route、HTTP 状态、刷新时间、错误摘要。

## Full-Stack Engineer 文件范围

下一轮实现 owner：`full-stack-software-engineer`。

允许改动：

- `pc-tools/workstation/src/App.vue`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/WorkstationTabs.vue`
- `pc-tools/workstation/src/components/*Robot*`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/server/*Robot*`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/*`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- 新实现 sprint 的 `sprints/<new_round>/tech-done.md`

不得改动：

- `onboard/scripts/upper_robot_api.py`
- `onboard/**` ROS2/硬件配置
- `firmware/**`
- `docs/vendor/**`
- WAVE ROVER/ESP32/Orange Pi UART、波特率、JSON 指令、速度映射、反馈协议等硬件事实

如下一轮发现 Robot API 合同缺字段，Full-Stack Engineer 只能先 fail-closed 展示缺字段；
不得自行修改 onboard API。需要 Robot Software Engineer 另开 sprint 补 API 合同。

## Full-Stack Engineer 验收命令

下一轮实现至少运行：

```bash
git status --short --branch
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
rg -n "Robot Control|Robot API|safe_to_control|HIL|cmd_vel|/api/base/manual|/api/radar/status|/api/map/list|/api/nav2/status|/api/camera/health" pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/README.md
```

若实现了本地 server smoke，追加：

```bash
cd pc-tools/workstation && npm run dev
curl -sS http://127.0.0.1:<port>/api/health
curl -sS http://127.0.0.1:<port>/<new_robot_api_proxy_health_path>
```

验收标准：

- PC 页面有 `Robot Control` 入口。
- Robot API connection、雷达/LiDAR、建图/地图、定位/Nav2、手动移动/Base、
  实时图传/Camera、安全边界七个区块都可见。
- read-only/status/latest/proof refresh 按钮按本文件矩阵开放。
- `/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start 等真实控制入口默认禁用。
- Robot API 不可达时页面 fail-closed，不出现误导性成功状态。
- `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md` 同步记录 V1 边界。

## 本轮实际改动

- 新增 `sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`。
- 未修改 `OKR.md`、`docs/product/*`、`pc-tools/*`、`onboard/*`、`firmware/*`、
  vendor 文件、硬件配置或测试代码。

## 本轮验证结果

已运行用户指定验收命令。

`git status --short --branch`

```text
## master...origin/master
?? sprints/2026.06.10_09-45_pc_robot_control_console/
```

最终复核时工作区额外显示：

```text
## master...origin/master
 M onboard/scripts/upper_robot_api.py
 M onboard/tests/test_nav2_runtime_proof_helper.py
?? sprints/2026.06.10_09-45_pc_robot_control_console/
```

`onboard/scripts/upper_robot_api.py` 和 `onboard/tests/test_nav2_runtime_proof_helper.py`
不在本轮允许修改范围内，本轮未编辑、未回滚这些改动；本轮实际新增文件仍仅为当前
sprint `tech-done.md`。

`test -f sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`

```text
退出码 0，目标文件存在。
```

`rg -n "sprint_type|PC|Robot API|雷达|建图|定位|手动|图传|safe|cmd_vel|HIL|文件范围|验收" sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`

```text
1:# 2026-06-10 09:45 PC Robot Control Console
3:## sprint_type
9:为 Full-Stack Engineer 定义 PC Robot Control Console 第一版实现边界，让
11:上位机 Robot API 状态、展示真实上车 evidence capture 入口，并保留清晰的安全锁。
14:PC 页面开始展示 Robot API connection、雷达/LiDAR、建图/地图、定位/Nav2、手动移动/Base、
15:实时图传/Camera 和安全边界，不放开真实运动。
23:- 第一版 PC 控制台必须 fail-closed：Robot API 不可达、状态字段缺失、proof 未通过或
26:## PC Robot Control Console 第一版设计
36:- Robot API connection：Robot API base URL、连接状态、最后刷新时间、schema/status、
37:  unified status 摘要、`safe_to_control`、`primary_actions_enabled`、
39:- 全局安全边界：`PC console V1 = status/proof first`，默认不发送 `/cmd_vel`，
43:### Robot API connection
65:- 任何会改变机器人运行态的动作必须进入 safety lock/HIL gate，第一版默认禁用。
67:### 雷达/LiDAR
89:### 建图/地图
109:### 定位/Nav2
131:### 手动移动/Base
156:### 实时图传/Camera
182:- 默认 `safe_to_control=false`，页面不得因为 PC UI 存在而把 `primary_actions_enabled` 置真。
183:- 所有真实运动入口都需要 safety lock + HIL gate；本轮实现不要求放开该 gate。
184:- 禁止直接发布 `/cmd_vel`、直接调用 ROS action、直接写 `/dev/ttyS5` 或任何 WAVE ROVER
192:## Full-Stack Engineer 文件范围
222:## Full-Stack Engineer 验收命令
242:验收标准：
244:- PC 页面有 `Robot Control` 入口。
245:- Robot API connection、雷达/LiDAR、建图/地图、定位/Nav2、手动移动/Base、
246:  实时图传/Camera、安全边界七个区块都可见。
248:- `/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start 等真实控制入口默认禁用。
```

完整 `rg` 输出在本轮终端验证中已确认覆盖 `sprint_type|PC|Robot API|雷达|建图|定位|手动|图传|safe|cmd_vel|HIL|文件范围|验收`
全部关键词。

复核命令：

```bash
git status --short --branch
test -f sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
rg -n "sprint_type|PC|Robot API|雷达|建图|定位|手动|图传|safe|cmd_vel|HIL|文件范围|验收" sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
```

## 失败定位

本轮是产品边界和 sprint 留档，不运行 PC workstation build/test，不连接真实 Robot API，
不验证真实上车链路。若上述文件存在和关键词验收失败，先修本文档。

## 剩余风险

- 本轮没有实现 PC 页面，只提供可交给 Full-Stack Engineer 的 V1 实现边界。
- 未验证 Robot API 当前返回字段是否足够 UI 直连消费；下一轮应通过 mock/unreachable
  fail-closed 和本地代理测试覆盖。
- 实时图传是否能在 PC workstation 内完成 WebRTC 预览，仍取决于 `/api/camera/offer`
  合同和浏览器端接入细节。
- Base 区不放开真实手动移动；后续真实运动必须另走 safety lock/HIL gate，并由硬件和
  Robot Software 证据确认。
