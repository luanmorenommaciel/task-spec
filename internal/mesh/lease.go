package mesh

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

var activeLeaseStates = []string{"leased", "preparing", "running", "verifying", "awaiting_supervision"}

func option(arguments []string, name, fallback string) string {
	for index := 0; index < len(arguments)-1; index++ {
		if arguments[index] == name {
			return arguments[index+1]
		}
	}
	return fallback
}

func hasOption(arguments []string, name string) bool {
	for _, argument := range arguments {
		if argument == name {
			return true
		}
	}
	return false
}

func integerOption(arguments []string, name string, fallback, minimum, maximum int) (int, error) {
	raw := option(arguments, name, strconv.Itoa(fallback))
	value, err := strconv.Atoi(raw)
	if err != nil || value < minimum || value > maximum {
		return 0, fmt.Errorf("%s must be between %d and %d", name, minimum, maximum)
	}
	return value, nil
}

func gitValue(repository Repository, arguments ...string) (string, error) {
	command := exec.Command("git", append([]string{"-C", repository.Root}, arguments...)...)
	output, err := command.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

func (store *Store) startRun(transaction *sql.Tx, request CommandRequest) CommandResponse {
	frontier, err := ResolveFrontier(store.repository)
	if err != nil {
		return failure("GRAPH_INVALID", err.Error())
	}
	maxParallel, err := integerOption(request.Arguments, "--max-parallel", 2, 1, 64)
	if err != nil {
		return failure("MESH_USAGE", err.Error())
	}
	ttl, err := integerOption(request.Arguments, "--lease-ttl", 300, 1, 86400)
	if err != nil {
		return failure("MESH_USAGE", err.Error())
	}
	mode := option(request.Arguments, "--mode", "supervised")
	if mode != "supervised" && mode != "autonomous" {
		return failure("MESH_USAGE", "--mode must be supervised or autonomous")
	}
	if mode == "autonomous" {
		if code, err := store.autonomousPreflight(request.Arguments); err != nil {
			return failure(code, err.Error())
		}
	}
	selected := []FrontierTask{}
	if taskID := option(request.Arguments, "--task", ""); taskID != "" {
		task, ok := frontier.Eligible(taskID)
		if !ok {
			return failure("TASK_NOT_ELIGIBLE", "task is not an authorized ready leaf")
		}
		selected = append(selected, task)
	} else if hasOption(request.Arguments, "--frontier") {
		if len(frontier.ConcurrencyGroups) > 0 {
			for _, taskID := range frontier.ConcurrencyGroups[0] {
				if task, ok := frontier.Eligible(taskID); ok && len(selected) < maxParallel {
					selected = append(selected, task)
				}
			}
		}
	} else {
		return failure("MESH_USAGE", "run requires --task <id> or --frontier")
	}
	if len(selected) == 0 {
		return failure("NO_ELIGIBLE_TASK", "the authorized ready frontier is empty")
	}
	targetCommit, err := gitValue(store.repository, "rev-parse", "HEAD")
	if err != nil {
		return failure("MESH_GIT_ERROR", err.Error())
	}
	targetBranch, err := gitValue(store.repository, "symbolic-ref", "--quiet", "--short", "HEAD")
	if err != nil {
		targetBranch = "detached"
	}
	runID, createdAt := NewID(), NowUTC()
	integrationBranch := "taskmesh/run/" + strings.Split(runID, "-")[0]
	integrationWorkspace, err := prepareIntegration(store.repository, runID, integrationBranch, targetCommit)
	if err != nil {
		return failure("MESH_WORKTREE_ERROR", err.Error())
	}
	if _, err := transaction.Exec(
		"INSERT INTO runs(run_id, graph_revision_digest, target_branch, target_commit, integration_branch, mode, max_parallel, state, created_at, integration_workspace) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
		runID, frontier.GraphRevisionDigest, targetBranch, targetCommit, integrationBranch, mode, maxParallel, createdAt, integrationWorkspace,
	); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	run := Run{Contract: "TaskMeshRun/v1", RunID: runID, Repository: store.repository.Root, GraphRevisionDigest: frontier.GraphRevisionDigest, IntegrationBranch: integrationBranch, Mode: mode, MaxParallel: maxParallel, State: "active", CreatedAt: createdAt}
	run.Target.Branch, run.Target.Commit = targetBranch, targetCommit
	if err := appendRunEvent(transaction, request.RequestID, runID, "", 0, "RUN_CREATED", map[string]any{"run": run}); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	leases := []Lease{}
	attempts := []map[string]any{}
	for _, task := range selected {
		decision, routeErr := routeTask(task, request.Arguments)
		if routeErr != nil || decision.Selected == nil {
			continue
		}
		lease, acquireErr := store.acquireLease(transaction, request.RequestID, runID, task, request.RequestID, time.Duration(ttl)*time.Second)
		if acquireErr != nil {
			continue
		}
		branch, workspace, prepareErr := prepareAttempt(store.repository, runID, lease, integrationBranch)
		if prepareErr != nil {
			_, _ = transaction.Exec("UPDATE leases SET state = 'parked' WHERE attempt_id = ?", lease.AttemptID)
			_ = appendRunEvent(transaction, request.RequestID, runID, lease.AttemptID, lease.FencingToken, "ATTEMPT_PARKED", map[string]any{"code": "MESH_WORKTREE_ERROR", "message": prepareErr.Error()})
			continue
		}
		decisionRaw, _ := canonicalJSON(decision)
		lease.Adapter, lease.Branch, lease.Workspace = *decision.Selected, branch, workspace
		if _, err := transaction.Exec("UPDATE leases SET adapter = ?, branch = ?, workspace = ?, decision_json = ? WHERE attempt_id = ?", lease.Adapter, branch, workspace, string(decisionRaw), lease.AttemptID); err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		route := map[string]any{"provider": option(request.Arguments, "--provider", ""), "model": option(request.Arguments, "--model", ""), "mode": mode}
		_ = appendRunEvent(transaction, request.RequestID, runID, lease.AttemptID, lease.FencingToken, "ROUTE_SELECTED", map[string]any{"decision": decision, "route": route, "branch": branch, "workspace": workspace})
		leases = append(leases, lease)
		attempts = append(attempts, map[string]any{"lease": lease, "adapter": lease.Adapter, "branch": branch, "workspace": workspace, "decision": decision})
	}
	if len(leases) == 0 {
		return failure("LEASE_CONFLICT", "another authoritative attempt already holds every selected task")
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_RUN_STARTED", Message: "authorized TaskMesh leases acquired", Data: map[string]any{"run": run, "leases": leases, "attempts": attempts}}
}

func (store *Store) acquireLease(transaction *sql.Tx, requestID, runID string, task FrontierTask, owner string, ttl time.Duration) (Lease, error) {
	if err := recoverExpiredTx(transaction, requestID, time.Now().UTC()); err != nil {
		return Lease{}, err
	}
	var activeAttempt string
	err := transaction.QueryRow(
		"SELECT attempt_id FROM leases WHERE task_revision_digest = ? AND state IN ('leased','preparing','running','verifying','awaiting_supervision') LIMIT 1",
		task.TaskRevisionDigest,
	).Scan(&activeAttempt)
	if err == nil {
		return Lease{}, fmt.Errorf("LEASE_CONFLICT: %s", activeAttempt)
	}
	if err != sql.ErrNoRows {
		return Lease{}, err
	}
	var token int64
	if err := transaction.QueryRow(
		"INSERT INTO lease_fences(task_revision_digest, token) VALUES (?, 1) ON CONFLICT(task_revision_digest) DO UPDATE SET token = token + 1 RETURNING token",
		task.TaskRevisionDigest,
	).Scan(&token); err != nil {
		return Lease{}, err
	}
	now := time.Now().UTC()
	lease := Lease{
		Contract: "RunLease/v1", RunID: runID, TaskID: task.TaskID, TaskRevisionDigest: task.TaskRevisionDigest,
		AttemptID: NewID(), FencingToken: token, Owner: owner,
		IssuedAt: now.Format(time.RFC3339Nano), ExpiresAt: now.Add(ttl).Format(time.RFC3339Nano),
		HeartbeatAt: now.Format(time.RFC3339Nano), State: "leased",
	}
	if _, err := transaction.Exec(
		"INSERT INTO leases(attempt_id, run_id, task_id, task_revision_digest, fencing_token, owner, issued_at, expires_at, heartbeat_at, state) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		lease.AttemptID, lease.RunID, lease.TaskID, lease.TaskRevisionDigest, lease.FencingToken, lease.Owner,
		lease.IssuedAt, lease.ExpiresAt, lease.HeartbeatAt, lease.State,
	); err != nil {
		return Lease{}, err
	}
	if err := appendRunEvent(transaction, requestID, runID, lease.AttemptID, token, "LEASE_ACQUIRED", map[string]any{"lease": lease}); err != nil {
		return Lease{}, err
	}
	return lease, nil
}

func scanLease(scanner interface{ Scan(...any) error }) (Lease, error) {
	var lease Lease
	lease.Contract = "RunLease/v1"
	err := scanner.Scan(&lease.RunID, &lease.TaskID, &lease.TaskRevisionDigest, &lease.AttemptID, &lease.FencingToken, &lease.Owner, &lease.IssuedAt, &lease.ExpiresAt, &lease.HeartbeatAt, &lease.State, &lease.Adapter, &lease.Branch, &lease.Workspace, &lease.AcceptanceRecord)
	return lease, err
}

const leaseColumns = "run_id, task_id, task_revision_digest, attempt_id, fencing_token, owner, issued_at, expires_at, heartbeat_at, state, COALESCE(adapter, ''), COALESCE(branch, ''), COALESCE(workspace, ''), COALESCE(acceptance_record, '')"

func (store *Store) heartbeat(transaction *sql.Tx, request CommandRequest) CommandResponse {
	attemptID := option(request.Arguments, "--attempt-id", "")
	token, err := integerOption(request.Arguments, "--fencing-token", 0, 1, int(^uint(0)>>1))
	if attemptID == "" || err != nil {
		return failure("MESH_USAGE", "heartbeat requires --attempt-id and --fencing-token")
	}
	now := time.Now().UTC()
	result, err := transaction.Exec(
		"UPDATE leases SET heartbeat_at = ?, expires_at = ? WHERE attempt_id = ? AND fencing_token = ? AND state IN ('leased','preparing','running','verifying','awaiting_supervision')",
		now.Format(time.RFC3339Nano), now.Add(5*time.Minute).Format(time.RFC3339Nano), attemptID, token,
	)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	changed, _ := result.RowsAffected()
	if changed != 1 {
		return failure("ATTEMPT_STALE", "heartbeat fencing token is no longer authoritative")
	}
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_HEARTBEAT_OK", Message: "authoritative lease renewed", Data: map[string]any{"lease": lease}}
}

func (store *Store) submit(transaction *sql.Tx, request CommandRequest) CommandResponse {
	attemptID := option(request.Arguments, "--attempt-id", "")
	token, err := integerOption(request.Arguments, "--fencing-token", 0, 1, int(^uint(0)>>1))
	if attemptID == "" || err != nil {
		return failure("MESH_USAGE", "submit requires --attempt-id and --fencing-token")
	}
	result, err := transaction.Exec(
		"UPDATE leases SET state = 'verifying', heartbeat_at = ? WHERE attempt_id = ? AND fencing_token = ? AND state IN ('leased','preparing','running')",
		NowUTC(), attemptID, token,
	)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	changed, _ := result.RowsAffected()
	if changed != 1 {
		return failure("ATTEMPT_STALE", "result fencing token is no longer authoritative")
	}
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	_ = appendRunEvent(transaction, request.RequestID, lease.RunID, lease.AttemptID, lease.FencingToken, "RESULT_SUBMITTED", map[string]any{"state": "verifying"})
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_RESULT_ACCEPTED", Message: "authoritative result entered verification", Data: map[string]any{"lease": lease}}
}

func (store *Store) cancel(transaction *sql.Tx, request CommandRequest) CommandResponse {
	if len(request.Arguments) == 0 {
		return failure("MESH_USAGE", "cancel requires an attempt ID")
	}
	attemptID := request.Arguments[0]
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return failure("ATTEMPT_NOT_FOUND", "attempt does not exist")
	}
	result, err := transaction.Exec("UPDATE leases SET state = 'cancelled', heartbeat_at = ? WHERE attempt_id = ? AND fencing_token = ? AND state IN ('leased','preparing','running','verifying','awaiting_supervision')", NowUTC(), attemptID, lease.FencingToken)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	changed, _ := result.RowsAffected()
	if changed != 1 {
		return failure("ATTEMPT_STALE", "attempt is no longer cancellable")
	}
	_ = appendRunEvent(transaction, request.RequestID, lease.RunID, lease.AttemptID, lease.FencingToken, "ATTEMPT_CANCELLED", map[string]any{"task_id": lease.TaskID})
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_CANCELLED", Message: "attempt cancelled and fenced", Data: map[string]any{"attempt_id": attemptID}}
}

func (store *Store) resume(transaction *sql.Tx, request CommandRequest) CommandResponse {
	if len(request.Arguments) == 0 {
		return failure("MESH_USAGE", "resume requires a run or attempt ID")
	}
	prior, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ? OR run_id = ? ORDER BY issued_at DESC LIMIT 1", request.Arguments[0], request.Arguments[0]))
	if err != nil {
		return failure("ATTEMPT_NOT_FOUND", "no resumable attempt exists")
	}
	if contains(activeLeaseStates, prior.State) {
		return failure("LEASE_CONFLICT", "the prior attempt is still authoritative")
	}
	var runMode string
	if err := transaction.QueryRow("SELECT mode FROM runs WHERE run_id = ?", prior.RunID).Scan(&runMode); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	routingArguments := []string{"--mode", runMode, "--adapter", prior.Adapter}
	var priorRouteRaw string
	if err := transaction.QueryRow("SELECT payload_json FROM events WHERE attempt_id = ? AND event_type = 'ROUTE_SELECTED' ORDER BY sequence DESC LIMIT 1", prior.AttemptID).Scan(&priorRouteRaw); err == nil {
		var payload map[string]any
		if json.Unmarshal([]byte(priorRouteRaw), &payload) == nil {
			if route, ok := payload["route"].(map[string]any); ok {
				if provider, ok := route["provider"].(string); ok && provider != "" {
					routingArguments = append(routingArguments, "--provider", provider)
				}
				if model, ok := route["model"].(string); ok && model != "" {
					routingArguments = append(routingArguments, "--model", model)
				}
			}
		}
	}
	if runMode == "autonomous" {
		if code, err := store.autonomousPreflight(routingArguments); err != nil {
			return failure(code, err.Error())
		}
	}
	frontier, err := ResolveFrontier(store.repository)
	if err != nil {
		return failure("GRAPH_INVALID", err.Error())
	}
	task, ok := frontier.Eligible(prior.TaskID)
	if !ok || task.TaskRevisionDigest != prior.TaskRevisionDigest {
		return failure("ATTEMPT_STALE", "task authority or graph readiness changed; create a new run")
	}
	lease, err := store.acquireLease(transaction, request.RequestID, prior.RunID, task, request.RequestID, 5*time.Minute)
	if err != nil {
		return failure("LEASE_CONFLICT", err.Error())
	}
	decision, err := routeTask(task, routingArguments)
	if err != nil || decision.Selected == nil {
		return failure("NO_ELIGIBLE_EXECUTOR", "no executor remains eligible for resumed attempt")
	}
	var integrationBranch string
	if err := transaction.QueryRow("SELECT integration_branch FROM runs WHERE run_id = ?", prior.RunID).Scan(&integrationBranch); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	branch, workspace, err := prepareAttempt(store.repository, prior.RunID, lease, integrationBranch)
	if err != nil {
		return failure("MESH_WORKTREE_ERROR", err.Error())
	}
	decisionRaw, _ := canonicalJSON(decision)
	lease.Adapter, lease.Branch, lease.Workspace = *decision.Selected, branch, workspace
	if _, err := transaction.Exec("UPDATE leases SET adapter = ?, branch = ?, workspace = ?, decision_json = ? WHERE attempt_id = ?", lease.Adapter, branch, workspace, string(decisionRaw), lease.AttemptID); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	route := map[string]any{"provider": option(routingArguments, "--provider", ""), "model": option(routingArguments, "--model", ""), "mode": runMode}
	_ = appendRunEvent(transaction, request.RequestID, prior.RunID, lease.AttemptID, lease.FencingToken, "ROUTE_SELECTED", map[string]any{"decision": decision, "route": route, "branch": branch, "workspace": workspace, "resumed_from": prior.AttemptID})
	attempt := map[string]any{"lease": lease, "adapter": lease.Adapter, "branch": branch, "workspace": workspace, "decision": decision}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_RESUMED", Message: "new fenced attempt acquired without widening the prior route", Data: map[string]any{"lease": lease, "attempts": []map[string]any{attempt}}}
}

func contains(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

func scanRun(scanner interface{ Scan(...any) error }, repository string) (Run, error) {
	var run Run
	run.Contract, run.Repository = "TaskMeshRun/v1", repository
	var finished sql.NullString
	err := scanner.Scan(&run.RunID, &run.GraphRevisionDigest, &run.Target.Branch, &run.Target.Commit, &run.IntegrationBranch, &run.Mode, &run.MaxParallel, &run.State, &run.CreatedAt, &finished)
	if finished.Valid {
		run.FinishedAt = &finished.String
	}
	return run, err
}

const runColumns = "run_id, graph_revision_digest, target_branch, target_commit, integration_branch, mode, max_parallel, state, created_at, finished_at"

func (store *Store) watchView(transaction *sql.Tx, request CommandRequest) CommandResponse {
	if len(request.Arguments) == 0 {
		return failure("MESH_USAGE", "watch requires a run ID")
	}
	runID := request.Arguments[0]
	after, err := integerOption(request.Arguments, "--after", 0, 0, int(^uint(0)>>1))
	if err != nil {
		return failure("MESH_USAGE", err.Error())
	}
	if _, err := scanRun(transaction.QueryRow("SELECT "+runColumns+" FROM runs WHERE run_id = ?", runID), store.repository.Root); err != nil {
		return failure("MESH_RUN_NOT_FOUND", "run does not exist")
	}
	all, err := eventsFrom(transaction)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	events := []Event{}
	var runLatest int64
	for _, event := range all {
		if event.RunID == runID {
			if event.Sequence > runLatest {
				runLatest = event.Sequence
			}
			if event.Sequence > int64(after) {
				events = append(events, event)
			}
		}
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_WATCH_READY", Message: "ordered durable TaskMesh history replayed", Data: map[string]any{"contract": "TaskMeshEventLog/v1", "run_id": runID, "after_sequence": after, "events": events, "latest_sequence": runLatest}}
}

func (store *Store) statusView(transaction *sql.Tx, request CommandRequest) CommandResponse {
	if len(request.Arguments) == 0 {
		events, err := eventsFrom(transaction)
		if err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_STATUS_READY", Message: "TaskMesh durable view rebuilt from events", Data: map[string]any{"contract": "TaskMeshRepositoryView/v1", "repository": store.repository.Root, "events": events, "latest_sequence": latestSequence(events)}}
	}
	identity := request.Arguments[0]
	run, err := scanRun(transaction.QueryRow("SELECT "+runColumns+" FROM runs WHERE run_id = ? OR run_id = (SELECT run_id FROM leases WHERE attempt_id = ?)", identity, identity), store.repository.Root)
	if err != nil {
		return failure("MESH_RUN_NOT_FOUND", "run or attempt does not exist")
	}
	rows, err := transaction.Query("SELECT "+leaseColumns+" FROM leases WHERE run_id = ? ORDER BY issued_at", run.RunID)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	leases := []Lease{}
	for rows.Next() {
		lease, scanErr := scanLease(rows)
		if scanErr != nil {
			rows.Close()
			return failure("MESH_STATE_ERROR", scanErr.Error())
		}
		leases = append(leases, lease)
	}
	rows.Close()
	allEvents, err := eventsFrom(transaction)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	runEvents := []Event{}
	for _, event := range allEvents {
		if event.RunID == run.RunID {
			runEvents = append(runEvents, event)
		}
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_STATUS_READY", Message: "durable run view rebuilt from events", Data: map[string]any{"contract": "TaskMeshView/v1", "run": run, "attempts": leases, "latest_sequence": latestSequence(runEvents), "generated_at": NowUTC()}}
}
