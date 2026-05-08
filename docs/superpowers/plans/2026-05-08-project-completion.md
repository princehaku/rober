# ros_rbs Project Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the three-stage `ros_rbs` project completion roadmap: hardware fact alignment, trash delivery MVP behavior, and product-grade navigation, vision, and acceptance documentation.

**Architecture:** The work is split into three independently verifiable phases. Phase 1 aligns hardware protocol documentation and local smoke testing without changing robot behavior. Phase 2 introduces a testable behavior state machine and task record layer before wiring it into ROS2 actions. Phase 3 improves fixed-route observability, vision debug data capture, and user/hardware acceptance docs.

**Tech Stack:** ROS2 Humble Python packages, `unittest`, PowerShell smoke test script, WAVE ROVER UART newline-delimited JSON protocol, Nav2, OpenCV, YAML/CSV route tooling.

---

## File Map

- `README.md`: public project overview and protocol summary.
- `docs/hardware/wave_rover_json_bridge.md`: source-backed hardware bridge notes and validation checklist.
- `scripts/run_smoke_tests.ps1`: Windows-friendly local test runner for ROS-independent tests.
- `src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`: protocol unit tests.
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`: pure Python delivery task state machine.
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`: JSON task record writer.
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`: ROS2 action integration.
- `src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`: state transition tests.
- `src/ros2_trashbot_behavior/test/test_task_record.py`: task record tests.
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`: debug status improvements.
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`: static coverage for debug status fields.
- `src/ros2_trashbot_vision/ros2_trashbot_vision/trash_detector.py`: ROI/debug/sample parameters and sample output.
- `src/ros2_trashbot_vision/test/test_trash_detector_static.py`: static coverage for new parameters.
- `docs/navigation/fixed_route_workflow.md`: learn/autonomous/fixed-route workflow.
- `docs/vision/trash_status_contract.md`: perception contract.
- `docs/acceptance/robot_bringup_checklist.md`: hardware and mission acceptance checklist.
- `docs/product/mobile_user_flow.md`: phone-first user flow.
- `docs/product/production_hardware_boundary.md`: low-cost production hardware boundary.

---

### Task 1: Phase 1 Protocol Documentation And Smoke Test

**Files:**
- Modify: `README.md`
- Create: `docs/hardware/wave_rover_json_bridge.md`
- Create: `scripts/run_smoke_tests.ps1`

- [ ] **Step 1: Update README protocol section**

Replace the binary frame section with a WAVE ROVER JSON section:

```markdown
## 串口协议

本项目底盘通信以 `docs/vendor/VENDOR_INDEX.md` 为硬件事实入口。当前 WAVE ROVER 官方 ESP32 固件使用 UART newline-delimited JSON：每条命令是一行 UTF-8 JSON，以 `\n` 结尾。vendor Raspberry Pi 示例为 `/dev/ttyAMA0`、`115200`，Orange Pi Zero 3 的实际串口设备名必须上车确认，launch 参数不得硬编码为 Raspberry Pi 路径。

常用命令：

- `{"T":1,"L":0.5,"R":0.5}`：左右轮速度命令，当前默认 `/cmd_vel` 映射路径。
- `{"T":13,"X":0.1,"Z":0.3}`：ROS 线速度/角速度命令，仅在硬件验证后通过参数启用。
- `{"T":131,"cmd":1}`：开启底盘反馈流。
- `{"T":142,"cmd":100}`：设置反馈间隔。
- `{"T":143,"cmd":0}`：关闭 UART echo。
- `T=1001` 反馈：用于 IMU、电池和底盘反馈解析；当前 `/odom` 来源需在代码和文档中明确。
```

- [ ] **Step 2: Add hardware bridge document**

Create `docs/hardware/wave_rover_json_bridge.md` with these sections:

```markdown
# WAVE ROVER JSON Bridge

## Sources

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

## UART Framing

The official WAVE ROVER ESP32 firmware expects one UTF-8 JSON object per UART line, terminated by `\n`.

## Command Modes

- `speed`: maps ROS `/cmd_vel` to `T=1` left/right speed values. This is the conservative project default.
- `ros`: maps ROS `/cmd_vel` to `T=13` `X`/`Z` values. Enable only after hardware validation on the loaded firmware.

## Configurable Launch Parameters

- `serial_port`
- `serial_baudrate`
- `command_mode`
- `track_width_m`
- `max_wheel_speed_mps`

## Validation Checklist

- Confirm actual Orange Pi serial device.
- Confirm baud rate at `115200`.
- Send stop command and verify wheels stop.
- Verify `T=1` positive left/right direction at low speed.
- Verify `T=1001` feedback fields.
- Verify IMU yaw unit and battery voltage.
- Test `T=13` only after stop and low-speed `T=1` are safe.

## Known Limits

`/odom` may be command-integrated until measured wheel odometry is validated. Do not treat it as fused localization.
```

- [ ] **Step 3: Add smoke test script**

Create `scripts/run_smoke_tests.ps1`:

```powershell
$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    python -m unittest discover -s src\ros2_trashbot_hardware\test -p "test*.py"
    python -m unittest discover -s src\ros2_trashbot_nav\test -p "test*.py"
    python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
}
finally {
    Pop-Location
}
```

- [ ] **Step 4: Run smoke test script**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_smoke_tests.ps1
```

Expected: hardware, nav, and behavior unit/static tests all pass.

---

### Task 2: Phase 1 Hardware Bridge Test Hardening

**Files:**
- Modify: `src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- Modify: `src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge.py`

- [ ] **Step 1: Write failing tests for invalid command modes and wheel clamping**

Add tests:

```python
def test_cmd_vel_speed_mode_clamps_wheel_values(self):
    bridge = _bridge_module()
    command = bridge.build_cmd_vel_command(
        linear_x=9.0,
        angular_z=0.0,
        command_mode="speed",
        track_width_m=0.172,
        max_wheel_speed_mps=1.3,
    )
    self.assertEqual(command, {"T": 1, "L": 1.0, "R": 1.0})

def test_cmd_vel_rejects_invalid_command_mode(self):
    bridge = _bridge_module()
    with self.assertRaisesRegex(ValueError, "Unsupported command_mode"):
        bridge.build_cmd_vel_command(
            linear_x=0.0,
            angular_z=0.0,
            command_mode="pwm",
            track_width_m=0.172,
            max_wheel_speed_mps=1.3,
        )
```

- [ ] **Step 2: Run tests and verify RED if behavior is missing**

Run:

```powershell
python -m unittest src\ros2_trashbot_hardware\test\test_waveshare_json_bridge.py
```

Expected: tests pass if behavior already exists, otherwise fail for the missing behavior. If both pass immediately, record that existing implementation already satisfies this task.

- [ ] **Step 3: Implement only missing behavior**

If needed, update `build_cmd_vel_command()` so invalid modes raise `ValueError` and speed mode clamps `L`/`R` to `[-1.0, 1.0]`.

- [ ] **Step 4: Run hardware tests**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_hardware\test -p "test*.py"
```

Expected: all hardware tests pass.

---

### Task 3: Phase 2 Delivery State Machine

**Files:**
- Create: `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- Create: `src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`

- [ ] **Step 1: Write failing state machine tests**

Create tests for success, missing target, navigation failure, dropoff failure, and cancel:

```python
import unittest

from ros2_trashbot_behavior.delivery_state_machine import DeliveryEvent, DeliveryState, DeliveryStateMachine


class DeliveryStateMachineTest(unittest.TestCase):
    def test_successful_delivery_returns_to_idle(self):
        machine = DeliveryStateMachine()
        machine.start_loaded_task("bin_a")
        machine.navigation_succeeded()
        machine.dropoff_confirmed()
        machine.return_succeeded()
        self.assertEqual(machine.state, DeliveryState.IDLE)
        self.assertEqual(machine.error_message, "")

    def test_missing_target_enters_error(self):
        machine = DeliveryStateMachine()
        machine.start_loaded_task("")
        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "delivery target is required")

    def test_navigation_failure_enters_error(self):
        machine = DeliveryStateMachine()
        machine.start_loaded_task("bin_a")
        machine.navigation_failed("nav timeout")
        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "nav timeout")

    def test_dropoff_failure_enters_error(self):
        machine = DeliveryStateMachine()
        machine.start_loaded_task("bin_a")
        machine.navigation_succeeded()
        machine.dropoff_failed("operator did not confirm")
        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "operator did not confirm")

    def test_cancel_enters_idle_with_cancel_event(self):
        machine = DeliveryStateMachine()
        machine.start_loaded_task("bin_a")
        machine.cancel("user canceled")
        self.assertEqual(machine.state, DeliveryState.IDLE)
        self.assertEqual(machine.events[-1].event, DeliveryEvent.CANCELED)
```

- [ ] **Step 2: Run state machine tests and verify RED**

Run:

```powershell
python -m unittest src\ros2_trashbot_behavior\test\test_delivery_state_machine.py
```

Expected: import failure because `delivery_state_machine.py` does not exist.

- [ ] **Step 3: Implement state machine**

Create `delivery_state_machine.py`:

```python
from dataclasses import dataclass, field
from enum import Enum
import time


class DeliveryState(Enum):
    IDLE = "idle"
    LOADED = "loaded"
    DELIVERING = "delivering"
    DROPOFF = "dropoff"
    RETURNING = "returning"
    ERROR = "error"


class DeliveryEvent(Enum):
    TASK_LOADED = "task_loaded"
    NAVIGATION_SUCCEEDED = "navigation_succeeded"
    NAVIGATION_FAILED = "navigation_failed"
    DROPOFF_CONFIRMED = "dropoff_confirmed"
    DROPOFF_FAILED = "dropoff_failed"
    RETURN_SUCCEEDED = "return_succeeded"
    RETURN_FAILED = "return_failed"
    CANCELED = "canceled"


@dataclass
class StateTransition:
    timestamp: float
    event: DeliveryEvent
    from_state: DeliveryState
    to_state: DeliveryState
    message: str = ""


@dataclass
class DeliveryStateMachine:
    state: DeliveryState = DeliveryState.IDLE
    target: str = ""
    error_message: str = ""
    events: list[StateTransition] = field(default_factory=list)

    def _transition(self, event: DeliveryEvent, to_state: DeliveryState, message: str = ""):
        previous = self.state
        self.state = to_state
        self.events.append(StateTransition(time.time(), event, previous, to_state, message))

    def start_loaded_task(self, target: str):
        self.target = target.strip()
        self.error_message = ""
        if not self.target:
            self.error_message = "delivery target is required"
            self._transition(DeliveryEvent.TASK_LOADED, DeliveryState.ERROR, self.error_message)
            return
        self._transition(DeliveryEvent.TASK_LOADED, DeliveryState.LOADED, self.target)
        self._transition(DeliveryEvent.TASK_LOADED, DeliveryState.DELIVERING, self.target)

    def navigation_succeeded(self):
        self._transition(DeliveryEvent.NAVIGATION_SUCCEEDED, DeliveryState.DROPOFF)

    def navigation_failed(self, message: str):
        self.error_message = message or "navigation failed"
        self._transition(DeliveryEvent.NAVIGATION_FAILED, DeliveryState.ERROR, self.error_message)

    def dropoff_confirmed(self):
        self._transition(DeliveryEvent.DROPOFF_CONFIRMED, DeliveryState.RETURNING)

    def dropoff_failed(self, message: str):
        self.error_message = message or "dropoff failed"
        self._transition(DeliveryEvent.DROPOFF_FAILED, DeliveryState.ERROR, self.error_message)

    def return_succeeded(self):
        self._transition(DeliveryEvent.RETURN_SUCCEEDED, DeliveryState.IDLE)

    def return_failed(self, message: str):
        self.error_message = message or "return failed"
        self._transition(DeliveryEvent.RETURN_FAILED, DeliveryState.ERROR, self.error_message)

    def cancel(self, message: str):
        self._transition(DeliveryEvent.CANCELED, DeliveryState.IDLE, message)
```

- [ ] **Step 4: Run state machine tests**

Run:

```powershell
python -m unittest src\ros2_trashbot_behavior\test\test_delivery_state_machine.py
```

Expected: all tests pass.

---

### Task 4: Phase 2 Task Record Writer

**Files:**
- Create: `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- Create: `src/ros2_trashbot_behavior/test/test_task_record.py`

- [ ] **Step 1: Write failing task record test**

Create:

```python
import json
import tempfile
import unittest
from pathlib import Path

from ros2_trashbot_behavior.delivery_state_machine import DeliveryStateMachine
from ros2_trashbot_behavior.task_record import write_task_record


class TaskRecordTest(unittest.TestCase):
    def test_write_task_record_persists_state_transitions(self):
        with tempfile.TemporaryDirectory() as td:
            machine = DeliveryStateMachine()
            machine.start_loaded_task("bin_a")
            machine.navigation_succeeded()
            machine.dropoff_confirmed()
            machine.return_succeeded()
            output = write_task_record(Path(td), "task-1", machine, "success", "")
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["task_id"], "task-1")
        self.assertEqual(payload["target"], "bin_a")
        self.assertEqual(payload["final_status"], "success")
        self.assertGreaterEqual(len(payload["state_transitions"]), 4)
```

- [ ] **Step 2: Run task record test and verify RED**

Run:

```powershell
python -m unittest src\ros2_trashbot_behavior\test\test_task_record.py
```

Expected: import failure because `task_record.py` does not exist.

- [ ] **Step 3: Implement task record writer**

Create:

```python
import json
from pathlib import Path
import time


def write_task_record(output_dir, task_id, machine, final_status, error_message):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id,
        "target": machine.target,
        "final_status": final_status,
        "error_message": error_message,
        "duration": (
            machine.events[-1].timestamp - machine.events[0].timestamp
            if len(machine.events) >= 2 else 0.0
        ),
        "written_at": time.time(),
        "state_transitions": [
            {
                "timestamp": event.timestamp,
                "event": event.event.value,
                "from_state": event.from_state.value,
                "to_state": event.to_state.value,
                "message": event.message,
            }
            for event in machine.events
        ],
    }
    path = output_dir / f"{task_id}.json"
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)
    return path
```

- [ ] **Step 4: Run behavior tests**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
```

Expected: all behavior tests pass.

---

### Task 5: Phase 2 Orchestrator Integration

**Files:**
- Modify: `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- Modify: `src/ros2_trashbot_behavior/test/test_patrol_action_contract_static.py`

- [ ] **Step 1: Add static test rejecting core sleep placeholders**

Add a static test that parses `_execute_collection` and fails if it contains `_sleep_async` calls without a dry-run guard:

```python
def test_collection_no_long_sleep_placeholders(self):
    source = ORCHESTRATOR_SOURCE.read_text(encoding="utf-8")
    self.assertNotIn("await self._sleep_async(3.0)", source)
    self.assertNotIn("await self._sleep_async(2.0)", source)
```

- [ ] **Step 2: Run behavior tests and verify RED**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
```

Expected: the new static test fails while current placeholder sleeps remain.

- [ ] **Step 3: Add orchestrator parameters and state machine calls**

Update `TaskOrchestrator.__init__()` to declare:

```python
self.declare_parameter("task_record_dir", "~/.ros/trashbot_tasks")
self.declare_parameter("delivery_target", "trash_station")
self.declare_parameter("delivery_dry_run", True)
self.task_record_dir = os.path.expanduser(self.get_parameter("task_record_dir").value)
self.delivery_target = str(self.get_parameter("delivery_target").value)
self.delivery_dry_run = bool(self.get_parameter("delivery_dry_run").value)
```

Update `_execute_collection()` to use `DeliveryStateMachine` and `write_task_record()`. In dry-run mode, call the state machine transitions immediately and return success. In non-dry-run mode, return a clear failure message until Nav2/fixed-route action wiring is implemented.

- [ ] **Step 4: Run behavior tests**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
```

Expected: all behavior tests pass.

---

### Task 6: Phase 3 Fixed Route Debug Status

**Files:**
- Modify: `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- Create: `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`

- [ ] **Step 1: Write static test for debug fields**

Create a test that requires `last_error`, `last_nav_result`, `updated_at`, and `current_target` in `_write_debug_status`.

- [ ] **Step 2: Run nav tests and verify RED**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_nav\test -p "test*.py"
```

Expected: new static test fails until fields are added.

- [ ] **Step 3: Add debug fields**

Add `self.last_error`, `self.last_nav_result`, and include current target pose summary and timestamp in the debug payload.

- [ ] **Step 4: Run nav tests**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_nav\test -p "test*.py"
```

Expected: all nav tests pass.

---

### Task 7: Phase 3 Vision Debug Data And Contracts

**Files:**
- Modify: `src/ros2_trashbot_vision/ros2_trashbot_vision/trash_detector.py`
- Create: `src/ros2_trashbot_vision/test/test_trash_detector_static.py`
- Create: `docs/vision/trash_status_contract.md`

- [ ] **Step 1: Write static tests for vision parameters**

Require these parameters in the source: `roi_x`, `roi_y`, `roi_width`, `roi_height`, `debug_image_topic`, `sample_output_dir`, and `save_detection_samples`.

- [ ] **Step 2: Run vision static test and verify RED**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_vision\test -p "test*.py"
```

Expected: static test fails until parameters exist.

- [ ] **Step 3: Add parameters and sample writer**

Add ROI cropping with normalized bounds, optional debug image publisher, and optional sample writer that saves original image, annotated image, and detection JSON.

- [ ] **Step 4: Add TrashStatus contract doc**

Document frame, confidence, trash type, `is_bin`, timestamp, and current heuristic limits.

- [ ] **Step 5: Run vision tests**

Run:

```powershell
python -m unittest discover -s src\ros2_trashbot_vision\test -p "test*.py"
```

Expected: all vision tests pass.

---

### Task 8: Phase 3 Workflow And Product Docs

**Files:**
- Create: `docs/navigation/fixed_route_workflow.md`
- Create: `docs/acceptance/robot_bringup_checklist.md`
- Create: `docs/product/mobile_user_flow.md`
- Create: `docs/product/production_hardware_boundary.md`

- [ ] **Step 1: Add navigation workflow doc**

Document learning, route recording, CSV-to-YAML conversion, fixed-route dry-run, autonomous run, and debug web status.

- [ ] **Step 2: Add robot bringup checklist**

Include serial confirmation, stop command, low-speed motion, feedback, map load, route dry-run, mission dry-run, physical emergency stop, and post-run logs.

- [ ] **Step 3: Add mobile user flow**

Document connect device, select station, confirm loaded, start, status, exception handling, and human takeover.

- [ ] **Step 4: Add production hardware boundary**

Document default hardware: chassis, upper computer, portable WiFi, camera, microphone, speaker. Require cost, assembly, maintenance, and software benefit for additions.

- [ ] **Step 5: Run smoke tests**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_smoke_tests.ps1
```

Expected: all smoke tests pass.

---

## Final Verification

- [ ] Run hardware tests:

```powershell
python -m unittest discover -s src\ros2_trashbot_hardware\test -p "test*.py"
```

- [ ] Run nav tests:

```powershell
python -m unittest discover -s src\ros2_trashbot_nav\test -p "test*.py"
```

- [ ] Run behavior tests:

```powershell
python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
```

- [ ] Run vision tests if test directory exists:

```powershell
if (Test-Path src\ros2_trashbot_vision\test) { python -m unittest discover -s src\ros2_trashbot_vision\test -p "test*.py" }
```

- [ ] Run smoke script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_smoke_tests.ps1
```

- [ ] Record ROS2 build gap if this Windows environment cannot source `/opt/ros/humble/setup.bash`.
