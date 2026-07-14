# Live AMCL TF Bringup Repair Interrupted

- Command:
  - `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json`
- Result:
  - Local process stayed running for more than 3 minutes and did not emit the expected JSON artifact.
  - Manual interrupt (`Ctrl-C`) was required.
- Traceback summary:
  - The hang was inside `field_route_evidence_preflight.py -> check_nav2_proof_refresh() -> run_command() -> subprocess.run()` while waiting on the SSH refresh readback command.
- Evidence boundary:
  - This note proves the live preflight entry can reach the long-running SSH refresh stage.
  - It does not prove `initialpose_published`, `amcl_pose_observed`, `map->odom`, `path_generated`, `safe_to_control`, HIL, delivery success, or real route execution success.
