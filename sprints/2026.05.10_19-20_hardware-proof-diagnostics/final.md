# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-10 19:59 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 收口结论：软件侧产品闭环完成；硬件在环证据仍未完成。

## 用户价值和产品北极星

本 sprint 的业务结果是：硬件 proof 进入 operator diagnostics 和手机售后诊断界面，普通用户或售后同学可以从页面看到硬件软件证据状态，而不是依赖工程师读 JSON artifact。

这推进了北极星中的“手机可用、失败可诊断、普通用户不碰命令行”。同时，本轮没有把软件 proof 夸大成硬件通过，保留了低成本量产必须具备的证据边界。

## OKR 映射

- O5 手机体验与量产边界：进度应上调。远程诊断最小数据包现在覆盖 hardware proof，operator 页面有可读卡片，售后诊断链路更接近普通用户可消费。
- O1 硬件协议可信底盘：可小幅上调或保持谨慎。software proof 已进入产品诊断链路，但真实 WAVE ROVER HIL、UART、IMU、电池、轮向证据仍缺。
- O2/O3/O4：本轮无功能上调；full smoke 仅作为不回归证据。

## KR 拆解或更新

- O5 KR4：完成 `hardware_proof` 进入 `/api/diagnostics` 的字段扩展。
- O5 KR5：operator 页面新增 Hardware proof 诊断卡，能提示 software proof、needs HIL、invalid config、read error 和下一步动作。
- O1 KR4：硬件 proof 软件路径被 targeted tests 和 full smoke 覆盖。
- O1 KR1-KR3/KR5：本轮未新增真实串口、反馈、IMU、电池、轮向或 launch 参数实测证据。

## 本轮核心抓手

把上一轮 hardware diagnostics proof 从“工程师 artifact”变成“产品诊断状态”。这让售后和手机界面能消费证据，也让下一轮 HIL 工作的缺口更明确。

## 做什么 / 不做什么

做了：

- `/api/diagnostics` 总是包含 `hardware_proof`。
- operator 页面新增 Hardware proof 诊断卡。
- 文案和状态保持保守，不出现 hardware passed、HIL passed、实车已通过结论。
- `tech-done.md` 已记录实现文件、验证命令、失败定位和剩余风险。

没做：

- 没有真实 HIL。
- 没有真实 UART、IMU、电池、轮向、速度单位、反馈频率证据。
- 没有修改产品代码或测试以外的硬件配置、launch、vendor 文件。
- 没有给 `operator_gateway.py` 增加 `hardware_proof_ref` ROS 参数入口。

## 优先级和验收口径

本轮 P0 通过：

- API 字段稳定存在。
- 页面诊断卡存在。
- 四类状态可表达且保守。
- 读取失败结构化降级。
- targeted tests、py_compile、full smoke、diff check 全部通过。

未进入验收：

- 真实手机浏览器截图。
- 真实 WAVE ROVER 上车 HIL。
- `operator_gateway.py` 参数接线后的 launch 级验证。

## 对应责任 Engineer

- 本轮实现：`full-stack-software-engineer`。
- 下一轮建议：
  - `robot-software-engineer` 主责 `operator_gateway.py` 的 `hardware_proof_ref` 参数入口和 bringup 接线。
  - `full-stack-software-engineer` 负责 API/UI 回归。
  - `hardware-engineer` 负责真实 WAVE ROVER HIL 证据采集。

## 风险、阻塞和需要补齐的证据链

- `operator_gateway.py` 尚无 `hardware_proof_ref` ROS 参数入口；默认未配置时，页面会显示 `read_error`，这符合保守降级，但不是理想用户体验。
- 真实 WAVE ROVER、UART、轮向、速度单位、反馈频率、IMU、电池证据仍缺。O1 不能因页面可见而声明硬件可信闭环完成。
- 手机/operator diagnostics 已能展示状态，但还缺真实手机浏览器截图和真实售后流程验证。
- 下一轮若接参数，不应硬编码本机 artifact 路径，应走 ROS 参数、launch 参数或配置文件，并保留 read error 降级。

## 验证结果

来自 `tech-done.md` 的实现验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
Ran 14 tests in 0.643s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'
Ran 16 tests in 8.051s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'
Ran 8 tests in 0.041s
OK
```

```bash
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
# no output; command exited 0
```

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
Ran 6 tests in 0.104s
OK
Ran 24 tests in 0.139s
OK
Ran 39 tests in 3.634s
OK
Ran 9 tests in 0.067s
OK
Ran 118 tests in 17.461s
OK
Ran 13 tests in 0.578s
OK
```

本 Product 收口验证：

```bash
git diff --check -- OKR.md sprints/2026.05.10_19-20_hardware-proof-diagnostics/side2side_check.md sprints/2026.05.10_19-20_hardware-proof-diagnostics/final.md
# no output; command exited 0
```

## 复盘

本轮最有价值的点是把“硬件证明还缺什么”展示给 operator，而不是让证明停留在工程师本地 artifact。产品上可以上调 O5，因为手机/远程诊断能力实质增强；O1 只能谨慎小幅上调，因为缺口从代码侧转移到了 HIL 和参数接线，不是被消灭。

下一轮最短路径：先补 `operator_gateway.py` 的 `hardware_proof_ref` 参数入口，让 launch 后页面能读到真实 artifact；再安排 hardware owner 做 WAVE ROVER HIL，把 UART、轮向、反馈、IMU、电池证据写回 proof 和 sprint 记录。
