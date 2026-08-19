package mesh

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
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

func routeTask(repository Repository, task FrontierTask, arguments []string) (DispatchDecision, SelectedRoute, error) {
	explicit := option(arguments, "--adapter", "")
	mode := option(arguments, "--mode", "supervised")
	flagModel := option(arguments, "--model", "")
	flagProvider := option(arguments, "--provider", "")
	backend := adapterForBackend(task.ExecutionBackend)
	definitions, err := LoadAdapters()
	if err != nil {
		return DispatchDecision{}, SelectedRoute{}, err
	}
	roster, err := LoadRoster(repository)
	if err != nil {
		return DispatchDecision{}, SelectedRoute{}, err
	}
	defaultAdapterOrder := AdapterOrder(definitions)
	order := append([]string{}, defaultAdapterOrder...)
	if roster != nil {
		preferred := roster.preferredAdapters(task.Effort, task.Kind)
		if len(preferred) > 0 {
			order = prependUnique(preferred, order)
		}
	}
	advisorDigest := (*string)(nil)
	if advisorPath := option(arguments, "--advisor-file", ""); advisorPath != "" {
		raw, err := os.ReadFile(advisorPath)
		if err != nil {
			return DispatchDecision{}, SelectedRoute{}, fmt.Errorf("read advisor response: %w", err)
		}
		var advisor struct {
			Order []string `json:"order"`
		}
		if err := json.Unmarshal(raw, &advisor); err != nil {
			return DispatchDecision{}, SelectedRoute{}, fmt.Errorf("decode advisor response: %w", err)
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
	policy := map[string]any{
		"allowed_adapters": defaultAdapterOrder,
		"explicit":         explicit,
		"task_backend":     task.ExecutionBackend,
		"mode":             mode,
		"provider":         flagProvider,
		"model":            flagModel,
		"effort":           task.Effort,
		"kind":             task.Kind,
	}
	if roster != nil {
		policy["roster_digest"] = roster.Digest
		policy["require_named_model"] = roster.RequireNamedModel
	}
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
		return decision, SelectedRoute{}, fmt.Errorf("NO_ELIGIBLE_EXECUTOR: unknown explicit adapter %s", explicit)
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
		ranked = prependUnique([]string{explicit}, ranked)
	} else if mode == "autonomous" {
		ranked = prependUnique([]string{"omp-rpc"}, ranked)
	} else if backend != "" {
		ranked = prependUnique([]string{backend}, ranked)
	}
	eligible := map[string]bool{}
	for _, candidate := range decision.Candidates {
		eligible[candidate.Adapter] = candidate.Eligible
	}
	selected := ""
	for _, adapter := range ranked {
		if eligible[adapter] {
			selected = adapter
			decision.Selected = &selected
			break
		}
	}
	if decision.Selected == nil {
		decision.Explanation = "no adapter survived deterministic eligibility"
		return decision, SelectedRoute{}, fmt.Errorf("NO_ELIGIBLE_EXECUTOR")
	}
	route := SelectedRoute{
		Adapter: selected,
		Mode:    mode,
		Model:   flagModel,
		Provider: flagProvider,
		Source:  "flag",
		Effort:  task.Effort,
		Kind:    task.Kind,
	}
	if flagModel == "" && roster != nil {
		if candidate, ok := roster.modelFor(selected, task.Effort, task.Kind); ok {
			route.Model, route.Provider, route.Source = candidate.Model, firstNonEmpty(flagProvider, candidate.Provider), "roster"
			route.RosterDigest = roster.Digest
		}
	}
	if roster != nil {
		route.RosterDigest = roster.Digest
		if roster.RequireNamedModel && strings.TrimSpace(route.Model) == "" {
			decision.Explanation = "roster requires a named model and none was selected"
			return decision, route, fmt.Errorf("EMPTY_MODEL: roster requires a named model for %s at effort %s", selected, task.Effort)
		}
	}
	if flagModel != "" {
		route.Source = "flag"
	}
	decision.Explanation = "selected by explicit choice, task backend, roster band, static policy, bounded advisor order, then stable tie-breaker"
	return decision, route, nil
}

func explainRoute(repository Repository, task FrontierTask, arguments []string) CommandResponse {
	decision, route, err := routeTask(repository, task, arguments)
	if err != nil {
		code := "NO_ELIGIBLE_EXECUTOR"
		if strings.HasPrefix(err.Error(), "EMPTY_MODEL") {
			code = "EMPTY_MODEL"
		}
		return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: false, Code: code, Message: err.Error(), Data: map[string]any{"decision": decision, "route": route}}
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_ROUTE_READY", Message: "deterministic route selected", Data: map[string]any{"decision": decision, "route": route}}
}

func prependUnique(front, rest []string) []string {
	seen, result := map[string]bool{}, []string{}
	for _, name := range append(append([]string{}, front...), rest...) {
		if name == "" || seen[name] {
			continue
		}
		seen[name] = true
		result = append(result, name)
	}
	return result
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

func stableCandidates(decision DispatchDecision) []DispatchCandidate {
	result := append([]DispatchCandidate{}, decision.Candidates...)
	sort.Slice(result, func(left, right int) bool { return result[left].Adapter < result[right].Adapter })
	return result
}
