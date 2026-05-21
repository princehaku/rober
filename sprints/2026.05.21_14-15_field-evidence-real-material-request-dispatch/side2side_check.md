# Field Evidence Real Material Request Dispatch Side-By-Side Check

Run time: 2026-05-21 14:22 CST

## Product Acceptance Question

Does this sprint convert the repeated real-field-material blocker into an executable request package, without claiming real route/elevator, phone/browser, hardware, cloud, HIL, delivery result, or delivery success?

Product answer: yes, accepted as `software_proof_docker_field_evidence_real_material_request_dispatch_gate` only.

## Side-By-Side Matrix

| Requirement | Evidence now present | Product verdict |
| --- | --- | --- |
| One request package for field owners | Autonomy gate emits `field_evidence_real_material_request_dispatch` artifact/summary with nine required material categories. | Pass as software-proof request dispatch. |
| Same safe `evidence_ref` discipline | Gate and Robot/mobile summaries preserve same-evidence-ref requirement and fail closed on mismatch. | Pass as metadata contract; real materials still missing. |
| Required route/task materials named | `task_record`, `nav2_fixed_route_runtime_log`, and `route_completion_signal` are explicitly requested. | Pass as request names only, not runtime proof. |
| Required elevator/field materials named | `elevator_door_floor_evidence` and `human_assistance_note` are explicitly requested. | Pass as request names only, not real elevator pass. |
| Required terminal/user materials named | `dropoff_cancel_completion`, `delivery_result`, `true_phone_browser_evidence`, and `diagnostics_mobile_safe_summary` are explicitly requested. | Pass as request names only, not true phone/browser or delivery proof. |
| Robot diagnostics stays safe | Robot alias allows only sanitized request metadata and keeps `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`. | Pass. |
| Mobile surface stays read-only | Mobile panel displays safe copy and disables Start Delivery / Confirm Dropoff / Cancel. | Pass. |
| Hardware facts do not become installed proof | Hardware consultation cites vendor boundary only and refuses to claim installed LiDAR/ToF, WAVE ROVER/UART/HIL, route pass, or delivery success. | Pass. |
| OKR progress remains conservative | Objective 5 remains about 68%, Objective 1 remains about 81%, Objectives 2/3/4 remain about 99%. | Pass; no percentage lift. |

## Boundary Check

Accepted evidence boundary:

- `software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

Blocked claims that remain blocked:

- real field rerun
- real `task_record`
- real `nav2_fixed_route_runtime_log`
- real `route_completion_signal`
- real elevator door/floor evidence
- real human assistance evidence
- real dropoff/cancel completion
- real `delivery_result`
- `true_phone_browser_evidence`
- route/elevator field pass
- Objective 5 external cloud/4G/OSS/CDN/DB/queue proof
- Objective 1 WAVE ROVER/UART/HIL or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution
- delivery success

## Worker Evidence Integrated

- Autonomy: PC gate, tests, README and evidence contract updates integrated.
- Robot: diagnostics safe alias, diagnostics tests and ROS runtime contract updates integrated.
- Full-Stack: mobile panel, fixture, tests and mobile user-flow doc updates integrated.
- Hardware: read-only vendor consultation integrated without changing hardware configuration or claiming installed proof.

## Acceptance Result

Product accepts the sprint as a field-owner request dispatch package. It is useful because it names the real evidence the next field run must produce. It is not counted as new real field progress because no requested real materials have been returned yet.
