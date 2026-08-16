package mesh

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

type boundedBuffer struct {
	mu        sync.Mutex
	buffer    bytes.Buffer
	remaining int
	truncated bool
}

func (buffer *boundedBuffer) Write(raw []byte) (int, error) {
	buffer.mu.Lock()
	defer buffer.mu.Unlock()
	original := len(raw)
	if len(raw) > buffer.remaining {
		raw, buffer.truncated = raw[:buffer.remaining], true
	}
	if len(raw) > 0 {
		_, _ = buffer.buffer.Write(raw)
		buffer.remaining -= len(raw)
	}
	return original, nil
}

func (buffer *boundedBuffer) String() string {
	buffer.mu.Lock()
	defer buffer.mu.Unlock()
	return buffer.buffer.String()
}

func sanitizedEnvironment() ([]string, []string) {
	result, secrets := []string{}, []string{}
	for _, entry := range os.Environ() {
		name, value, _ := strings.Cut(entry, "=")
		upper := strings.ToUpper(name)
		if name == "TASKSPEC_SIGNING_KEY" || strings.Contains(upper, "EVALUATOR_PRIVATE") || strings.Contains(upper, "IDENTITY_PRIVATE") || strings.Contains(upper, "PRIVATE_KEY") || strings.Contains(upper, "SIGNING_KEY") {
			continue
		}
		if (strings.HasSuffix(upper, "_API_KEY") || strings.HasSuffix(upper, "_TOKEN")) && len(value) >= 8 {
			secrets = append(secrets, value)
		}
		result = append(result, entry)
	}
	return result, secrets
}

var credentialPattern = regexp.MustCompile(`(?i)(sk-[A-Za-z0-9_-]{8,}|(?:api[_-]?key|token)[=:][A-Za-z0-9._-]{8,})`)

func redact(value string, secrets []string) string {
	value = credentialPattern.ReplaceAllString(value, "[REDACTED]")
	for _, secret := range secrets {
		value = strings.ReplaceAll(value, secret, "[REDACTED]")
	}
	return value
}

func (store *Store) loadAttempt(attemptID string) (Lease, error) {
	return scanLease(store.db.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
}

func (store *Store) transitionAttempt(requestID, attemptID string, token int64, from []string, state, eventType string, payload map[string]any) error {
	transaction, err := store.db.Begin()
	if err != nil {
		return err
	}
	defer transaction.Rollback()
	placeholders := strings.TrimSuffix(strings.Repeat("?,", len(from)), ",")
	arguments := []any{state, NowUTC(), attemptID, token}
	for _, value := range from {
		arguments = append(arguments, value)
	}
	result, err := transaction.Exec("UPDATE leases SET state = ?, heartbeat_at = ? WHERE attempt_id = ? AND fencing_token = ? AND state IN ("+placeholders+")", arguments...)
	if err != nil {
		return err
	}
	changed, _ := result.RowsAffected()
	if changed != 1 {
		return fmt.Errorf("ATTEMPT_STALE")
	}
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return err
	}
	if err := appendRunEvent(transaction, requestID, lease.RunID, attemptID, token, eventType, payload); err != nil {
		return err
	}
	return transaction.Commit()
}

func (store *Store) GenerateHandoff(lease Lease, definition AdapterDefinition) (string, string, error) {
	cli, err := taskSpecCLI(store.repository)
	if err != nil {
		return "", "", err
	}
	statusCommand := exec.Command("bash", cli, "--json", "status", lease.TaskID)
	statusCommand.Dir = lease.Workspace
	statusCommand.Env = append(os.Environ(), "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace)
	statusOutput, err := statusCommand.Output()
	if err != nil {
		return "", "", fmt.Errorf("resolve attempt task: %w", err)
	}
	var envelope cliEnvelope
	if err := json.Unmarshal(statusOutput, &envelope); err != nil {
		return "", "", err
	}
	var status taskStatus
	if err := json.Unmarshal(envelope.Data, &status); err != nil {
		return "", "", err
	}
	directory := filepath.Join(lease.Workspace, ".taskspec", "mesh", "handoffs")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return "", "", err
	}
	handoff := filepath.Join(directory, lease.AttemptID+".json")
	command := exec.Command("bash", cli, "handoff", status.Path, "--backend", definition.Harness, "--attempt-id", lease.AttemptID, "--out", handoff)
	command.Dir = lease.Workspace
	command.Env = append(os.Environ(), "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace)
	if output, err := command.CombinedOutput(); err != nil {
		return "", "", fmt.Errorf("create TaskHandoff: %s: %w", strings.TrimSpace(string(output)), err)
	}
	raw, err := os.ReadFile(handoff)
	if err != nil {
		return "", "", err
	}
	prompt := "Execute exactly one authorized Task-Spec leaf. Read the TaskHandoff below, stay inside its write scope and budgets, do not modify the Task-Spec contract, do not spawn subagents, and do not commit. Return a concise result after the work is complete.\n\n" + string(raw)
	return handoff, prompt, nil
}

func executionTimeout() time.Duration {
	if raw := os.Getenv("TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC"); raw != "" {
		if seconds, err := strconv.Atoi(raw); err == nil && seconds > 0 && seconds <= 86400 {
			return time.Duration(seconds) * time.Second
		}
	}
	return 30 * time.Minute
}

func (store *Store) ExecuteAttempt(parent context.Context, attemptID string) error {
	lease, err := store.loadAttempt(attemptID)
	if err != nil {
		return err
	}
	definitions, err := LoadAdapters()
	if err != nil {
		return err
	}
	definition, ok := definitions[lease.Adapter]
	if !ok {
		return fmt.Errorf("NO_ELIGIBLE_EXECUTOR: %s", lease.Adapter)
	}
	var mode string
	if err := store.db.QueryRow("SELECT mode FROM runs WHERE run_id = ?", lease.RunID).Scan(&mode); err != nil {
		return err
	}
	if mode == "autonomous" {
		return store.executeAutonomousAttempt(parent, lease, definition)
	}
	probe := ProbeAdapter(definition)
	if !probe.Available {
		_ = store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"leased"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "NO_ELIGIBLE_EXECUTOR", "probe": probe})
		return fmt.Errorf("NO_ELIGIBLE_EXECUTOR: %s", probe.ReasonUnavailable)
	}
	if err := store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"leased"}, "preparing", "ADAPTER_PREPARING", map[string]any{"probe": probe}); err != nil {
		return err
	}
	handoff, prompt, err := store.GenerateHandoff(lease, definition)
	if err != nil {
		_ = store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"preparing"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "HANDOFF_FAILED", "message": err.Error()})
		return err
	}
	timeout := executionTimeout()
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()
	executable, arguments, err := adapterCommand(definition, lease.Workspace, prompt, timeout)
	if err != nil {
		return err
	}
	command := exec.CommandContext(ctx, executable, arguments...)
	command.Dir = lease.Workspace
	baseEnvironment, secrets := sanitizedEnvironment()
	command.Env = append(baseEnvironment,
		"TASKMESH_HANDOFF="+handoff,
		"TASKMESH_ATTEMPT_ID="+lease.AttemptID,
		"TASKMESH_WORKSPACE="+lease.Workspace,
	)
	if definition.PromptMode == "stdin" {
		command.Stdin = strings.NewReader(prompt)
	}
	output := &boundedBuffer{remaining: 1024 * 1024}
	command.Stdout, command.Stderr = output, output
	command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	command.Cancel = func() error {
		if command.Process == nil {
			return nil
		}
		return syscall.Kill(-command.Process.Pid, syscall.SIGTERM)
	}
	command.WaitDelay = 5 * time.Second
	started := NowUTC()
	if err := store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"preparing"}, "running", "ADAPTER_STARTED", map[string]any{"adapter": definition.Name, "version": probe.AdapterVersion}); err != nil {
		return err
	}
	runErr := command.Run()
	finished := NowUTC()
	redacted := redact(output.String(), secrets)
	artifact, artifactDigest, artifactErr := store.writeExecutionArtifact(lease, definition, probe, started, finished, redacted, output.truncated, runErr)
	if artifactErr != nil {
		return artifactErr
	}
	if runErr != nil {
		code := "EXECUTION_FAILED"
		if ctx.Err() == context.DeadlineExceeded {
			code = "EXECUTION_TIMEOUT"
		} else if ctx.Err() == context.Canceled {
			code = "EXECUTION_CANCELLED"
		}
		_ = store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"running"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": code, "artifact": artifact, "digest": artifactDigest})
		return fmt.Errorf("%s: %w", code, runErr)
	}
	if err := store.transitionAttempt("adapter-"+NewID(), attemptID, lease.FencingToken, []string{"running"}, "verifying", "ADAPTER_COMPLETED", map[string]any{"artifact": artifact, "digest": artifactDigest}); err != nil {
		return err
	}
	return store.verifyAcceptCommitAndIntegrate(lease, handoff, probe, artifact, artifactDigest, started, finished, "supervised", "", "", "")
}

func (store *Store) executeAutonomousAttempt(parent context.Context, lease Lease, definition AdapterDefinition) error {
	setup, err := store.loadSandboxSetup()
	if err != nil {
		_ = store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"leased"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "SANDBOX_UNAVAILABLE", "message": err.Error()})
		return codedError{Code: "SANDBOX_UNAVAILABLE", Message: err.Error()}
	}
	provider, model := "", ""
	var decisionRaw string
	if err := store.db.QueryRow("SELECT COALESCE(decision_json, '') FROM leases WHERE attempt_id = ?", lease.AttemptID).Scan(&decisionRaw); err != nil {
		return err
	}
	var decision map[string]any
	if err := json.Unmarshal([]byte(decisionRaw), &decision); err == nil {
		// Provider and model are sealed into the routing policy digest and recovered from the run event below.
		_ = decision
	}
	var payloadRaw string
	err = store.db.QueryRow("SELECT payload_json FROM events WHERE attempt_id = ? AND event_type = 'ROUTE_SELECTED' ORDER BY sequence DESC LIMIT 1", lease.AttemptID).Scan(&payloadRaw)
	if err == nil {
		var payload map[string]any
		if json.Unmarshal([]byte(payloadRaw), &payload) == nil {
			if route, ok := payload["route"].(map[string]any); ok {
				provider, _ = route["provider"].(string)
				model, _ = route["model"].(string)
			}
		}
	}
	if provider == "" || model == "" {
		_ = store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"leased"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "CREDENTIAL_BOUNDARY_UNVERIFIED"})
		return codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: "autonomous route lost its fixed provider or model"}
	}
	probe := AdapterProbe{Contract: "ExecutorCapability/v1", Adapter: definition.Name, AdapterVersion: "omp/" + setup.OMPVersion, Harness: definition.Harness, Available: true, AssuranceModes: []string{"autonomous"}, Tools: []string{"read", "edit", "shell"}, Network: "attempt_proxy_only", Executable: setup.ImageDigest, ObservedAt: NowUTC()}
	probe.Limits.MaxParallel, probe.Limits.MaxOutputBytes, probe.Limits.TimeoutSec = 1, 1048576, int(executionTimeout().Seconds())
	if err := store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"leased"}, "preparing", "SANDBOX_PREPARING", map[string]any{"probe": probe, "image_digest": setup.ImageDigest}); err != nil {
		return err
	}
	handoff, prompt, err := store.GenerateHandoff(lease, definition)
	if err != nil {
		_ = store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"preparing"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "HANDOFF_FAILED", "message": err.Error()})
		return err
	}
	if err := store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"preparing"}, "running", "SANDBOX_STARTED", map[string]any{"runtime": setup.Runtime, "image_digest": setup.ImageDigest}); err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(parent, executionTimeout())
	defer cancel()
	result, runErr := store.runSandbox(ctx, lease, handoff, prompt, provider, model, setup)
	artifact, artifactDigest, artifactErr := store.writeExecutionArtifact(lease, definition, probe, result.StartedAt, result.FinishedAt, redact(result.Output, nil), result.Truncated, runErr)
	if artifactErr != nil {
		return artifactErr
	}
	if runErr != nil {
		code := "EXECUTION_FAILED"
		if typed, ok := runErr.(codedError); ok {
			code = typed.Code
		}
		_ = store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"running"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": code, "artifact": artifact, "digest": artifactDigest})
		return runErr
	}
	if err := store.finalizeSandboxEvidence(lease, handoff, artifact, artifactDigest, &result); err != nil {
		code := "CREDENTIAL_BOUNDARY_UNVERIFIED"
		if typed, ok := err.(codedError); ok {
			code = typed.Code
		}
		_ = store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"running"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": code, "message": err.Error()})
		return err
	}
	if err := store.transitionAttempt("sandbox-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"running"}, "verifying", "SANDBOX_COMPLETED", map[string]any{"artifact": artifact, "digest": artifactDigest, "sandbox_evidence": result.SandboxEvidence}); err != nil {
		return err
	}
	return store.verifyAcceptCommitAndIntegrate(lease, handoff, probe, artifact, artifactDigest, result.StartedAt, result.FinishedAt, "autonomous", result.Receipt, os.Getenv("TASKSPEC_MESH_TRUST_REGISTRY"), result.SandboxEvidence)
}

func (store *Store) writeExecutionArtifact(lease Lease, definition AdapterDefinition, probe AdapterProbe, started, finished, output string, truncated bool, runErr error) (string, string, error) {
	directory := filepath.Join(store.repository.StateDir, "artifacts")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return "", "", err
	}
	path := filepath.Join(directory, lease.AttemptID+".json")
	outcome := "success"
	if runErr != nil {
		outcome = "failed"
	}
	artifact := map[string]any{
		"contract": "TaskMeshAdapterArtifact/v1", "task_id": lease.TaskID, "task_revision_digest": lease.TaskRevisionDigest,
		"attempt_id": lease.AttemptID, "fencing_token": lease.FencingToken, "adapter": definition.Name,
		"adapter_version": probe.AdapterVersion, "started_at": started, "finished_at": finished,
		"terminal_outcome": outcome, "output": output, "truncated": truncated,
	}
	raw, err := json.MarshalIndent(artifact, "", "  ")
	if err != nil {
		return "", "", err
	}
	raw = append(raw, '\n')
	if err := os.WriteFile(path, raw, 0o600); err != nil {
		return "", "", err
	}
	digest := sha256.Sum256(raw)
	return path, "sha256:" + hex.EncodeToString(digest[:]), nil
}

func copyNonClobbering(source, destination string) error {
	raw, err := os.ReadFile(source)
	if err != nil {
		return err
	}
	if existing, err := os.ReadFile(destination); err == nil {
		if bytes.Equal(existing, raw) {
			return nil
		}
		return fmt.Errorf("acceptance record collision: %s", destination)
	}
	if err := os.MkdirAll(filepath.Dir(destination), 0o700); err != nil {
		return err
	}
	file, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	if _, err := io.Copy(file, bytes.NewReader(raw)); err != nil {
		file.Close()
		return err
	}
	return file.Close()
}

func (store *Store) verifyAcceptCommitAndIntegrate(lease Lease, handoff string, probe AdapterProbe, artifact, artifactDigest, started, finished, mode, environmentReceipt, trustRegistry, sandboxEvidence string) error {
	cli, err := taskSpecCLI(store.repository)
	if err != nil {
		return err
	}
	statusCommand := exec.Command("bash", cli, "--json", "status", lease.TaskID)
	statusCommand.Dir = lease.Workspace
	statusCommand.Env = append(os.Environ(), "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace)
	statusOutput, err := statusCommand.Output()
	if err != nil {
		return err
	}
	var statusEnvelope cliEnvelope
	if err := json.Unmarshal(statusOutput, &statusEnvelope); err != nil {
		return err
	}
	var status taskStatus
	if err := json.Unmarshal(statusEnvelope.Data, &status); err != nil {
		return err
	}
	acceptArguments := []string{"--json", "accept", "--stamp", "--handoff", handoff}
	if mode == "autonomous" {
		acceptArguments = append(acceptArguments, "--accepted-by", "taskmesh-autonomous", "--environment-receipt", environmentReceipt, "--trust-registry", trustRegistry)
	} else {
		acceptArguments = append(acceptArguments, "--allow-tier2", "--supervised-by", "taskmesh", "--reason", "supervised host worktree execution")
	}
	acceptArguments = append(acceptArguments, status.Path)
	accept := exec.Command("bash", append([]string{cli}, acceptArguments...)...)
	accept.Dir = lease.Workspace
	accept.Env = append(os.Environ(), "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace)
	acceptOutput, err := accept.Output()
	if err != nil {
		_ = store.transitionAttempt("verify-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"verifying"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "ACCEPTANCE_FAILED", "output": redact(string(acceptOutput), nil)})
		return fmt.Errorf("ACCEPTANCE_FAILED")
	}
	var acceptEnvelope cliEnvelope
	if err := json.Unmarshal(acceptOutput, &acceptEnvelope); err != nil {
		return err
	}
	var finalized struct {
		AcceptanceRecord string `json:"acceptance_record"`
	}
	if err := json.Unmarshal(acceptEnvelope.Data, &finalized); err != nil || finalized.AcceptanceRecord == "" {
		return fmt.Errorf("ACCEPTANCE_FAILED: missing AcceptanceFinalized record")
	}
	transition := exec.Command("bash", cli, "transition", lease.TaskID, "done")
	transition.Dir = lease.Workspace
	transition.Env = append(os.Environ(), "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace)
	if output, err := transition.CombinedOutput(); err != nil {
		return fmt.Errorf("transition accepted task: %s: %w", strings.TrimSpace(string(output)), err)
	}
	if err := runGit(store.repository, lease.Workspace, "add", "-A"); err != nil {
		return err
	}
	if err := runGit(store.repository, lease.Workspace, "commit", "--quiet", "-m", "TaskMesh: complete "+lease.TaskID); err != nil {
		return err
	}
	destination := filepath.Join(store.repository.Root, ".taskspec", "acceptance", lease.TaskID, lease.AttemptID+".json")
	if err := copyNonClobbering(finalized.AcceptanceRecord, destination); err != nil {
		return err
	}
	recordResult, err := store.Process(context.Background(), CommandRequest{RequestID: "accept-" + lease.AttemptID, Command: "record-acceptance", Arguments: []string{"--attempt-id", lease.AttemptID, "--fencing-token", fmt.Sprint(lease.FencingToken), "--record", destination}})
	if err != nil || !recordResult.OK {
		return fmt.Errorf("ACCEPTANCE_FAILED: import canonical record")
	}
	integrateResult, err := store.Process(context.Background(), CommandRequest{RequestID: "integrate-" + lease.AttemptID, Command: "integrate", Arguments: []string{"--attempt-id", lease.AttemptID}})
	if err != nil || !integrateResult.OK {
		return fmt.Errorf("INTEGRATION_FAILED: %s", integrateResult.Code)
	}
	return store.writeEngineReceipt(lease, handoff, probe, artifact, artifactDigest, started, finished, destination, sandboxEvidence)
}

func (store *Store) writeEngineReceipt(lease Lease, handoff string, probe AdapterProbe, artifact, artifactDigest, started, finished, acceptance, sandboxEvidence string) error {
	handoffRaw, err := os.ReadFile(handoff)
	if err != nil {
		return err
	}
	var handoffValue map[string]any
	if err := json.Unmarshal(handoffRaw, &handoffValue); err != nil {
		return err
	}
	handoffHash := sha256.Sum256(handoffRaw)
	artifacts := []map[string]any{{"path": artifact, "digest": artifactDigest}, {"path": acceptance}}
	if sandboxEvidence != "" {
		artifacts = append(artifacts, map[string]any{"path": sandboxEvidence})
	}
	receipt := map[string]any{
		"contract": "EngineRunReceipt/v2", "subject": map[string]any{
			"task_id": lease.TaskID, "task_revision_digest": lease.TaskRevisionDigest,
			"authorization_ref": handoffValue["authorization"].(map[string]any)["ref"],
			"attempt_id":        lease.AttemptID, "base_commit": handoffValue["source"].(map[string]any)["base_commit"],
		},
		"observed_at": finished, "run_id": lease.RunID, "handoff_digest": "sha256:" + hex.EncodeToString(handoffHash[:]),
		"provider": probe.Harness, "model_id": "adapter-selected", "adapter_version": probe.AdapterVersion,
		"engine_version": probe.AdapterVersion, "environment_digest": artifactDigest, "started_at": started,
		"finished_at": finished, "attempts": 1, "terminal_outcome": "accepted", "acceptance_verdict": "accepted",
		"artifacts": artifacts, "deviations": []string{},
	}
	raw, err := json.MarshalIndent(receipt, "", "  ")
	if err != nil {
		return err
	}
	path := filepath.Join(store.repository.StateDir, "artifacts", lease.AttemptID+"-engine-receipt.json")
	return os.WriteFile(path, append(raw, '\n'), 0o600)
}
