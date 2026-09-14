package mesh

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"time"
)

type executionRecipe struct {
	Contract   string   `json:"contract"`
	Strategy   string   `json:"strategy"`
	Version    string   `json:"strategy_version"`
	MaxRounds  int      `json:"max_rounds"`
	NoProgress int      `json:"no_progress_rounds"`
	EvalIDs    []string `json:"eval_ids"`
	Required   []string `json:"required_capabilities"`
}

type recipeHandoff struct {
	Environment struct {
		Required bool `json:"required"`
	} `json:"environment_contract"`
	Budgets struct {
		Tokens *int `json:"tokens"`
	} `json:"budgets"`
	Spec     string `json:"spec"`
	Revision string `json:"task_revision_digest"`
	Source   struct {
		Base string `json:"base_commit"`
	} `json:"source"`
	Agent struct {
		Recipe          *executionRecipe `json:"execution_recipe"`
		Timeout         int              `json:"timeout_minutes"`
		MCPDependencies []string         `json:"mcp_dependencies"`
	} `json:"agent_contract"`
	Scope struct {
		Touches   []string `json:"touches_paths"`
		Creates   []string `json:"creates_paths"`
		Forbidden []string `json:"do_not_touch"`
	} `json:"write_scope"`
}

func readRecipeHandoff(path string) (recipeHandoff, error) {
	var result recipeHandoff
	raw, err := os.ReadFile(path)
	if err != nil {
		return result, err
	}
	err = json.Unmarshal(raw, &result)
	return result, err
}

// Reserve before invoking a provider: crashes and new attempts never refund rounds.
func (store *Store) reserveRecipeRound(lease Lease, recipe *executionRecipe, minutes int) (int, time.Time, error) {
	tx, err := store.db.Begin()
	if err != nil {
		return 0, time.Time{}, err
	}
	defer tx.Rollback()
	var token int64
	var state, expiry string
	if err = tx.QueryRow("SELECT fencing_token,state,expires_at FROM leases WHERE attempt_id=?", lease.AttemptID).Scan(&token, &state, &expiry); err != nil {
		return 0, time.Time{}, err
	}
	expires, err := time.Parse(time.RFC3339, expiry)
	if err != nil || token != lease.FencingToken || !contains([]string{"preparing", "running"}, state) || time.Now().After(expires) {
		return 0, time.Time{}, fmt.Errorf("ATTEMPT_STALE")
	}
	deadline := time.Now().UTC().Add(time.Duration(minutes) * time.Minute)
	_, err = tx.Exec("INSERT OR IGNORE INTO recipe_budgets (task_id,revision,used,deadline,no_progress,last_fingerprint) VALUES (?,?,0,?,0,'')", lease.TaskID, lease.TaskRevisionDigest, deadline.Format(time.RFC3339Nano))
	if err != nil {
		return 0, time.Time{}, err
	}
	var used, stalled int
	var recorded string
	if err = tx.QueryRow("SELECT used,deadline,no_progress FROM recipe_budgets WHERE task_id=? AND revision=?", lease.TaskID, lease.TaskRevisionDigest).Scan(&used, &recorded, &stalled); err != nil {
		return 0, time.Time{}, err
	}
	deadline, err = time.Parse(time.RFC3339Nano, recorded)
	if err != nil {
		return 0, time.Time{}, err
	}
	if used >= recipe.MaxRounds {
		return 0, deadline, fmt.Errorf("RECIPE_BUDGET_EXHAUSTED")
	}
	if stalled >= recipe.NoProgress {
		return 0, deadline, fmt.Errorf("RECIPE_NO_PROGRESS")
	}
	if !time.Now().Before(deadline) {
		return 0, deadline, fmt.Errorf("RECIPE_TIMEOUT")
	}
	used++
	if _, err = tx.Exec("UPDATE recipe_budgets SET used=? WHERE task_id=? AND revision=?", used, lease.TaskID, lease.TaskRevisionDigest); err != nil {
		return 0, deadline, err
	}
	if err = appendRunEvent(tx, "recipe-"+NewID(), lease.RunID, lease.AttemptID, lease.FencingToken, "RECIPE_ROUND_RESERVED", map[string]any{"round": used, "strategy": recipe.Strategy, "strategy_version": recipe.Version, "deadline": recorded}); err != nil {
		return 0, deadline, err
	}
	return used, deadline, tx.Commit()
}

func (store *Store) recordRecipeFailure(lease Lease, fingerprint string) (int, error) {
	tx, err := store.db.Begin()
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	var token int64
	var state string
	if err = tx.QueryRow("SELECT fencing_token,state FROM leases WHERE attempt_id=?", lease.AttemptID).Scan(&token, &state); err != nil || token != lease.FencingToken || state != "running" {
		return 0, fmt.Errorf("ATTEMPT_STALE")
	}
	var previous string
	var count int
	if err = tx.QueryRow("SELECT last_fingerprint,no_progress FROM recipe_budgets WHERE task_id=? AND revision=?", lease.TaskID, lease.TaskRevisionDigest).Scan(&previous, &count); err != nil {
		return 0, err
	}
	if previous == fingerprint {
		count++
	} else {
		count = 1
	}
	_, err = tx.Exec("UPDATE recipe_budgets SET last_fingerprint=?,no_progress=? WHERE task_id=? AND revision=?", fingerprint, count, lease.TaskID, lease.TaskRevisionDigest)
	if err != nil {
		return 0, err
	}
	return count, tx.Commit()
}

func managedCommand(ctx context.Context, workspace, executable string, args []string, prompt string, env []string) (string, error) {
	cmd := exec.CommandContext(ctx, executable, args...)
	cmd.Dir = workspace
	cmd.Env = env
	if prompt != "" {
		cmd.Stdin = strings.NewReader(prompt)
	}
	out := &boundedBuffer{remaining: 1024 * 1024}
	cmd.Stdout = out
	cmd.Stderr = out
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	cmd.Cancel = func() error {
		if cmd.Process == nil {
			return nil
		}
		return syscall.Kill(-cmd.Process.Pid, syscall.SIGTERM)
	}
	cmd.WaitDelay = 5 * time.Second
	err := cmd.Run()
	return out.String(), err
}

func reportedExecutionDenial(output string) bool {
	for _, line := range strings.Split(output, "\n") {
		var event struct {
			Type    string            `json:"type"`
			Denials []json.RawMessage `json:"permission_denials"`
		}
		if json.Unmarshal([]byte(line), &event) == nil && event.Type == "result" && len(event.Denials) > 0 {
			return true
		}
	}
	return false
}

func scopeContains(path string, roots []string) bool {
	for _, root := range roots {
		root = strings.TrimSuffix(filepath.ToSlash(root), "/")
		if path == root || strings.HasPrefix(path, root+"/") {
			return true
		}
	}
	return false
}

func recipeScopeDigest(ctx context.Context, lease Lease, handoff recipeHandoff) (string, error) {
	paths := map[string]bool{}
	for _, args := range [][]string{{"diff", "--name-only", "-z", handoff.Source.Base}, {"ls-files", "--others", "--exclude-standard", "-z"}} {
		cmd := exec.CommandContext(ctx, "git", args...)
		cmd.Dir = lease.Workspace
		raw, err := cmd.Output()
		if err != nil {
			return "", err
		}
		for _, path := range strings.Split(string(raw), "\x00") {
			if path != "" {
				paths[path] = true
			}
		}
	}
	allowed := append(append([]string{}, handoff.Scope.Touches...), handoff.Scope.Creates...)
	ordered := []string{}
	for path := range paths {
		ordered = append(ordered, path)
	}
	sort.Strings(ordered)
	hash := sha256.New()
	for _, path := range ordered {
		if !scopeContains(path, allowed) || scopeContains(path, handoff.Scope.Forbidden) {
			return "", fmt.Errorf("SCOPE_VIOLATION: %s", path)
		}
		full := filepath.Join(lease.Workspace, path)
		info, err := os.Lstat(full)
		if os.IsNotExist(err) {
			fmt.Fprintf(hash, "%s\x00deleted\x00", path)
			continue
		}
		if err != nil {
			return "", err
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return "", fmt.Errorf("SCOPE_VIOLATION: symlink %s", path)
		}
		if !info.Mode().IsRegular() {
			return "", fmt.Errorf("SCOPE_VIOLATION: non-file %s", path)
		}
		raw, err := os.ReadFile(full)
		if err != nil {
			return "", err
		}
		fmt.Fprintf(hash, "%s\x00%o\x00", path, info.Mode())
		hash.Write(raw)
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func failingRecipeEvals(output string, required []string) ([]string, error) {
	seen := map[string]string{}
	scanner := bufio.NewScanner(strings.NewReader(output))
	scanner.Buffer(make([]byte, 4096), 1024*1024)
	for scanner.Scan() {
		var row struct {
			Eval   string `json:"eval"`
			Status string `json:"status"`
		}
		if json.Unmarshal(scanner.Bytes(), &row) == nil && row.Eval != "" {
			seen[row.Eval] = row.Status
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	failures := []string{}
	for _, id := range append(append([]string{}, required...), "_exit_check") {
		state, ok := seen[id]
		if !ok {
			return nil, fmt.Errorf("EVALUATION_EVIDENCE_MISSING: %s", id)
		}
		if state != "pass" {
			failures = append(failures, id)
		}
	}
	sort.Strings(failures)
	return failures, nil
}

func (store *Store) executeManagedRecipe(parent context.Context, lease Lease, definition AdapterDefinition, probe AdapterProbe, handoffPath, prompt string, handoff recipeHandoff) error {
	return store.executeRecipe(parent, lease, definition, probe, handoffPath, prompt, handoff, nil)
}

type managedSandbox struct {
	Setup    SandboxSetup
	Provider string
	Model    string
}

// The round controller is shared by host and attested execution. Adapters do not
// own retry state, and a replacement attempt never starts a fresh task budget.
func (store *Store) executeRecipe(parent context.Context, lease Lease, definition AdapterDefinition, probe AdapterProbe, handoffPath, prompt string, handoff recipeHandoff, sandbox *managedSandbox) error {
	recipe := handoff.Agent.Recipe
	park := func(err error) error {
		_ = store.transitionAttempt("recipe-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"preparing", "running", "verifying"}, "parked", "ATTEMPT_PARKED", map[string]any{"code": "RECIPE_STOPPED", "message": err.Error()})
		return err
	}
	if handoff.Environment.Required {
		return park(fmt.Errorf("ENVIRONMENT_UNVERIFIED: custom required environment contracts are not supported by this recipe adapter"))
	}
	if handoff.Budgets.Tokens != nil && *handoff.Budgets.Tokens > 0 {
		return park(fmt.Errorf("RECIPE_CAPABILITY_UNAVAILABLE: hard token-budget enforcement"))
	}
	if recipe.Contract != "TaskExecutionRecipe/v1" || recipe.MaxRounds < 1 || recipe.NoProgress < 1 || handoff.Agent.Timeout < 1 {
		return park(fmt.Errorf("RECIPE_INVALID"))
	}
	capabilities := []string{"managed_recipe_v1", "persistent_round_budget", "signed_timeout"}
	if sandbox != nil {
		capabilities = append(capabilities, "attested_execution")
	}
	for _, capability := range recipe.Required {
		if !contains(capabilities, capability) {
			return park(fmt.Errorf("RECIPE_CAPABILITY_UNAVAILABLE: %s", capability))
		}
	}
	cli, err := taskSpecCLI(store.repository)
	if err != nil {
		return park(err)
	}
	baseEnv, secrets := sanitizedEnvironment()
	env := append(baseEnv, "TASKSPEC_WORKSPACE_ROOT="+lease.Workspace, "TASKMESH_HANDOFF="+handoffPath, "TASKMESH_ATTEMPT_ID="+lease.AttemptID)
	relative, relErr := filepath.Rel(lease.Workspace, handoff.Spec)
	if relErr != nil || strings.HasPrefix(relative, "..") {
		return park(fmt.Errorf("HANDOFF_SCOPE_INVALID"))
	}
	origin := filepath.Join(store.repository.Root, relative)
	handoffBytes, err := os.ReadFile(handoffPath)
	if err != nil {
		return park(err)
	}
	handoffDigest := sha256.Sum256(handoffBytes)
	verifyHandoff := func() error {
		raw, err := os.ReadFile(handoffPath)
		if err != nil || sha256.Sum256(raw) != handoffDigest {
			return fmt.Errorf("HANDOFF_CHANGED")
		}
		return nil
	}
	feedback := ""
	for {
		round, deadline, err := store.reserveRecipeRound(lease, recipe, handoff.Agent.Timeout)
		if err != nil {
			return park(err)
		}
		ctx, cancel := context.WithDeadline(parent, deadline)
		authority := filepath.Join(filepath.Dir(filepath.Dir(cli)), "src", "security", "verify_authorization.py")
		if err = verifyHandoff(); err != nil {
			cancel()
			return park(err)
		}
		if out, authErr := managedCommand(ctx, lease.Workspace, "python3", []string{authority, handoff.Spec, lease.TaskRevisionDigest, "--origin", origin}, "", os.Environ()); authErr != nil {
			cancel()
			return park(fmt.Errorf("AUTHORITY_CHANGED: %s", redact(out, secrets)))
		}
		validation, checkErr := managedCommand(ctx, lease.Workspace, "bash", []string{cli, "validate", "--no-state", handoff.Spec}, "", os.Environ())
		if checkErr != nil {
			cancel()
			return park(fmt.Errorf("AUTHORITY_CHANGED: %s", redact(validation, secrets)))
		}
		if err = store.transitionAttempt("recipe-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"preparing", "running"}, "running", "RECIPE_ROUND_STARTED", map[string]any{"round": round}); err != nil {
			cancel()
			return err
		}
		roundPrompt := prompt + "\n\nFollow the resolved execution_recipe. This is one managed round. Do not self-accept or spawn agents.\n" + feedback
		started := NowUTC()
		var output string
		var runErr error
		var sandboxResult SandboxRunResult
		if sandbox != nil {
			sandboxResult, runErr = store.runSandbox(ctx, lease, handoffPath, roundPrompt, sandbox.Provider, sandbox.Model, sandbox.Setup)
			output = sandboxResult.Output
		} else {
			executable, args, commandErr := adapterCommand(definition, lease.Workspace, roundPrompt, time.Until(deadline), lease.Model, lease.Provider)
			if commandErr != nil {
				cancel()
				return park(commandErr)
			}
			args = managedAdapterArguments(definition, handoff, args)
			input := ""
			if definition.PromptMode == "stdin" {
				input = roundPrompt
			}
			output, runErr = managedCommand(ctx, lease.Workspace, executable, args, input, env)
		}
		artifact, artifactDigest, artifactErr := store.writeExecutionArtifact(lease, definition, probe, started, NowUTC(), redact(output, secrets), len(output) >= 1024*1024, runErr)
		if artifactErr != nil {
			cancel()
			return park(artifactErr)
		}
		if err = copyNonClobbering(artifact, strings.TrimSuffix(artifact, ".json")+fmt.Sprintf(".round-%d.json", round)); err != nil {
			cancel()
			return park(err)
		}
		if runErr != nil {
			cancel()
			return park(fmt.Errorf("EXECUTION_FAILED: %w", runErr))
		}
		if reportedExecutionDenial(output) {
			cancel()
			return park(fmt.Errorf("EXECUTOR_PERMISSION_DENIED: the harness reported a blocked tool call; inspect the retained artifact before retrying"))
		}
		if err = verifyHandoff(); err != nil {
			cancel()
			return park(err)
		}
		if out, authErr := managedCommand(ctx, lease.Workspace, "python3", []string{authority, handoff.Spec, lease.TaskRevisionDigest, "--origin", origin}, "", os.Environ()); authErr != nil {
			cancel()
			return park(fmt.Errorf("AUTHORITY_CHANGED: %s", redact(out, secrets)))
		}
		validation, checkErr = managedCommand(ctx, lease.Workspace, "bash", []string{cli, "validate", "--no-state", handoff.Spec}, "", os.Environ())
		if checkErr != nil {
			cancel()
			return park(fmt.Errorf("AUTHORITY_CHANGED: %s", redact(validation, secrets)))
		}
		scopeDigest, err := recipeScopeDigest(ctx, lease, handoff)
		if err != nil {
			cancel()
			return park(err)
		}
		if sandbox != nil {
			// Verify and retain the round's independently signed execution evidence
			// before evaluating or offering any failure feedback to another round.
			if err = store.finalizeSandboxEvidenceIn(ctx, lease, handoffPath, artifact, artifactDigest, &sandboxResult, fmt.Sprintf(".round-%d", round)); err != nil {
				cancel()
				return park(err)
			}
		}
		evaluation, evalErr := managedCommand(ctx, lease.Workspace, "bash", []string{cli, "run", "--ci", handoff.Spec}, "", env)
		if afterDigest, afterErr := recipeScopeDigest(ctx, lease, handoff); afterErr != nil {
			cancel()
			return park(afterErr)
		} else {
			scopeDigest = afterDigest
		}
		if err = verifyHandoff(); err != nil {
			cancel()
			return park(err)
		}
		if out, authErr := managedCommand(ctx, lease.Workspace, "python3", []string{authority, handoff.Spec, lease.TaskRevisionDigest, "--origin", origin}, "", os.Environ()); authErr != nil {
			cancel()
			return park(fmt.Errorf("AUTHORITY_CHANGED: %s", redact(out, secrets)))
		}
		identity := recipeIdentity(output, lease.Model, lease.Provider)
		record, _ := json.MarshalIndent(map[string]any{"contract": "TaskRecipeRound/v1", "attempt_id": lease.AttemptID, "round": round, "model": identity["model"], "provider": identity["provider"], "execution_identity": identity, "harness": definition.Name, "harness_version": probe.AdapterVersion, "strategy": recipe.Strategy, "strategy_version": recipe.Version, "started_at": started, "finished_at": NowUTC(), "evaluation": redact(evaluation, secrets), "scope_digest": scopeDigest, "usage": recipeUsage(output), "evaluation_environment": "sanitized_host", "sandbox_evidence": sandboxResult.SandboxEvidence}, "", "  ")
		if err = os.WriteFile(strings.TrimSuffix(artifact, ".json")+fmt.Sprintf(".round-%d.evals.json", round), append(record, '\n'), 0600); err != nil {
			cancel()
			return park(err)
		}
		failures, evidenceErr := failingRecipeEvals(evaluation, recipe.EvalIDs)
		if evidenceErr != nil {
			cancel()
			return park(evidenceErr)
		}
		if ctx.Err() != nil {
			err = ctx.Err()
			cancel()
			return park(err)
		}
		cancel()
		if len(failures) == 0 && evalErr == nil {
			if err = store.transitionAttempt("recipe-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"running"}, "verifying", "RECIPE_VERIFIED", map[string]any{"round": round, "artifact": artifact, "digest": artifactDigest, "scope_digest": scopeDigest, "evaluation": redact(evaluation, secrets)}); err != nil {
				return err
			}
			if sandbox != nil {
				acceptCtx, acceptCancel := context.WithDeadline(parent, deadline)
				defer acceptCancel()
				if err = store.verifyAcceptCommitAndIntegrateWithin(acceptCtx, lease, handoffPath, probe, artifact, artifactDigest, started, sandboxResult.FinishedAt, "autonomous", "", "", sandboxResult.Receipt, os.Getenv("TASKSPEC_MESH_TRUST_REGISTRY"), sandboxResult.SandboxEvidence); err != nil {
					return park(err)
				}
				return nil
			}
			return store.transitionAttempt("recipe-"+NewID(), lease.AttemptID, lease.FencingToken, []string{"verifying"}, "awaiting_supervision", "SUPERVISION_REQUIRED", map[string]any{"next_command": "taskspec mesh accept " + lease.AttemptID + " --supervised-by <identity> --reason <text>"})
		}
		if len(failures) == 0 {
			return park(fmt.Errorf("EVALUATION_RUNNER_FAILED"))
		}
		if _, err = store.recordRecipeFailure(lease, strings.Join(failures, ",")+":"+scopeDigest); err != nil {
			return park(err)
		}
		feedback = "Previous round failed these evals: " + strings.Join(failures, ",") + "\n" + redact(evaluation, secrets)
		if len(feedback) > 32768 {
			feedback = feedback[:32768]
		}
	}
}

func managedAdapterArguments(definition AdapterDefinition, handoff recipeHandoff, args []string) []string {
	if definition.Name == "claude-native" && len(handoff.Agent.MCPDependencies) == 0 {
		// Global MCP startup is outside a recipe that declares no MCP dependencies.
		// Leave explicitly declared dependencies and custom adapters configurable.
		args = append(args, "--restricted", "--tools", "Read,Edit,Write,Bash", "--strict-mcp-config", "--mcp-config", `{"mcpServers":{}}`)
	}
	return args
}

// A harness default is unknown until reported. Never infer a provider or model
// from a product name; compatible harnesses may route to other providers.
func recipeIdentity(output, routeModel, routeProvider string) map[string]any {
	result := map[string]any{"model": nil, "provider": nil, "source": "unreported_harness_default"}
	models := map[string]bool{}
	for _, line := range strings.Split(output, "\n") {
		var event map[string]any
		if json.Unmarshal([]byte(line), &event) != nil {
			continue
		}
		if model, ok := event["model"].(string); ok && model != "" {
			models[model] = true
		}
		if usage, ok := event["modelUsage"].(map[string]any); ok {
			for model := range usage {
				if model != "" {
					models[model] = true
				}
			}
		}
		if provider, ok := event["provider"].(string); ok && provider != "" {
			result["provider"] = provider
		}
	}
	ordered := []string{}
	for model := range models {
		ordered = append(ordered, model)
	}
	sort.Strings(ordered)
	result["reported_models"] = ordered
	if len(ordered) > 0 {
		result["source"] = "reported_by_harness"
	}
	if len(ordered) == 1 {
		result["model"] = ordered[0]
	}
	if routeModel != "" {
		result["model"] = routeModel
		result["source"] = "explicit_route"
	}
	if routeProvider != "" {
		result["provider"] = routeProvider
	}
	return result
}

// Native harnesses report usage as JSON/JSONL. Preserve available measurements as
// reported values; absence is unknown and is never treated as zero consumption.
func recipeUsage(output string) map[string]any {
	var result map[string]any
	for _, line := range strings.Split(output, "\n") {
		var event map[string]any
		if json.Unmarshal([]byte(line), &event) != nil {
			continue
		}
		values := map[string]any{}
		if usage, ok := event["usage"].(map[string]any); ok {
			for _, key := range []string{"input_tokens", "output_tokens", "cached_input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"} {
				if value, ok := usage[key].(float64); ok && value >= 0 {
					values[key] = value
				}
			}
		}
		if cost, ok := event["total_cost_usd"].(float64); ok && cost >= 0 {
			values["total_cost_usd"] = cost
		}
		if len(values) > 0 {
			values["claim"] = "reported_by_harness"
			result = values
		}
	}
	return result
}
