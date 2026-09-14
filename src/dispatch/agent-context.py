#!/usr/bin/env python3
"""Print the stable machine-facing Task-Spec CLI contract."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

commands = json.loads((ROOT / "src/cli/commands.json").read_text())

contract = {
    "contract": "TaskSpecAgentContext/v1",
    "engine_version": VERSION,
    "format_version": 4,
    "default_format_version": 3,
    "supported_format_versions": [1, 2, 3, 4],
    "binary": "taskspec",
    "global_options": {
        "--json": "wrap command stdout/stderr and exit status in one JSON envelope",
        "--dry-run": "prevent supported mutations and report intended action",
        "NO_COLOR": "disable ANSI color when present",
        "TASKSPEC_COLOR": "0 disables and 1 forces ANSI color",
    },
    "exit_codes": {"0": "success", "1": "validation, gate, eval, or acceptance failure", "2": "usage error", "3": "unsupported runtime requirement"},
    "commands": commands,
    "contracts": {
        "task_spec": "spec/schemas/task-spec-frontmatter.schema.json",
        "task_execution_recipe": "spec/schemas/task-execution-recipe.schema.json",
        "task_plan_provenance": "spec/schemas/task-plan-provenance.schema.json",
        "task_plan_bundle": "spec/schemas/task-plan-bundle.schema.json",
        "task_plan_snapshot": "spec/schemas/task-plan-snapshot.schema.json",
        "task_plan_import": "spec/schemas/task-plan-import.schema.json",
        "task_plan_lineage": "spec/schemas/decompose-task-lineage.schema.json",
        "task_plan_review": "spec/schemas/decompose-delivery-plan-review.schema.json",
        "task_decomposition_recipe": "spec/schemas/decompose-recipe.schema.json",
        "task_operational_import": "spec/schemas/task-operational-import.schema.json",
        "task_operational_evidence": "spec/schemas/task-operational-evidence.schema.json",
        "task_plan": "spec/schemas/task-plan.schema.json",
        "task_materialization_receipt": "spec/schemas/task-materialization-receipt.schema.json",
        "task_handoff": "spec/schemas/task-handoff.schema.json",
        "task_revision": "spec/schemas/task-revision.schema.json",
        "task_graph_view": "spec/schemas/task-graph-view.schema.json",
        "task_status": "spec/schemas/task-status.schema.json",
        "receipt_subject": "spec/schemas/receipt-subject.schema.json",
        "acceptance_record": "spec/schemas/acceptance-record.schema.json",
        "acceptance_finalized": "spec/schemas/acceptance-finalized.schema.json",
        "acceptance_failure": "spec/schemas/acceptance-failure.schema.json",
        "evaluator_trust": "spec/schemas/evaluator-trust.schema.json",
        "mutation_matrix": "spec/schemas/mutation-matrix.schema.json",
        "provider_smoke_evidence": "spec/schemas/provider-smoke-evidence.schema.json",
        "authoring_evidence": "spec/schemas/authoring-evidence.schema.json",
        "evaluation_receipt": "spec/schemas/evaluation-receipt.schema.json",
        "graded_evaluation_receipt": "spec/schemas/graded-evaluation-receipt.schema.json",
        "human_acceptance_receipt": "spec/schemas/human-acceptance-receipt.schema.json",
        "environment_contract": "spec/schemas/environment-contract.schema.json",
        "environment_receipt": "spec/schemas/environment-receipt.schema.json",
        "authorization_receipt": "spec/schemas/authorization-receipt.schema.json",
        "engine_run_receipt": "spec/schemas/engine-run-receipt.schema.json",
        "holdout_bundle": "spec/schemas/holdout-bundle.schema.json",
        "holdout_descriptor": "spec/schemas/holdout-descriptor.schema.json",
        "agent_contract": "spec/schemas/agent-contract.schema.json",
        "a2a_artifact": "spec/schemas/a2a-artifact.schema.json",
        "mcp_task": "spec/schemas/mcp-task.schema.json",
        "taskmesh_api": "spec/schemas/taskmesh-api.schema.json",
        "taskmesh_run": "spec/schemas/taskmesh-run.schema.json",
        "executor_capability": "spec/schemas/executor-capability.schema.json",
        "dispatch_decision": "spec/schemas/dispatch-decision.schema.json",
        "run_lease": "spec/schemas/run-lease.schema.json",
        "taskmesh_event": "spec/schemas/taskmesh-event.schema.json",
        "taskmesh_view": "spec/schemas/taskmesh-view.schema.json",
        "sandbox_evidence": "spec/schemas/sandbox-evidence.schema.json",
        "credential_lease": "spec/schemas/credential-lease.schema.json",
        "taskmesh_roster": "spec/schemas/taskmesh-roster.schema.json",
    },
    "credentials": "TaskHandoff and AgentContext never contain credentials; provider and model credentials remain external to core.",
    "taskmesh": {
        "api": "TaskMeshAPI/v1alpha1",
        "commands": ["init", "doctor", "serve", "frontier", "run", "status", "watch", "explain", "cancel", "resume", "accept", "finish", "adapters", "setup sandbox", "mcp"],
        "mcp_tools": ["taskmesh.frontier", "taskmesh.explain_route", "taskmesh.start_run", "taskmesh.get_run", "taskmesh.cancel_attempt", "taskmesh.accept_attempt", "taskmesh.finish_run"],
        "authority": "TaskMesh leases, routes, observes, recovers, and integrates; only canonical taskspec accept may accept a task revision.",
    },
}

print(json.dumps(contract, indent=2, ensure_ascii=False))
