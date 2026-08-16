package mesh

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type acceptanceRecord struct {
	Contract string `json:"contract"`
	Subject  struct {
		TaskID             string `json:"task_id"`
		TaskRevisionDigest string `json:"task_revision_digest"`
		AttemptID          string `json:"attempt_id"`
		BaseCommit         string `json:"base_commit"`
	} `json:"subject"`
	Outcome struct {
		Status string `json:"status"`
		Code   string `json:"code"`
	} `json:"outcome"`
}

func safeAcceptancePath(repository Repository, raw string) (string, error) {
	if raw == "" {
		return "", fmt.Errorf("--record is required")
	}
	abs, err := filepath.Abs(raw)
	if err != nil {
		return "", err
	}
	real, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return "", err
	}
	root := filepath.Join(repository.Root, ".taskspec", "acceptance")
	rootReal, err := filepath.EvalSymlinks(root)
	if err != nil {
		return "", fmt.Errorf("canonical acceptance directory is unavailable: %w", err)
	}
	relative, err := filepath.Rel(rootReal, real)
	if err != nil || relative == ".." || filepath.IsAbs(relative) || len(relative) >= 3 && relative[:3] == ".."+string(filepath.Separator) {
		return "", fmt.Errorf("acceptance record escapes canonical storage")
	}
	return real, nil
}

func (store *Store) recordAcceptance(transaction *sql.Tx, request CommandRequest) CommandResponse {
	attemptID := option(request.Arguments, "--attempt-id", "")
	token, err := integerOption(request.Arguments, "--fencing-token", 0, 1, int(^uint(0)>>1))
	if attemptID == "" || err != nil {
		return failure("MESH_USAGE", "record-acceptance requires --attempt-id and --fencing-token")
	}
	recordPath, err := safeAcceptancePath(store.repository, option(request.Arguments, "--record", ""))
	if err != nil {
		return failure("ACCEPTANCE_FAILED", err.Error())
	}
	raw, err := os.ReadFile(recordPath)
	if err != nil {
		return failure("ACCEPTANCE_FAILED", err.Error())
	}
	var record acceptanceRecord
	if err := json.Unmarshal(raw, &record); err != nil {
		return failure("ACCEPTANCE_FAILED", err.Error())
	}
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return failure("ATTEMPT_NOT_FOUND", "attempt does not exist")
	}
	var baseCommit string
	if err := transaction.QueryRow("SELECT target_commit FROM runs WHERE run_id = ?", lease.RunID).Scan(&baseCommit); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	if lease.FencingToken != int64(token) || !contains(activeLeaseStates, lease.State) {
		return failure("ATTEMPT_STALE", "acceptance references a non-authoritative attempt")
	}
	if record.Contract != "AcceptanceRecord/v1" || record.Outcome.Status != "accepted" || record.Subject.TaskID != lease.TaskID || record.Subject.TaskRevisionDigest != lease.TaskRevisionDigest || record.Subject.AttemptID != lease.AttemptID || record.Subject.BaseCommit != baseCommit {
		return failure("ACCEPTANCE_FAILED", "AcceptanceRecord subject does not match the authoritative attempt")
	}
	if _, err := transaction.Exec("UPDATE leases SET state = 'accepted', acceptance_record = ?, heartbeat_at = ? WHERE attempt_id = ? AND fencing_token = ?", recordPath, NowUTC(), attemptID, token); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	_ = appendRunEvent(transaction, request.RequestID, lease.RunID, lease.AttemptID, lease.FencingToken, "ATTEMPT_ACCEPTED", map[string]any{"acceptance_record": recordPath})
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_ACCEPTANCE_IMPORTED", Message: "canonical Task-Spec acceptance imported", Data: map[string]any{"attempt_id": attemptID, "acceptance_record": recordPath}}
}

func (store *Store) integrate(transaction *sql.Tx, request CommandRequest) CommandResponse {
	attemptID := option(request.Arguments, "--attempt-id", "")
	if attemptID == "" {
		return failure("MESH_USAGE", "integrate requires --attempt-id")
	}
	lease, err := scanLease(transaction.QueryRow("SELECT "+leaseColumns+" FROM leases WHERE attempt_id = ?", attemptID))
	if err != nil {
		return failure("ATTEMPT_NOT_FOUND", "attempt does not exist")
	}
	if lease.State != "accepted" || lease.AcceptanceRecord == "" {
		return failure("ACCEPTANCE_FAILED", "only canonically accepted attempts can integrate")
	}
	var targetBranch, targetCommit, integrationBranch, integrationWorkspace string
	if err := transaction.QueryRow("SELECT target_branch, target_commit, integration_branch, COALESCE(integration_workspace, '') FROM runs WHERE run_id = ?", lease.RunID).Scan(&targetBranch, &targetCommit, &integrationBranch, &integrationWorkspace); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	if targetBranch != "detached" {
		currentTarget, err := gitValue(store.repository, "rev-parse", "refs/heads/"+targetBranch)
		if err != nil || currentTarget != targetCommit {
			return failure("TARGET_DIVERGED", "target branch moved; create a new explicitly authorized run")
		}
	}
	if integrationWorkspace == "" || lease.Branch == "" {
		return failure("MESH_WORKTREE_ERROR", "attempt or integration workspace is missing")
	}
	if err := runGit(store.repository, integrationWorkspace, "merge", "--no-ff", "--no-edit", lease.Branch); err != nil {
		_ = runGit(store.repository, integrationWorkspace, "merge", "--abort")
		_, _ = transaction.Exec("UPDATE leases SET state = 'parked' WHERE attempt_id = ?", attemptID)
		_ = appendRunEvent(transaction, request.RequestID, lease.RunID, lease.AttemptID, lease.FencingToken, "INTEGRATION_PARKED", map[string]any{"code": "INTEGRATION_CONFLICT"})
		return failure("INTEGRATION_CONFLICT", "attempt branch conflicts with the integration branch")
	}
	if _, err := transaction.Exec("UPDATE leases SET state = 'integrated', heartbeat_at = ? WHERE attempt_id = ?", NowUTC(), attemptID); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	_ = appendRunEvent(transaction, request.RequestID, lease.RunID, lease.AttemptID, lease.FencingToken, "ATTEMPT_INTEGRATED", map[string]any{"integration_branch": integrationBranch})
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_INTEGRATED", Message: "accepted attempt merged into the run integration branch", Data: map[string]any{"attempt_id": attemptID, "integration_branch": integrationBranch, "target_unchanged": true}}
}

func shellQuote(value string) string { return "'" + strings.ReplaceAll(value, "'", "'\\''") + "'" }

func (store *Store) finish(transaction *sql.Tx, request CommandRequest) CommandResponse {
	if len(request.Arguments) == 0 {
		return failure("MESH_USAGE", "finish requires a run ID")
	}
	runID := request.Arguments[0]
	run, err := scanRun(transaction.QueryRow("SELECT "+runColumns+" FROM runs WHERE run_id = ?", runID), store.repository.Root)
	if err != nil {
		return failure("MESH_RUN_NOT_FOUND", "run does not exist")
	}
	if run.State == "finished" {
		commands := [][]string{{"git", "checkout", run.Target.Branch}, {"git", "merge", "--no-ff", run.IntegrationBranch}}
		return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_FINISHED", Message: "run was already finished; target branch remains human-owned", Data: map[string]any{"run": run, "merge_route": map[string]any{"commands": commands, "target_unchanged": true}}, NextCommand: "git checkout " + shellQuote(run.Target.Branch) + " && git merge --no-ff " + shellQuote(run.IntegrationBranch)}
	}
	if run.State != "active" {
		return failure("RUN_INCOMPLETE", "only an active run can finish")
	}
	if run.Target.Branch != "detached" {
		current, err := gitValue(store.repository, "rev-parse", "refs/heads/"+run.Target.Branch)
		if err != nil || current != run.Target.Commit {
			return failure("TARGET_DIVERGED", "target branch moved; create a new explicitly authorized run")
		}
	}
	rows, err := transaction.Query("SELECT task_id, state, fencing_token FROM leases WHERE run_id = ? ORDER BY task_id, fencing_token DESC", runID)
	if err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	latest := map[string]string{}
	for rows.Next() {
		var taskID, state string
		var token int64
		if err := rows.Scan(&taskID, &state, &token); err != nil {
			rows.Close()
			return failure("MESH_STATE_ERROR", err.Error())
		}
		if _, exists := latest[taskID]; !exists {
			latest[taskID] = state
		}
	}
	rows.Close()
	if len(latest) == 0 {
		return failure("RUN_INCOMPLETE", "run has no attempts")
	}
	for taskID, state := range latest {
		if state != "integrated" {
			return failure("RUN_INCOMPLETE", "latest attempt for "+taskID+" is "+state)
		}
	}
	finished := NowUTC()
	if _, err := transaction.Exec("UPDATE runs SET state = 'finished', finished_at = ? WHERE run_id = ? AND state = 'active'", finished, runID); err != nil {
		return failure("MESH_STATE_ERROR", err.Error())
	}
	run.State, run.FinishedAt = "finished", &finished
	commands := [][]string{{"git", "checkout", run.Target.Branch}, {"git", "merge", "--no-ff", run.IntegrationBranch}}
	mergeRoute := map[string]any{"target_branch": run.Target.Branch, "target_commit": run.Target.Commit, "integration_branch": run.IntegrationBranch, "commands": commands, "target_unchanged": true}
	_ = appendRunEvent(transaction, request.RequestID, runID, "", 0, "RUN_FINISHED", map[string]any{"merge_route": mergeRoute})
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_FINISHED", Message: "integration branch is ready for a human-owned merge", Data: map[string]any{"run": run, "merge_route": mergeRoute}, NextCommand: "git checkout " + shellQuote(run.Target.Branch) + " && git merge --no-ff " + shellQuote(run.IntegrationBranch)}
}
