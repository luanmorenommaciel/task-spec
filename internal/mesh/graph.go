package mesh

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

type graphNode struct {
	TaskID             string `json:"task_id"`
	Path               string `json:"path"`
	Status             string `json:"status"`
	Effort             string `json:"effort"`
	TaskRevisionDigest string `json:"task_revision_digest"`
}

type graphIssue struct {
	Code     string `json:"code"`
	Severity string `json:"severity"`
}

type graphView struct {
	Contract            string              `json:"contract"`
	GraphRevisionDigest string              `json:"graph_revision_digest"`
	Nodes               []graphNode         `json:"nodes"`
	Issues              []graphIssue        `json:"issues"`
	ReadyFrontier       []string            `json:"ready_frontier"`
	ConcurrencyGroups   [][]string          `json:"concurrency_groups"`
	BlockedReasons      map[string][]string `json:"blocked_reasons"`
}

type taskStatus struct {
	Contract      string `json:"contract"`
	TaskID        string `json:"task_id"`
	Lifecycle     string `json:"lifecycle"`
	Authorization struct {
		Tier         int    `json:"tier"`
		Verification string `json:"verification"`
		Stale        bool   `json:"stale"`
	} `json:"authorization"`
}

type cliEnvelope struct {
	OK       bool            `json:"ok"`
	ExitCode int             `json:"exit_code"`
	Data     json.RawMessage `json:"data"`
	Stderr   string          `json:"stderr"`
}

type FrontierTask struct {
	TaskID             string   `json:"task_id"`
	TaskRevisionDigest string   `json:"task_revision_digest"`
	Effort             string   `json:"effort"`
	Eligible           bool     `json:"eligible"`
	Blockers           []string `json:"blockers"`
}

type Frontier struct {
	Contract            string         `json:"contract"`
	GraphRevisionDigest string         `json:"graph_revision_digest"`
	Tasks               []FrontierTask `json:"tasks"`
	ConcurrencyGroups   [][]string     `json:"concurrency_groups"`
}

func taskSpecCLI(repository Repository) (string, error) {
	if home := os.Getenv("TASKSPEC_HOME"); home != "" {
		candidate := filepath.Join(home, "bin", "taskspec")
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			return candidate, nil
		}
	}
	candidate := filepath.Join(repository.Root, "bin", "taskspec")
	if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
		return candidate, nil
	}
	return "", fmt.Errorf("Task-Spec CLI is unavailable; set TASKSPEC_HOME")
}

func callTaskSpec(repository Repository, arguments ...string) (json.RawMessage, error) {
	cli, err := taskSpecCLI(repository)
	if err != nil {
		return nil, err
	}
	commandArguments := append([]string{cli, "--json"}, arguments...)
	command := exec.Command("bash", commandArguments...)
	command.Dir = repository.Root
	output, runErr := command.Output()
	var envelope cliEnvelope
	if err := json.Unmarshal(output, &envelope); err != nil {
		return nil, fmt.Errorf("decode Task-Spec %s: %w", arguments[0], err)
	}
	if runErr != nil || !envelope.OK {
		return nil, fmt.Errorf("Task-Spec %s rejected: %s", arguments[0], envelope.Stderr)
	}
	return envelope.Data, nil
}

func ResolveFrontier(repository Repository) (Frontier, error) {
	raw, err := callTaskSpec(repository, "graph")
	if err != nil {
		return Frontier{}, err
	}
	var graph graphView
	if err := json.Unmarshal(raw, &graph); err != nil {
		return Frontier{}, err
	}
	if graph.Contract != "TaskGraphView/v1" {
		return Frontier{}, fmt.Errorf("unsupported graph contract %q", graph.Contract)
	}
	for _, issue := range graph.Issues {
		if issue.Severity == "error" {
			return Frontier{}, fmt.Errorf("GRAPH_INVALID: %s", issue.Code)
		}
	}
	nodes := map[string]graphNode{}
	for _, node := range graph.Nodes {
		nodes[node.TaskID] = node
	}
	frontier := Frontier{Contract: "TaskMeshFrontier/v1", GraphRevisionDigest: graph.GraphRevisionDigest, Tasks: []FrontierTask{}, ConcurrencyGroups: [][]string{}}
	eligible := map[string]bool{}
	for _, taskID := range graph.ReadyFrontier {
		node, exists := nodes[taskID]
		candidate := FrontierTask{TaskID: taskID, TaskRevisionDigest: node.TaskRevisionDigest, Effort: node.Effort, Blockers: []string{}}
		if !exists {
			candidate.Blockers = append(candidate.Blockers, "GRAPH_NODE_MISSING")
		} else if node.Effort == "XL" || node.Effort == "XXL" {
			candidate.Blockers = append(candidate.Blockers, "COMPOSITION_NODE")
		}
		statusRaw, statusErr := callTaskSpec(repository, "status", taskID)
		if statusErr != nil {
			candidate.Blockers = append(candidate.Blockers, "STATUS_UNAVAILABLE")
		} else {
			var status taskStatus
			if err := json.Unmarshal(statusRaw, &status); err != nil {
				candidate.Blockers = append(candidate.Blockers, "STATUS_INVALID")
			} else {
				if status.Lifecycle != "ready" {
					candidate.Blockers = append(candidate.Blockers, "NOT_READY")
				}
				if status.Authorization.Tier != 1 || status.Authorization.Verification != "verified" || status.Authorization.Stale {
					candidate.Blockers = append(candidate.Blockers, "AUTHORIZATION_NOT_TIER1")
				}
			}
		}
		candidate.Eligible = len(candidate.Blockers) == 0
		eligible[taskID] = candidate.Eligible
		frontier.Tasks = append(frontier.Tasks, candidate)
	}
	for _, group := range graph.ConcurrencyGroups {
		filtered := []string{}
		for _, taskID := range group {
			if eligible[taskID] {
				filtered = append(filtered, taskID)
			}
		}
		if len(filtered) > 0 {
			frontier.ConcurrencyGroups = append(frontier.ConcurrencyGroups, filtered)
		}
	}
	return frontier, nil
}

func (frontier Frontier) Eligible(taskID string) (FrontierTask, bool) {
	for _, task := range frontier.Tasks {
		if task.TaskID == taskID && task.Eligible {
			return task, true
		}
	}
	return FrontierTask{}, false
}
