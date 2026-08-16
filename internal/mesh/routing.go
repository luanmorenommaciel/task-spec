package mesh

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

func adapterForBackend(backend string) string {
	switch backend {
	case "codex":
		return "codex-native"
	case "claude", "claude-code":
		return "claude-native"
	case "grok", "grok-build":
		return "grok-native"
	case "omp":
		return "omp-rpc"
	default:
		return ""
	}
}

func routeTask(task FrontierTask, arguments []string) (DispatchDecision, error) {
	explicit := option(arguments, "--adapter", "")
	mode := option(arguments, "--mode", "supervised")
	backend := adapterForBackend(task.ExecutionBackend)
	definitions, err := LoadAdapters()
	if err != nil {
		return DispatchDecision{}, err
	}
	defaultAdapterOrder := AdapterOrder(definitions)
	order := append([]string{}, defaultAdapterOrder...)
	advisorDigest := (*string)(nil)
	if advisorPath := option(arguments, "--advisor-file", ""); advisorPath != "" {
		raw, err := os.ReadFile(advisorPath)
		if err != nil {
			return DispatchDecision{}, fmt.Errorf("read advisor response: %w", err)
		}
		var advisor struct {
			Order []string `json:"order"`
		}
		if err := json.Unmarshal(raw, &advisor); err != nil {
			return DispatchDecision{}, fmt.Errorf("decode advisor response: %w", err)
		}
		known := map[string]bool{}
		for _, adapter := range defaultAdapterOrder {
			known[adapter] = true
		}
		seen, ranked := map[string]bool{}, []string{}
		for _, adapter := range advisor.Order {
			if known[adapter] && !seen[adapter] {
				ranked, seen[adapter] = append(ranked, adapter), true
			}
		}
		for _, adapter := range order {
			if !seen[adapter] {
				ranked = append(ranked, adapter)
			}
		}
		order = ranked
		digest, _ := digestJSON(map[string]any{"order": advisor.Order})
		advisorDigest = &digest
	}
	policy := map[string]any{"allowed_adapters": defaultAdapterOrder, "explicit": explicit, "task_backend": task.ExecutionBackend, "mode": mode, "provider": option(arguments, "--provider", ""), "model": option(arguments, "--model", "")}
	policyDigest, _ := digestJSON(policy)
	decision := DispatchDecision{
		Contract: "DispatchDecision/v1", TaskID: task.TaskID, TaskRevisionDigest: task.TaskRevisionDigest,
		PolicyDigest: policyDigest, Candidates: []DispatchCandidate{}, AdvisorResponseDigest: advisorDigest,
		DecidedAt: NowUTC(),
	}
	known := map[string]bool{}
	for _, adapter := range defaultAdapterOrder {
		known[adapter] = true
	}
	if explicit != "" && !known[explicit] {
		return decision, fmt.Errorf("NO_ELIGIBLE_EXECUTOR: unknown explicit adapter %s", explicit)
	}
	for index, adapter := range defaultAdapterOrder {
		candidate := DispatchCandidate{Adapter: adapter, Eligible: true, RejectionReasons: []string{}, StaticScore: float64(100 - index)}
		definition := definitions[adapter]
		if !contains(definition.AssuranceModes, mode) {
			candidate.Eligible = false
			candidate.RejectionReasons = append(candidate.RejectionReasons, "ASSURANCE_MODE_UNSUPPORTED")
		}
		if mode == "autonomous" && adapter != "omp-rpc" {
			candidate.Eligible = false
			candidate.RejectionReasons = append(candidate.RejectionReasons, "AUTONOMOUS_OMP_ONLY")
		}
		if mode == "supervised" && backend != "" && adapter != backend {
			candidate.Eligible = false
			candidate.RejectionReasons = append(candidate.RejectionReasons, "TASK_BACKEND_CONSTRAINT")
		}
		decision.Candidates = append(decision.Candidates, candidate)
	}
	ranked := append([]string{}, order...)
	if explicit != "" {
		ranked = append([]string{explicit}, ranked...)
	} else if mode == "autonomous" {
		ranked = append([]string{"omp-rpc"}, ranked...)
	} else if backend != "" {
		ranked = append([]string{backend}, ranked...)
	}
	eligible := map[string]bool{}
	for _, candidate := range decision.Candidates {
		eligible[candidate.Adapter] = candidate.Eligible
	}
	for _, adapter := range ranked {
		if eligible[adapter] {
			selected := adapter
			decision.Selected = &selected
			break
		}
	}
	if decision.Selected == nil {
		decision.Explanation = "no adapter survived deterministic eligibility"
		return decision, fmt.Errorf("NO_ELIGIBLE_EXECUTOR")
	}
	decision.Explanation = "selected by explicit choice, task backend, static policy, bounded advisor order, then stable tie-breaker"
	return decision, nil
}

func explainRoute(task FrontierTask, arguments []string) CommandResponse {
	decision, err := routeTask(task, arguments)
	if err != nil {
		return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: false, Code: "NO_ELIGIBLE_EXECUTOR", Message: err.Error(), Data: map[string]any{"decision": decision}}
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_ROUTE_READY", Message: "deterministic route selected", Data: map[string]any{"decision": decision}}
}

func stableCandidates(decision DispatchDecision) []DispatchCandidate {
	result := append([]DispatchCandidate{}, decision.Candidates...)
	sort.Slice(result, func(left, right int) bool { return result[left].Adapter < result[right].Adapter })
	return result
}
