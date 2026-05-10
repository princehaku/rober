# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-10 19:20 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 产品范围：operator diagnostics API + 手机 operator 页面硬件 proof 售后诊断显示。

## 背景

18-19 sprint 已经把 WAVE ROVER 软件侧 proof 做成离线 artifact，但它仍停留在工程师手动执行和阅读 JSON 的阶段。对普通手机用户和售后同学来说，这个证据还没有进入可用诊断链路。

本轮把 proof artifact 接入 `/api/diagnostics` 和 operator 手机页面，让售后能快速判断：

- 软件 proof 是否存在并可读。
- 当前只是 software proof，仍需要 HIL。
- 是否是 invalid config。
- 是否是 artifact read error。

## 用户价值和产品北极星

用户价值：当机器人无法发车或售后排查底盘问题时，手机页面能给出可理解的诊断状态和下一步动作，减少普通用户接触 SSH、ROS2、串口工具和 vendor JSON 的概率。

产品北极星：低成本自主垃圾投递机器人必须用手机完成核心操作和诊断闭环。硬件可信度要可追溯，但在没有上车证据前不能对用户承诺硬件已通过。

## OKR 映射

- Objective 5 KR4：扩展远程诊断最小数据包，新增 hardware proof 证据链。
- Objective 5 KR5：增强普通用户验收标准中的“失败时知道怎么做”。
- Objective 1 KR4/KR5：复用上一轮 proof artifact，继续把硬件协议软件证据和参数边界暴露给诊断链路。

## KR 拆解或更新

本轮完成后，KR 证据应能写入后续收口文档：

- `/api/diagnostics.hardware_proof.status` 能表达 `software_proof`、`needs_hil`、`invalid_config`、`read_error`。
- `/api/diagnostics.hardware_proof.artifact_ref` 指向被读取的 proof artifact 路径或配置引用。
- `/api/diagnostics.hardware_proof.vendor_sources` 只展示 proof artifact 中已有 vendor source refs，不在 UI 中新增未经查证的硬件事实。
- `/api/diagnostics.hardware_proof.risk_flags` 和 `hil_recipe` 摘要提醒售后下一步需要真实 WAVE ROVER HIL。
- operator 页面有独立硬件 proof diagnostics 区域，不复用 vision integrity 的状态以免混淆。

## 用户故事

1. 作为普通手机用户，我打开 operator 页面后看到“硬件软件证据已生成，但需要上车验证”，而不是看到“硬件已通过”。
2. 作为售后同学，我打开 `/api/diagnostics` 后能看到 proof artifact 的路径、状态、风险 flags 和 HIL 下一步。
3. 作为工程师，我给 gateway 配置一个缺失或损坏的 artifact 路径时，diagnostics 仍返回 HTTP 200，并把问题表达为 read error。
4. 作为 Product/OKR Owner，我能在 sprint 收口时区分 Objective 1 software proof、Objective 1 HIL 缺口和 Objective 5 手机诊断进展。

## 产品边界

页面和 API 只能表达以下高层状态：

- `software_proof`：离线 software proof artifact 可读，说明软件侧证据存在。
- `needs_hil`：artifact 或 risk flags 表明仍需真实 WAVE ROVER HIL。
- `invalid_config`：proof artifact 明确报告配置非法。
- `read_error`：artifact 未配置、文件缺失、无法读取、JSON 损坏或字段不符合预期。

页面和 API 不允许表达：

- 不允许显示 hardware passed、HIL passed、vehicle verified、实车已通过等结论。
- 不允许新增 UART 设备名、波特率、速度单位、引脚、电压或机械尺寸假设。
- 不允许把 `T=13` 描述为默认安全控制路径。
- 不允许要求普通用户执行命令行才能理解当前状态。

## 功能需求

- `operator_gateway_diagnostics.py`
  - 新增读取 hardware proof artifact 的纯函数。
  - 所有读取失败必须变成结构化 summary，不允许中断 `build_diagnostics_payload()`。
  - 支持 artifact 正常、`invalid_config`、缺失路径、损坏 JSON、未知 status。
  - 对 `software_proof_ready` 做保守映射：用户态 summary 至少包含 `software_proof` 和 `needs_hil` 语义。
- `operator_gateway_http.py`
  - `/api/diagnostics` 返回 hardware proof summary。
  - HTML 页面新增 hardware diagnostics card。
  - 文案强调 software proof 和 needs HIL，不宣称实车硬件通过。
- Tests
  - behavior diagnostics tests 覆盖 artifact 读取和失败降级。
  - HTTP/page tests 覆盖 endpoint 字段和页面静态 contract。
- Docs
  - `docs/interfaces/ros_contracts.md` 增补 `/api/diagnostics.hardware_proof` 字段表和状态语义。
  - 本 sprint `tech-done.md` 记录实际改动、验证输出、偏差和风险。

## 非功能需求

- diagnostics 读取必须无 ROS daemon 依赖，单元测试可在本地 Python 环境运行。
- artifact path 为空、缺失或损坏时，HTTP API 仍返回可消费 payload。
- 手机页面在窄屏下保持已有 operator 页面结构，不引入重依赖。
- 字段命名要稳定，方便后续云端/4G remote support 复用。

## 优先级和验收口径

- P0：`/api/diagnostics` 新增 `hardware_proof` 字段，并覆盖四类产品状态。
- P0：operator 页面展示 hardware proof card，文案不越过 HIL 边界。
- P0：targeted operator diagnostics/http tests 通过。
- P0：py_compile、full smoke、diff check 通过。
- P1：接口文档可让后续 phone/cloud support 按字段消费。

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`。
- 只读咨询：`hardware-engineer`，仅在需要解释上一轮 proof artifact 字段时介入。
- Product 收口：`product-okr-owner`。

## 风险、阻塞和需要补齐的证据链

- 真实硬件证据仍缺：WAVE ROVER UART、轮向、速度单位、反馈频率、IMU、电池、T=13 均需 HIL。
- 本轮只能提高 Objective 5 诊断可用性和 Objective 1 证据可消费性，不能关闭 Objective 1 HIL。
- 如果现有 `operator_gateway` 没有 hardware proof artifact 参数，Engineer 需要选择最小配置入口，但不能硬编码本机路径。
- 实现后必须补 `tech-done.md`、`side2side_check.md`、`final.md`，并由 Product/OKR Owner 决定是否更新 `OKR.md`。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后更新：`tech-done.md`。
- 验收后更新：`side2side_check.md`、`final.md`。
