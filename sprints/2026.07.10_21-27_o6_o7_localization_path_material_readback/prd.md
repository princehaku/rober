# O6/O7 Localization Path Material Readback PRD

## Product Goal

Expose the latest O1 localization/path material to cloud archive and PC operator surfaces so an operator can see the actual state of the same run: map/localization signals were observed, but path generation did not succeed. This prevents the next operator or engineer from confusing a cross-run clean-baseline path with current same-run path proof.

## User Value

The operator-facing value is diagnostic clarity. O7 should show whether same-run map/localization/path material exists, why it is not route execution proof, and which current live artifacts are still required before retrying route execution or claiming delivery progress.

## Scope

In scope:

- Algorithm manifest additive packet: `localization_path_material_readback`.
- O6 archive/detail/consumer/include readback for that packet.
- O7 consumer adapter, shared contract, fixture preview panel, and tests for the same packet.
- Documentation updates under `docs/navigation/`, `docs/interfaces/`, and `docs/product/`.

Out of scope:

- Real robot motion, Nav2 execution, `/cmd_vel`, serial access, HIL, or route command execution.
- O5 production cloud, public TLS, production DB/queue, OSS/CDN, or real phone/browser validation.
- Claiming route execution success, delivery success, safe-to-control, or HIL pass.

## Acceptance Criteria

1. Algorithm output includes `schema=trashbot.localization_path_material_readback.v1`, `proof_scope=software_proof_localization_path_material_readback_only`, same-run localization booleans, same-run path false fields, fixed false safety fields, blocked reasons, and next required evidence.
2. O6 safely archives and returns the packet from field evidence, archive detail, consumer detail, artifact bundle path where applicable, and `include=localization_path_material_readback`.
3. O7 safely consumes and displays the packet, including same-run map/localization presence, same-run path generation result, cross-run comparator boundary, blocked reasons, and next required evidence.
4. Hostile or mismatched payloads fail closed and do not leak raw paths, URLs, tokens, traceback, base64, serial device paths, response bodies, or ROS command topics.
5. All validation commands in `tech-plan.md` pass or are repaired before closeout.

## OKR Position

This sprint may support a conservative O6/O7 increment only if it consumes the new O1 material delta through Algorithm -> O6 -> O7 and keeps route success false. It must not update O5 or O1 percentage unless current live external or HIL materials are newly introduced.

