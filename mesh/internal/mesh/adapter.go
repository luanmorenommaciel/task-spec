package mesh

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type AdapterDefinition struct {
	Contract       string   `json:"contract"`
	Name           string   `json:"name"`
	Harness        string   `json:"harness"`
	Executable     string   `json:"executable"`
	VersionArgs    []string `json:"version_args"`
	Command        []string `json:"command"`
	PromptMode     string   `json:"prompt_mode"`
	EventFormat    string   `json:"event_format"`
	AssuranceModes []string `json:"assurance_modes"`
}

type AdapterProbe struct {
	Contract       string   `json:"contract"`
	Adapter        string   `json:"adapter"`
	AdapterVersion string   `json:"adapter_version"`
	Harness        string   `json:"harness"`
	Available      bool     `json:"available"`
	AssuranceModes []string `json:"assurance_modes"`
	Tools          []string `json:"tools"`
	Network        string   `json:"network"`
	Limits         struct {
		MaxParallel    int `json:"max_parallel"`
		MaxOutputBytes int `json:"max_output_bytes"`
		TimeoutSec     int `json:"timeout_sec"`
	} `json:"limits"`
	Executable        string `json:"executable,omitempty"`
	ReasonUnavailable string `json:"reason_unavailable,omitempty"`
	ObservedAt        string `json:"observed_at"`
}

func adapterDirectory() (string, error) {
	if explicit := os.Getenv("TASKSPEC_MESH_ADAPTER_DIR"); explicit != "" {
		return filepath.Abs(explicit)
	}
	if home := os.Getenv("TASKSPEC_HOME"); home != "" {
		return filepath.Join(home, "harness", "mesh-adapters"), nil
	}
	return "", fmt.Errorf("TASKSPEC_HOME or TASKSPEC_MESH_ADAPTER_DIR is required")
}

func LoadAdapters() (map[string]AdapterDefinition, error) {
	directory, err := adapterDirectory()
	if err != nil {
		return nil, err
	}
	paths, err := filepath.Glob(filepath.Join(directory, "*.json"))
	if err != nil {
		return nil, err
	}
	definitions := map[string]AdapterDefinition{}
	for _, path := range paths {
		raw, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		var definition AdapterDefinition
		if err := json.Unmarshal(raw, &definition); err != nil {
			return nil, fmt.Errorf("decode adapter %s: %w", path, err)
		}
		if definition.Contract != "TaskMeshAdapter/v1" || definition.Name == "" || definition.Executable == "" || len(definition.Command) == 0 {
			return nil, fmt.Errorf("invalid TaskMesh adapter: %s", path)
		}
		if definition.PromptMode != "stdin" && definition.PromptMode != "argument" {
			return nil, fmt.Errorf("adapter %s has unsupported prompt_mode", definition.Name)
		}
		if _, duplicate := definitions[definition.Name]; duplicate {
			return nil, fmt.Errorf("duplicate adapter %s", definition.Name)
		}
		definitions[definition.Name] = definition
	}
	if len(definitions) == 0 {
		return nil, fmt.Errorf("no TaskMesh adapters found in %s", directory)
	}
	return definitions, nil
}

func AdapterOrder(definitions map[string]AdapterDefinition) []string {
	preferred := []string{"codex-native", "claude-native", "grok-native", "omp-rpc"}
	result, included := []string{}, map[string]bool{}
	for _, name := range preferred {
		if _, exists := definitions[name]; exists {
			result, included[name] = append(result, name), true
		}
	}
	remainder := []string{}
	for name := range definitions {
		if !included[name] {
			remainder = append(remainder, name)
		}
	}
	sort.Strings(remainder)
	return append(result, remainder...)
}

func ProbeAdapter(definition AdapterDefinition) AdapterProbe {
	probe := AdapterProbe{Contract: "ExecutorCapability/v1", Adapter: definition.Name, Harness: definition.Harness, AssuranceModes: definition.AssuranceModes, Tools: []string{"read", "edit", "shell"}, Network: "unrestricted", ObservedAt: NowUTC()}
	probe.Limits.MaxParallel, probe.Limits.MaxOutputBytes, probe.Limits.TimeoutSec = 1, 1048576, 1800
	executable, err := exec.LookPath(definition.Executable)
	if err != nil {
		probe.AdapterVersion, probe.ReasonUnavailable = "unavailable", err.Error()
		return probe
	}
	probe.Executable = executable
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, executable, definition.VersionArgs...)
	output, err := command.CombinedOutput()
	if err != nil {
		probe.AdapterVersion, probe.ReasonUnavailable = "unavailable", strings.TrimSpace(string(output))+": "+err.Error()
		return probe
	}
	probe.Available, probe.AdapterVersion = true, strings.TrimSpace(string(output))
	return probe
}

func adapterCommand(definition AdapterDefinition, workspace, prompt string, timeout time.Duration) (string, []string, error) {
	executable, err := exec.LookPath(definition.Executable)
	if err != nil {
		return "", nil, err
	}
	arguments := make([]string, 0, len(definition.Command))
	for _, argument := range definition.Command {
		argument = strings.ReplaceAll(argument, "{workspace}", workspace)
		argument = strings.ReplaceAll(argument, "{timeout}", fmt.Sprintf("%ds", int(timeout.Seconds())))
		argument = strings.ReplaceAll(argument, "{prompt}", prompt)
		arguments = append(arguments, argument)
	}
	return executable, arguments, nil
}

func (store *Store) adaptersCommand(request CommandRequest) CommandResponse {
	definitions, err := LoadAdapters()
	if err != nil {
		return failure("NO_ELIGIBLE_EXECUTOR", err.Error())
	}
	action := "list"
	if len(request.Arguments) > 0 {
		action = request.Arguments[0]
	}
	probes := []AdapterProbe{}
	for _, name := range AdapterOrder(definitions) {
		definition := definitions[name]
		if len(request.Arguments) > 1 && request.Arguments[1] != name {
			continue
		}
		if action == "probe" {
			probes = append(probes, ProbeAdapter(definition))
		} else {
			probe := AdapterProbe{Contract: "ExecutorCapability/v1", Adapter: definition.Name, AdapterVersion: "not-probed", Harness: definition.Harness, AssuranceModes: definition.AssuranceModes, Tools: []string{"read", "edit", "shell"}, Network: "unrestricted", ObservedAt: NowUTC()}
			probe.Limits.MaxParallel, probe.Limits.MaxOutputBytes, probe.Limits.TimeoutSec = 1, 1048576, 1800
			probes = append(probes, probe)
		}
	}
	if action != "list" && action != "probe" {
		return failure("MESH_USAGE", "adapters requires list or probe")
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_ADAPTERS_READY", Message: "TaskMesh adapter capabilities resolved", Data: map[string]any{"adapters": probes}}
}
