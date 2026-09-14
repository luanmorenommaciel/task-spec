package main

import (
	"bytes"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestStatusBeforeInitializationDoesNotWriteGitOrRuntime(t *testing.T) {
	root := t.TempDir()
	if output, err := exec.Command("git", "init", "-q", root).CombinedOutput(); err != nil {
		t.Fatalf("git init: %v %s", err, output)
	}
	exclude := filepath.Join(root, ".git", "info", "exclude")
	before, err := os.ReadFile(exclude)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(exclude, 0o400); err != nil {
		t.Fatal(err)
	}
	for _, item := range []struct {
		arguments []string
		exitCode  int
	}{{[]string{"status"}, 0}, {[]string{"status", "missing-attempt"}, 1}} {
		arguments := append([]string{"--repository", root, "--json"}, item.arguments...)
		if code := run(arguments); code != item.exitCode {
			t.Fatalf("%v exit=%d, want %d", arguments, code, item.exitCode)
		}
	}
	after, err := os.ReadFile(exclude)
	if err != nil || !bytes.Equal(before, after) {
		t.Fatalf("read-only status changed Git excludes: %v", err)
	}
	if _, err := os.Lstat(filepath.Join(root, ".taskspec")); !os.IsNotExist(err) {
		t.Fatalf("read-only status created runtime state: %v", err)
	}
}
