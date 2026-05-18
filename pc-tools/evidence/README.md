# Evidence Gates

## route_task_field_retest_drill_console

`route_task_field_retest_drill_console.py` consumes only the previous
`route_task_field_retest_operator_drill` artifact, summary, or compatible wrapper.
It emits `trashbot.route_task_field_retest_drill_console.v1` and
`trashbot.route_task_field_retest_drill_console_summary.v1` under
`software_proof_docker_route_task_field_retest_drill_console_gate`.

The gate is Docker-only software proof: `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false` are fixed
boundaries. It does not call ROS, Nav2, serial/UART, WAVE ROVER, browser,
cloud, OSS/CDN, DB/queue, 4G, phone device, or real hardware.
