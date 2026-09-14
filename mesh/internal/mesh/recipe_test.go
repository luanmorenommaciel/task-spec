package mesh

import (
	"context"
	"errors"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func recipeStore(t *testing.T) (*Store, Lease) {
	t.Helper()
	root := t.TempDir()
	if out, err := exec.Command("git", "init", "-q", root).CombinedOutput(); err != nil {
		t.Fatalf("git: %v %s", err, out)
	}
	repo, err := ResolveRepository(root)
	if err != nil {
		t.Fatal(err)
	}
	store, err := OpenStore(repo)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { store.Close() })
	now := NowUTC()
	expiry := time.Now().UTC().Add(time.Hour).Format(time.RFC3339)
	_, err = store.db.Exec("INSERT INTO runs(run_id,graph_revision_digest,target_branch,target_commit,integration_branch,mode,max_parallel,state,created_at) VALUES ('run','graph','main','base','int','supervised',1,'active',?)", now)
	if err != nil {
		t.Fatal(err)
	}
	_, err = store.db.Exec("INSERT INTO leases(attempt_id,run_id,task_id,task_revision_digest,fencing_token,owner,issued_at,expires_at,heartbeat_at,state) VALUES ('attempt','run','task','revision',1,'test',?,?,?,'running')", now, expiry, now)
	if err != nil {
		t.Fatal(err)
	}
	return store, Lease{RunID: "run", TaskID: "task", TaskRevisionDigest: "revision", AttemptID: "attempt", FencingToken: 1, Workspace: root}
}

func TestRecipeBudgetPersistsAcrossReplacement(t *testing.T) {
	store, lease := recipeStore(t)
	recipe := &executionRecipe{MaxRounds: 3, NoProgress: 2}
	n, deadline, err := store.reserveRecipeRound(lease, recipe, 30)
	if err != nil || n != 1 {
		t.Fatalf("first: %d %v", n, err)
	}
	// A different attempt of the same revision consumes the same durable budget.
	_, err = store.db.Exec("UPDATE leases SET attempt_id='replacement',fencing_token=2 WHERE attempt_id='attempt'")
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err = store.reserveRecipeRound(lease, recipe, 30); err == nil {
		t.Fatal("stale attempt reserved a round")
	}
	lease.AttemptID = "replacement"
	lease.FencingToken = 2
	n, same, err := store.reserveRecipeRound(lease, recipe, 30)
	if err != nil || n != 2 || !same.Equal(deadline) {
		t.Fatalf("resume reset budget/deadline: %d %v", n, err)
	}
	if _, _, err = store.reserveRecipeRound(lease, recipe, 30); err != nil {
		t.Fatal(err)
	}
	if _, _, err = store.reserveRecipeRound(lease, recipe, 30); err == nil || !strings.Contains(err.Error(), "EXHAUSTED") {
		t.Fatalf("budget not enforced: %v", err)
	}
}

func TestRecipeNoProgressAndFencing(t *testing.T) {
	store, lease := recipeStore(t)
	recipe := &executionRecipe{MaxRounds: 5, NoProgress: 2}
	if _, _, err := store.reserveRecipeRound(lease, recipe, 30); err != nil {
		t.Fatal(err)
	}
	for _, fingerprint := range []string{"eval_1:digest-a", "eval_1:digest-b", "eval_1:digest-b"} {
		if _, err := store.recordRecipeFailure(lease, fingerprint); err != nil {
			t.Fatal(err)
		}
	}
	if _, _, err := store.reserveRecipeRound(lease, recipe, 30); err == nil || !strings.Contains(err.Error(), "NO_PROGRESS") {
		t.Fatalf("breaker: %v", err)
	}
	if _, err := store.db.Exec("UPDATE leases SET state='cancelled'"); err != nil {
		t.Fatal(err)
	}
	if _, err := store.recordRecipeFailure(lease, "new"); err == nil {
		t.Fatal("cancelled attempt changed failure accounting")
	}
}

func TestRecipeTotalTimeoutAndCancellation(t *testing.T) {
	store, lease := recipeStore(t)
	recipe := &executionRecipe{MaxRounds: 3, NoProgress: 2}
	if _, _, err := store.reserveRecipeRound(lease, recipe, 30); err != nil {
		t.Fatal(err)
	}
	if _, err := store.db.Exec("UPDATE recipe_budgets SET deadline=?", time.Now().Add(-time.Second).UTC().Format(time.RFC3339Nano)); err != nil {
		t.Fatal(err)
	}
	if _, _, err := store.reserveRecipeRound(lease, recipe, 30); err == nil || !strings.Contains(err.Error(), "TIMEOUT") {
		t.Fatal("timeout reset")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := managedCommand(ctx, lease.Workspace, "sh", []string{"-c", "sleep 5"}, "", os.Environ()); err == nil {
		t.Fatal("cancelled command ran")
	}
}

func TestRecipeRefusesRequiredCapabilityBeforeInvocation(t *testing.T) {
	store, lease := recipeStore(t)
	handoff := recipeHandoff{}
	handoff.Agent.Timeout = 30
	handoff.Agent.Recipe = &executionRecipe{Contract: "TaskExecutionRecipe/v1", MaxRounds: 3, NoProgress: 2, Required: []string{"managed_recipe_v1", "hard_token_budget"}}
	err := store.executeManagedRecipe(context.Background(), lease, AdapterDefinition{}, AdapterProbe{}, "", "", handoff)
	if err == nil || !strings.Contains(err.Error(), "RECIPE_CAPABILITY_UNAVAILABLE") {
		t.Fatalf("missing capability ran: %v", err)
	}
	var count int
	if err = store.db.QueryRow("SELECT COUNT(*) FROM recipe_budgets").Scan(&count); err != nil || count != 0 {
		t.Fatalf("unsupported capability consumed a round: %d %v", count, err)
	}
}

func TestRecipeIdentityPreservesUnknownAndReportedValues(t *testing.T) {
	unknown := recipeIdentity("", "", "")
	if unknown["model"] != nil || unknown["provider"] != nil {
		t.Fatal("inferred unreported model/provider")
	}
	reported := recipeIdentity("{\"model\":\"reported-model\"}\n{\"modelUsage\":{\"helper-model\":{}}}", "chosen-model", "chosen-provider")
	if reported["model"] != "chosen-model" || reported["provider"] != "chosen-provider" || len(reported["reported_models"].([]string)) != 2 {
		t.Fatal(reported)
	}
}

func TestManagedClaudeLoadsOnlyDeclaredMCPContext(t *testing.T) {
	definition := AdapterDefinition{Name: "claude-native"}
	handoff := recipeHandoff{}
	if !contains(managedAdapterArguments(definition, handoff, []string{"-p"}), "--strict-mcp-config") {
		t.Fatal("undeclared global MCP configuration loaded")
	}
	if !contains(managedAdapterArguments(definition, handoff, []string{"-p"}), "--restricted") {
		t.Fatal("undeclared user hooks loaded")
	}
	handoff.Agent.MCPDependencies = []string{"declared-server"}
	if contains(managedAdapterArguments(definition, handoff, []string{"-p"}), "--strict-mcp-config") {
		t.Fatal("declared MCP dependencies discarded")
	}
}

func TestRecipeEvalEvidenceAndScope(t *testing.T) {
	failures, err := failingRecipeEvals("{\"eval\":\"eval_1\",\"status\":\"fail\"}\n{\"eval\":\"_exit_check\",\"status\":\"pass\"}", []string{"eval_1"})
	if err != nil || len(failures) != 1 {
		t.Fatalf("eval result %v %v", failures, err)
	}
	if _, err = failingRecipeEvals("", []string{"eval_1"}); err == nil {
		t.Fatal("missing eval evidence accepted")
	}
	_, lease := recipeStore(t)
	for _, args := range [][]string{{"config", "user.email", "fixture@example.invalid"}, {"config", "user.name", "fixture"}, {"commit", "--allow-empty", "-qm", "fixture"}} {
		cmd := exec.Command("git", args...)
		cmd.Dir = lease.Workspace
		if err := cmd.Run(); err != nil {
			t.Fatal(err)
		}
	}
	handoff := recipeHandoff{}
	handoff.Source.Base = "HEAD"
	handoff.Scope.Creates = []string{"allowed.txt"}
	if err := os.WriteFile(filepath.Join(lease.Workspace, "allowed.txt"), []byte("result"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := recipeScopeDigest(context.Background(), lease, handoff); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(lease.Workspace, "outside.txt"), []byte("bad"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := recipeScopeDigest(context.Background(), lease, handoff); err == nil {
		t.Fatal("scope escape accepted")
	}
}

func TestRecipeUsageRemainsReported(t *testing.T) {
	if recipeUsage("no measurement") != nil {
		t.Fatal("missing usage became zero")
	}
	usage := recipeUsage(`{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3},"total_cost_usd":0.02}`)
	if usage["input_tokens"] != float64(12) || usage["claim"] != "reported_by_harness" {
		t.Fatal(usage)
	}
}

func TestLeaseClaimsSerializeAcrossRuns(t *testing.T) {
	store, lease := recipeStore(t)
	tx, err := store.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	candidate := FrontierTask{TaskID: "other", TaskRevisionDigest: "other-revision", ClaimedPaths: []string{"independent.txt"}, ClaimedResources: []string{"database"}}
	if err = checkLeaseClaims(tx, candidate); err == nil {
		t.Fatal("pre-upgrade unknown scope was ignored")
	}
	for _, claim := range [][2]string{{"marker", "v1"}, {"resource", "database"}, {"path", "src"}} {
		if _, err = tx.Exec("INSERT INTO lease_claims(attempt_id,kind,value) VALUES (?,?,?)", lease.AttemptID, claim[0], claim[1]); err != nil {
			t.Fatal(err)
		}
	}
	if err = checkLeaseClaims(tx, candidate); err == nil || !strings.Contains(err.Error(), "RESOURCE_LEASE_CONFLICT") {
		t.Fatalf("resource contention ignored: %v", err)
	}
	candidate.ClaimedResources = nil
	candidate.ClaimedPaths = []string{"src/child/file.go"}
	if err = checkLeaseClaims(tx, candidate); err == nil || !strings.Contains(err.Error(), "WRITE_LEASE_CONFLICT") {
		t.Fatalf("write contention ignored: %v", err)
	}
	if _, err = tx.Exec("UPDATE leases SET state='cancelled'"); err != nil {
		t.Fatal(err)
	}
	if err = checkLeaseClaims(tx, candidate); err != nil {
		t.Fatal("cancelled lease retained claims", err)
	}
}

func TestManagedRecipeCapabilityModes(t *testing.T) {
	for _, modes := range [][]string{{"supervised", "autonomous"}, {"autonomous"}} {
		probe := ProbeAdapter(AdapterDefinition{Name: "missing-test-adapter", Executable: "taskspec-nonexistent-probe", AssuranceModes: modes})
		if contains(modes, "supervised") {
			if len(probe.ManagedRecipeModes) != 1 || probe.ManagedRecipeModes[0] != "supervised" {
				t.Fatalf("recipe modes overstate assurance: %v", probe.ManagedRecipeModes)
			}
		} else if len(probe.ManagedRecipeModes) != 0 || len(probe.ManagedRecipeCapabilities) != 0 {
			t.Fatal("autonomous-only adapter advertised managed recipes")
		}
	}
}

func TestCredentialRotationPreservesHistoryAndMigratesV39(t *testing.T) {
	store, lease := recipeStore(t)
	lease.ExpiresAt = time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)
	first, _, err := store.issueCredential(lease, "test", "fixed-model", "http://127.0.0.1")
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err = store.issueCredential(lease, "test", "fixed-model", "http://127.0.0.1"); err == nil {
		t.Fatal("issued two live capabilities for one attempt")
	}
	store.setCredentialState(lease.AttemptID, "revoked")
	// Reconstruct the previously shipped table before reopening the store.
	var schema string
	if err = store.db.QueryRow("SELECT sql FROM sqlite_master WHERE name='credential_leases'").Scan(&schema); err != nil {
		t.Fatal(err)
	}
	tx, err := store.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	for _, statement := range []string{
		"DROP INDEX one_active_credential",
		"ALTER TABLE credential_leases RENAME TO fixture_credentials",
		strings.Replace(schema, "NOT NULL REFERENCES", "NOT NULL UNIQUE REFERENCES", 1),
		"INSERT INTO credential_leases SELECT * FROM fixture_credentials",
		"DROP TABLE fixture_credentials",
	} {
		if _, err = tx.Exec(statement); err != nil {
			tx.Rollback()
			t.Fatal(err)
		}
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	repository := store.repository
	store.Close()
	reopened, err := OpenStore(repository)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	second, _, err := reopened.issueCredential(lease, "test", "fixed-model", "http://127.0.0.1")
	if err != nil || first.LeaseID == second.LeaseID {
		t.Fatalf("rotation: %v", err)
	}
	reopened.setCredentialState(lease.AttemptID, "active")
	var oldState, newState string
	reopened.db.QueryRow("SELECT state FROM credential_leases WHERE lease_id=?", first.LeaseID).Scan(&oldState)
	reopened.db.QueryRow("SELECT state FROM credential_leases WHERE lease_id=?", second.LeaseID).Scan(&newState)
	if oldState != "revoked" || newState != "active" {
		t.Fatalf("history changed: %s %s", oldState, newState)
	}
	reopened.setCredentialState(lease.AttemptID, "revoked")
}

func TestAttestedRecipeCapabilityIsRestrictedToOMP(t *testing.T) {
	for _, name := range []string{"omp-rpc", "custom-sandbox"} {
		probe := ProbeAdapter(AdapterDefinition{Name: name, Executable: "taskspec-nonexistent-probe", AssuranceModes: []string{"supervised", "autonomous"}})
		if contains(probe.ManagedRecipeModes, "autonomous") != (name == "omp-rpc") {
			t.Fatalf("wrong attested capability for %s: %v", name, probe.ManagedRecipeModes)
		}
	}
}

func TestAcceptanceEvaluationHonorsManagedCancellation(t *testing.T) {
	store, lease := recipeStore(t)
	root := store.repository.Root
	lease.Workspace = root
	t.Setenv("TASKSPEC_HOME", root)
	if err := os.MkdirAll(filepath.Join(root, "bin"), 0700); err != nil {
		t.Fatal(err)
	}
	cli := `#!/usr/bin/env bash
set -eu
case "$2" in
  status) printf '%s\n' '{"data":{"path":"task.md"}}' ;;
  accept) touch evaluation-started; sleep 0.3; touch evaluation-escaped; exit 1 ;;
  *) exit 1 ;;
esac
`
	if err := os.WriteFile(filepath.Join(root, "bin", "taskspec"), []byte(cli), 0700); err != nil {
		t.Fatal(err)
	}
	handoff := filepath.Join(root, "handoff.json")
	if err := os.WriteFile(handoff, []byte(`{}`), 0600); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	finished := make(chan error, 1)
	go func() {
		finished <- store.verifyAcceptCommitAndIntegrateWithin(ctx, lease, handoff, AdapterProbe{}, "", "", "", "", "autonomous", "", "", "", "", "")
	}()
	deadline := time.Now().Add(5 * time.Second)
	for {
		if _, err := os.Stat(filepath.Join(root, "evaluation-started")); err == nil {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("acceptance evaluator did not start")
		}
		time.Sleep(5 * time.Millisecond)
	}
	cancel()
	select {
	case err := <-finished:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("acceptance ignored cancellation: %v", err)
		}
	case <-time.After(time.Second):
		t.Fatal("acceptance evaluation outlived cancellation")
	}
	time.Sleep(350 * time.Millisecond)
	if _, err := os.Stat(filepath.Join(root, "evaluation-escaped")); !os.IsNotExist(err) {
		t.Fatal("evaluation child process outlived its managed run")
	}
}

func TestExecutingLeaseRenewsWithoutRefundingRecipeBudget(t *testing.T) {
	store, lease := recipeStore(t)
	_, originalDeadline, err := store.reserveRecipeRound(lease, &executionRecipe{MaxRounds: 3, NoProgress: 2}, 10)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	lease.IssuedAt = now.Format(time.RFC3339Nano)
	lease.ExpiresAt = now.Add(time.Second).Format(time.RFC3339Nano)
	if _, err = store.db.Exec("UPDATE leases SET issued_at=?,expires_at=? WHERE attempt_id=?", lease.IssuedAt, lease.ExpiresAt, lease.AttemptID); err != nil {
		t.Fatal(err)
	}
	daemon := &Daemon{store: store}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	finished := make(chan struct{})
	go func() { daemon.renewExecutingLease(ctx, lease, cancel); close(finished) }()
	time.Sleep(1300 * time.Millisecond)
	if err = store.RecoverExpired(context.Background()); err != nil {
		t.Fatal(err)
	}
	current, err := store.loadAttempt(lease.AttemptID)
	if err != nil || current.State != "running" {
		t.Fatalf("live execution lost its lease: %v %s", err, current.State)
	}
	var used int
	var deadline string
	if err = store.db.QueryRow("SELECT used,deadline FROM recipe_budgets WHERE task_id=?", lease.TaskID).Scan(&used, &deadline); err != nil {
		t.Fatal(err)
	}
	if used != 1 || deadline != originalDeadline.Format(time.RFC3339Nano) {
		t.Fatal("renewal changed the signed execution budget")
	}
	result, err := store.Process(context.Background(), CommandRequest{RequestID: NewID(), Command: "cancel", Arguments: []string{lease.AttemptID}})
	if err != nil || !result.OK {
		t.Fatalf("cancel: %v %#v", err, result)
	}
	select {
	case <-finished:
	case <-time.After(time.Second):
		t.Fatal("renewal did not cancel execution after authority ended")
	}
	current, _ = store.loadAttempt(lease.AttemptID)
	if current.State != "cancelled" || ctx.Err() == nil {
		t.Fatal("renewal revived a cancelled attempt")
	}
}

func TestManagedWorkspacesStayOutsideGitMetadata(t *testing.T) {
	store, _ := recipeStore(t)
	repo := store.repository
	for _, args := range [][]string{{"config", "user.name", "fixture"}, {"config", "user.email", "fixture@example.invalid"}} {
		if err := runGit(repo, repo.Root, args...); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(repo.Root, "source.txt"), []byte("original"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := runGit(repo, repo.Root, "add", "source.txt"); err != nil {
		t.Fatal(err)
	}
	if err := runGit(repo, repo.Root, "commit", "-qm", "fixture"); err != nil {
		t.Fatal(err)
	}
	base, err := gitValue(repo, "rev-parse", "HEAD")
	if err != nil {
		t.Fatal(err)
	}
	integration, err := prepareIntegration(repo, "test-run", "test-integration", base)
	if err != nil {
		t.Fatal(err)
	}
	_, workspace, err := prepareAttempt(repo, "test-run", Lease{TaskID: "T-20260914-fixture", AttemptID: "test-attempt"}, "test-integration")
	if err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{integration, workspace} {
		relative, err := filepath.Rel(repo.GitCommon, path)
		if err != nil || !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
			t.Fatalf("source worktree lives in Git metadata: %s", path)
		}
		if !strings.HasPrefix(path, filepath.Join(repo.StateDir, "workspaces")+string(filepath.Separator)) {
			t.Fatalf("unexpected workspace: %s", path)
		}
	}
	if err := os.WriteFile(filepath.Join(workspace, "source.txt"), []byte("candidate"), 0600); err != nil {
		t.Fatal(err)
	}
	original, err := os.ReadFile(filepath.Join(repo.Root, "source.txt"))
	if err != nil || string(original) != "original" {
		t.Fatal("attempt changed target checkout")
	}
	if head, _ := gitValue(repo, "rev-parse", "HEAD"); head != base {
		t.Fatal("attempt changed target branch")
	}
	outside := t.TempDir()
	linked := filepath.Join(repo.StateDir, "workspaces", "linked-run")
	if err := os.Symlink(outside, linked); err != nil {
		t.Fatal(err)
	}
	if _, err := managedWorkspaceRoot(repo, "linked-run"); err == nil {
		t.Fatal("managed workspace followed a symlink")
	}
}

func TestReportedPermissionDenialIsNotRepairable(t *testing.T) {
	for _, output := range []string{
		`{"type":"result","is_error":false,"permission_denials":[{"tool_name":"Edit"}]}`,
		"unstructured progress\n" + `{"type":"result","permission_denials":[{"tool_name":"Bash"}]}`,
	} {
		if !reportedExecutionDenial(output) {
			t.Fatal("harness permission denial was treated as ordinary repair feedback")
		}
	}
	for _, output := range []string{`{"type":"result","permission_denials":[]}`, `{"type":"assistant","content":"permission_denials"}`, "ordinary output"} {
		if reportedExecutionDenial(output) {
			t.Fatal("ordinary output was classified as a permission denial")
		}
	}
}

func TestStaleCancelStillStopsDaemonOwnedExecution(t *testing.T) {
	store, lease := recipeStore(t)
	if _, err := store.db.Exec("UPDATE leases SET state='lost' WHERE attempt_id=?", lease.AttemptID); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	daemon := &Daemon{store: store, cancels: map[string]context.CancelFunc{lease.AttemptID: cancel}}
	request := httptest.NewRequest("POST", "/v1/command", strings.NewReader(`{"request_id":"stale-cancel","command":"cancel","arguments":["attempt"]}`))
	response := httptest.NewRecorder()
	daemon.Handler().ServeHTTP(response, request)
	if ctx.Err() != context.Canceled {
		t.Fatal("a stale lease prevented cancellation of the local executor")
	}
	current, _ := store.loadAttempt(lease.AttemptID)
	if current.State != "lost" {
		t.Fatal("cancellation revived a stale lease")
	}
}
