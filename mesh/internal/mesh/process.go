package mesh

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
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
	executable, arguments, err := adapterCommand(definition, lease.Workspace, prompt, timeout, lease.Model, lease.Provider)
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
	if err := store.transitionAttempt("supervision-"+NewID(), attemptID, lease.FencingToken, []string{"verifying"}, "awaiting_supervision", "SUPERVISION_REQUIRED", map[string]any{"artifact": artifact, "digest": artifactDigest, "next_command": "taskspec mesh accept " + attemptID + " --supervised-by <identity> --reason <text>"}); err != nil {
		return err
	}
	return nil
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
	return store.verifyAcceptCommitAndIntegrate(lease, handoff, probe, artifact, artifactDigest, result.StartedAt, result.FinishedAt, "autonomous", "", "", result.Receipt, os.Getenv("TASKSPEC_MESH_TRUST_REGISTRY"), result.SandboxEvidence)
}

type adapterArtifact struct {
	Contract        string `json:"contract"`
	Adapter         string `json:"adapter"`
	AdapterVersion  string `json:"adapter_version"`
	StartedAt       string `json:"started_at"`
	FinishedAt      string `json:"finished_at"`
	TerminalOutcome string `json:"terminal_outcome"`
}

func (store *Store) retainedCommand(requestID string) (CommandResponse, bool, error) {
	var raw string
	err := store.db.QueryRow("SELECT response_json FROM commands WHERE request_id = ?", requestID).Scan(&raw)
	if err == sql.ErrNoRows {
		return CommandResponse{}, false, nil
	}
	if err != nil {
		return CommandResponse{}, false, err
	}
	var response CommandResponse
	if err := json.Unmarshal([]byte(raw), &response); err != nil {
		return CommandResponse{}, false, err
	}
	return response, true, nil
}

func (store *Store) retainCommand(request CommandRequest, response CommandResponse) (CommandResponse, error) {
	response.RequestID = request.RequestID
	raw, err := canonicalJSON(response)
	if err != nil {
		return response, err
	}
	_, err = store.db.Exec("INSERT INTO commands(request_id, command, response_json, created_at) VALUES (?, ?, ?, ?)", request.RequestID, request.Command, string(raw), NowUTC())
	if err != nil {
		if retained, ok, readErr := store.retainedCommand(request.RequestID); readErr == nil && ok {
			return retained, nil
		}
		return response, err
	}
	return response, nil
}

func (store *Store) processSupervisedAccept(ctx context.Context, request CommandRequest) (CommandResponse, error) {
	if retained, ok, err := store.retainedCommand(request.RequestID); err != nil || ok {
		return retained, err
	}
	if err := store.RecoverExpired(ctx); err != nil {
		return CommandResponse{}, err
	}
	if len(request.Arguments) == 0 {
		return store.retainCommand(request, failure("MESH_USAGE", "accept requires an attempt ID, --supervised-by, and --reason"))
	}
	attemptID := request.Arguments[0]
	supervisor, reason := option(request.Arguments, "--supervised-by", ""), option(request.Arguments, "--reason", "")
	_, secrets := sanitizedEnvironment()
	reason = strings.TrimSpace(redact(reason, secrets))
	if !validRouteToken(supervisor) || reason == "" || len(reason) > 512 {
		return store.retainCommand(request, failure("MESH_USAGE", "accept requires --supervised-by <identity> and --reason <text>"))
	}
	lease, err := store.loadAttempt(attemptID)
	if err != nil {
		return store.retainCommand(request, failure("ATTEMPT_NOT_FOUND", "attempt does not exist"))
	}
	var mode string
	if err := store.db.QueryRow("SELECT mode FROM runs WHERE run_id = ?", lease.RunID).Scan(&mode); err != nil {
		return CommandResponse{}, err
	}
	if mode != "supervised" || lease.State != "awaiting_supervision" {
		return store.retainCommand(request, failure("ATTEMPT_STALE", "only a supervised attempt awaiting explicit supervision can be accepted"))
	}
	if err := store.transitionAttempt("supervision-"+NewID(), attemptID, lease.FencingToken, []string{"awaiting_supervision"}, "awaiting_supervision", "SUPERVISION_GRANTED", map[string]any{"supervised_by": supervisor, "reason": reason}); err != nil {
		return store.retainCommand(request, failure("ATTEMPT_STALE", err.Error()))
	}
	artifact := filepath.Join(store.repository.StateDir, "artifacts", attemptID+".json")
	raw, err := os.ReadFile(artifact)
	if err != nil {
		return store.retainCommand(request, failure("ACCEPTANCE_FAILED", "execution artifact is unavailable"))
	}
	var retained adapterArtifact
	if err := json.Unmarshal(raw, &retained); err != nil || retained.Contract != "TaskMeshAdapterArtifact/v1" || retained.TerminalOutcome != "success" {
		return store.retainCommand(request, failure("ACCEPTANCE_FAILED", "execution artifact is invalid or unsuccessful"))
	}
	digest := sha256.Sum256(raw)
	definitions, err := LoadAdapters()
	if err != nil {
		return store.retainCommand(request, failure("NO_ELIGIBLE_EXECUTOR", err.Error()))
	}
	definition, ok := definitions[lease.Adapter]
	if !ok {
		return store.retainCommand(request, failure("NO_ELIGIBLE_EXECUTOR", "attempt adapter is unavailable"))
	}
	handoff := filepath.Join(lease.Workspace, ".taskspec", "mesh", "handoffs", attemptID+".json")
	if _, err := os.Stat(handoff); err != nil {
		return store.retainCommand(request, failure("HANDOFF_STALE", "attempt handoff is unavailable"))
	}
	probe := ProbeAdapter(definition)
	probe.AdapterVersion, probe.Available = retained.AdapterVersion, true
	if err := store.verifyAcceptCommitAndIntegrate(lease, handoff, probe, artifact, "sha256:"+hex.EncodeToString(digest[:]), retained.StartedAt, retained.FinishedAt, "supervised", supervisor, reason, "", "", ""); err != nil {
		return store.retainCommand(request, failure("ACCEPTANCE_FAILED", err.Error()))
	}
	response := CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_SUPERVISED_ACCEPTED", Message: "explicit supervision completed canonical Task-Spec acceptance and integration", Data: map[string]any{"attempt_id": attemptID, "supervised_by": supervisor}}
	_ = ctx
	return store.retainCommand(request, response)
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

func (store *Store) verifyAcceptCommitAndIntegrate(lease Lease, handoff string, probe AdapterProbe, artifact, artifactDigest, started, finished, mode, supervisor, reason, environmentReceipt, trustRegistry, sandboxEvidence string) error {
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
		acceptArguments = append(acceptArguments, "--allow-tier2", "--supervised-by", supervisor, "--reason", reason)
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
	deviations := []string{}
	if sandboxEvidence == "" {
		deviations = append(deviations, "supervised host worktree; not a security sandbox")
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
		"artifacts": artifacts, "deviations": deviations,
	}
	raw, err := json.MarshalIndent(receipt, "", "  ")
	if err != nil {
		return err
	}
	path := filepath.Join(store.repository.StateDir, "artifacts", lease.AttemptID+"-engine-receipt.json")
	return os.WriteFile(path, append(raw, '\n'), 0o600)
}
