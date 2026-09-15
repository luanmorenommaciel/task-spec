package mesh

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

const claudeReadDenial = `{"type":"user","message":{"content":[{"type":"tool_result","is_error":true,"content":"file is outside workspace; --restricted confines the file tools to the working directory."}]}}`

func TestDenialArtifactRetainsStopCodeAfterOutputTruncation(t *testing.T) {
	store, lease := recipeStore(t)
	path, _, err := store.writeExecutionArtifact(lease, AdapterDefinition{}, AdapterProbe{}, NowUTC(), NowUTC(), "retained prefix", true, errExecutorPermissionDenied)
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var artifact map[string]any
	if err := json.Unmarshal(raw, &artifact); err != nil {
		t.Fatal(err)
	}
	if artifact["error_code"] != "EXECUTOR_PERMISSION_DENIED" || artifact["terminal_outcome"] != "failed" || artifact["truncated"] != true {
		t.Fatal("truncated output lost its denial stop reason")
	}
}

func TestManagedCommandStopsOnStreamedDenial(t *testing.T) {
	for _, event := range []string{
		claudeReadDenial,
		`{"type":"item.completed","item":{"type":"command_execution","exit_code":1,"aggregated_output":"Operation not permitted"}}`,
	} {
		workspace := t.TempDir()
		marker := filepath.Join(workspace, "unauthorized-fallback")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		// A process ignoring TERM must not get time to execute a fallback action.
		script := `trap '' TERM; printf '%s\n' "$DENIAL_EVENT"; sleep 2; printf fallback > "$MARKER"`
		output, err := managedCommand(ctx, workspace, "sh", []string{"-c", script}, "", append(os.Environ(), "DENIAL_EVENT="+event, "MARKER="+marker), true)
		cancel()
		if !errors.Is(err, errExecutorPermissionDenied) || !strings.Contains(output, event) {
			t.Fatalf("denial was not retained and stopped: %v %q", err, output)
		}
		if _, err := os.Stat(marker); !os.IsNotExist(err) {
			t.Fatal("fallback executed after denial")
		}
	}
}

func TestDenialStreamChunkingAndRetentionLimit(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	writer := &denialOutput{output: &boundedBuffer{remaining: 16}, cancel: cancel}
	// Oversized ordinary output must not hide a later denial or grow pending memory.
	writer.Write([]byte(strings.Repeat("x", 2*1024*1024+1)))
	if len(writer.pending) != 0 {
		t.Fatal("oversized event was retained")
	}
	writer.Write([]byte("\n" + claudeReadDenial[:40]))
	if writer.Denied() {
		t.Fatal("partial event classified")
	}
	writer.Write([]byte(claudeReadDenial[40:] + "\n"))
	if !writer.Denied() || ctx.Err() != context.Canceled {
		t.Fatal("late chunked denial was missed")
	}
	if len(writer.output.String()) != 16 {
		t.Fatal("output retention bound changed")
	}
}

func TestDenialStreamPreservesOrdinaryFailuresAndFinalEvent(t *testing.T) {
	for _, event := range []string{
		`{"type":"user","message":{"content":[{"type":"tool_result","is_error":true,"content":"AssertionError: invalid result"}]}}`,
		`{"type":"user","message":{"content":[{"type":"tool_result","is_error":false,"content":"Documentation: permission denied"}]}}`,
	} {
		writer := &denialOutput{output: &boundedBuffer{remaining: 4096}, cancel: func() { t.Fatal("ordinary output cancelled execution") }}
		writer.Write([]byte(event + "\n"))
		writer.Finish()
		if writer.Denied() {
			t.Fatal("ordinary failure classified as denial")
		}
	}
	writer := &denialOutput{output: &boundedBuffer{remaining: 4096}, cancel: func() {}}
	writer.Write([]byte(claudeReadDenial))
	writer.Finish()
	if !writer.Denied() {
		t.Fatal("final event without newline was missed")
	}
}
