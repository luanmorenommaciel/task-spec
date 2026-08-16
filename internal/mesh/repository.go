package mesh

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

type Repository struct {
	Root       string
	StateDir   string
	Database   string
	RuntimeDir string
	Socket     string
	Log        string
	GitCommon  string
}

func ResolveRepository(input string) (Repository, error) {
	abs, err := filepath.Abs(input)
	if err != nil {
		return Repository{}, err
	}
	real, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return Repository{}, fmt.Errorf("resolve repository: %w", err)
	}
	command := exec.Command("git", "-C", real, "rev-parse", "--show-toplevel")
	output, err := command.Output()
	if err != nil {
		return Repository{}, fmt.Errorf("TaskMesh requires a Git repository: %w", err)
	}
	root := strings.TrimSpace(string(output))
	root, err = filepath.EvalSymlinks(root)
	if err != nil {
		return Repository{}, fmt.Errorf("resolve Git root: %w", err)
	}
	commonCommand := exec.Command("git", "-C", root, "rev-parse", "--git-common-dir")
	commonOutput, err := commonCommand.Output()
	if err != nil {
		return Repository{}, fmt.Errorf("resolve Git common directory: %w", err)
	}
	common := strings.TrimSpace(string(commonOutput))
	if !filepath.IsAbs(common) {
		common = filepath.Join(root, common)
	}
	common, err = filepath.Abs(common)
	if err != nil {
		return Repository{}, err
	}
	stateDir := filepath.Join(root, ".taskspec", "mesh")
	runtimeBase := os.Getenv("XDG_RUNTIME_DIR")
	if runtimeBase == "" {
		runtimeBase = filepath.Join(os.TempDir(), "taskspec-"+strconv.Itoa(os.Getuid()))
	}
	runtimeDir := filepath.Join(runtimeBase, "taskmesh")
	digest := sha256.Sum256([]byte(root))
	name := hex.EncodeToString(digest[:8])
	return Repository{
		Root: root, StateDir: stateDir, Database: filepath.Join(stateDir, "mesh.db"),
		RuntimeDir: runtimeDir, Socket: filepath.Join(runtimeDir, name+".sock"),
		Log: filepath.Join(stateDir, "daemon.log"), GitCommon: common,
	}, nil
}

func (repository Repository) Prepare() error {
	if err := os.MkdirAll(repository.StateDir, 0o700); err != nil {
		return fmt.Errorf("create TaskMesh state: %w", err)
	}
	if err := os.Chmod(repository.StateDir, 0o700); err != nil {
		return fmt.Errorf("protect TaskMesh state: %w", err)
	}
	if err := os.MkdirAll(repository.RuntimeDir, 0o700); err != nil {
		return fmt.Errorf("create TaskMesh runtime directory: %w", err)
	}
	if err := os.Chmod(repository.RuntimeDir, 0o700); err != nil {
		return fmt.Errorf("protect TaskMesh runtime directory: %w", err)
	}
	if err := repository.ensureRuntimeIgnored(); err != nil {
		return err
	}
	return nil
}

func (repository Repository) ensureRuntimeIgnored() error {
	info := filepath.Join(repository.GitCommon, "info")
	if err := os.MkdirAll(info, 0o700); err != nil {
		return err
	}
	exclude := filepath.Join(info, "exclude")
	raw, err := os.ReadFile(exclude)
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	for _, line := range strings.Split(string(raw), "\n") {
		if strings.TrimSpace(line) == ".taskspec/mesh/" {
			return nil
		}
	}
	file, err := os.OpenFile(exclude, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = file.WriteString("\n# TaskMesh disposable runtime projection\n.taskspec/mesh/\n")
	return err
}
