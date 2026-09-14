package mesh

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func runGit(repository Repository, workingDirectory string, arguments ...string) error {
	command := exec.Command("git", arguments...)
	command.Dir = workingDirectory
	if output, err := command.CombinedOutput(); err != nil {
		return fmt.Errorf("git %s: %s: %w", strings.Join(arguments, " "), strings.TrimSpace(string(output)), err)
	}
	return nil
}

func managedWorkspaceRoot(repository Repository, runID string) (string, error) {
	root := filepath.Join(repository.StateDir, "workspaces", runID)
	for path := root; path != repository.Root; path = filepath.Dir(path) {
		if path == filepath.Dir(path) {
			return "", fmt.Errorf("managed workspace escapes repository")
		}
		info, err := os.Lstat(path)
		if err == nil && info.Mode()&os.ModeSymlink != 0 {
			return "", fmt.Errorf("managed workspace cannot traverse a symlink: %s", path)
		}
		if err != nil && !os.IsNotExist(err) {
			return "", err
		}
	}
	return root, nil
}

func prepareIntegration(repository Repository, runID, branch, targetCommit string) (string, error) {
	root, err := managedWorkspaceRoot(repository, runID)
	if err != nil {
		return "", err
	}
	workspace := filepath.Join(root, "integration")
	if err := os.MkdirAll(root, 0o700); err != nil {
		return "", err
	}
	if err := runGit(repository, repository.Root, "branch", branch, targetCommit); err != nil {
		return "", err
	}
	if err := runGit(repository, repository.Root, "worktree", "add", "--quiet", workspace, branch); err != nil {
		_ = runGit(repository, repository.Root, "branch", "-D", branch)
		return "", err
	}
	return workspace, nil
}

func prepareAttempt(repository Repository, runID string, lease Lease, integrationBranch string) (string, string, error) {
	shortAttempt := strings.Split(lease.AttemptID, "-")[0]
	taskSlug := strings.ToLower(strings.TrimPrefix(lease.TaskID, "T-"))
	branch := "taskmesh/" + taskSlug + "/" + shortAttempt
	root, err := managedWorkspaceRoot(repository, runID)
	if err != nil {
		return "", "", err
	}
	workspace := filepath.Join(root, "attempts", lease.AttemptID)
	if err := os.MkdirAll(filepath.Dir(workspace), 0o700); err != nil {
		return "", "", err
	}
	if err := runGit(repository, repository.Root, "worktree", "add", "--quiet", "-b", branch, workspace, integrationBranch); err != nil {
		return "", "", err
	}
	return branch, workspace, nil
}
