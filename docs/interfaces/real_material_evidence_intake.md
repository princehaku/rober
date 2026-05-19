# Real Material Evidence Intake

`real_material_evidence_intake` is a dependency-free PC evidence gate for the
real-material回填入口 after `real_material_readiness_board`. It reads a material
manifest or sample manifest, groups material by owner, and emits an artifact plus
phone/Robot-safe summary.

It is an intake surface, not a pass/fail proof surface. Every output remains:

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Schemas

Artifact schema:

- `schema=trashbot.real_material_evidence_intake.v1`
- `evidence_boundary=software_proof_docker_real_material_evidence_intake_gate`
- `real_material_evidence_intake=<intake_status>`
- `same_evidence_ref_required=true`
- `safe_evidence_ref=<shared safe evidence_ref or empty on rejection>`
- `material_groups=[...]`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.real_material_evidence_intake_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `group_count=4`
- `accepted_count=<count>`
- `missing_count=<count>`
- `rejected_count=<count>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Material Groups

| material_group | Objective / review ref | Owner handoff | Required material items |
|---|---|---|---|
| `o5_external` | `Objective 5` | `product-okr-owner` | `public_https_tls`, `4g_sim`, `oss_cdn_live_traffic`, `production_db_queue`, `worker_migration_cutover`, `external_proof` |
| `o1_pr5_hardware` | `Objective 1`, `PR #5`, `PRRT_kwDOSWB9286CJ3tX` | `hardware-engineer` | `2d_lidar_sku_source_receipt`, `tof_sku_source_receipt`, `procurement_install_wiring_power_calibration`, `hil_entry`, `wave_rover_uart_hil_packet` |
| `pr4_route_elevator` | `PR #4`, `Objective 2`, `Objective 3` | `autonomy-engineer` | `nav2_fixed_route_runtime_log`, `route_completion_signal`, `field_task_record`, `elevator_door_state`, `target_floor_confirmation`, `human_assistance_record`, `dropoff_cancel_material`, `delivery_result` |
| `o4_real_phone` | `Objective 4` | `full-stack-software-engineer` | `real_phone_browser_session`, `production_app`, `pwa_prompt_user_choice`, `true_phone_browser_acceptance` |

`accepted_items` only means the manifest contains a safe metadata summary/ref
for manual review. It does not prove Objective 5 external readiness, Objective 1
hardware readiness, PR #5 closure, PR #4 route/elevator completion, or Objective
4 real phone acceptance.

## Manifest Shape

The manifest may use either a dict or list for `material_groups`.

```json
{
  "schema": "trashbot.real_material_manifest.v1",
  "evidence_ref": "field-material-2026-05-19T21-22Z",
  "material_groups": {
    "o1_pr5_hardware": {
      "evidence_ref": "field-material-2026-05-19T21-22Z",
      "items": {
        "wave_rover_uart_hil_packet": {
          "summary": "operator-redacted material summary for manual review",
          "material_ref": "wave-rover-uart-hil-redacted-ref"
        }
      }
    }
  }
}
```

All groups must share one safe `evidence_ref`. The reference must be non-empty,
use only safe identifier characters, and must not contain paths, credentials, or
token-like text.

## Fail-Closed Rules

The gate rejects or blocks when it sees:

- empty or unsafe `evidence_ref`
- cross-group `evidence_ref` mismatch
- unsupported material item names
- missing required material items
- `delivery_success`, `primary_actions_enabled`, `safe_to_control`,
  `hil_pass`, `field_pass`, or `control_enabled` fields
- absolute paths, serial/UART device paths, DB/queue URLs, OSS/CDN credentials,
  authorization headers, tokens, passwords, or secret-like strings

The generated artifact and summary explicitly keep:

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Vendor Source Boundary

Hardware-related fields cite local vendor source boundaries:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

These files establish the local WAVE ROVER / Orange Pi Zero 3 / ESP32 / UART
source boundary. They do not prove real WAVE ROVER UART feedback, real HIL
packet success, 2D LiDAR / ToF SKU/source/receipt, procurement, installation,
wiring, power, calibration, PR #5 closeout, or delivery success.
