package mesh

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type workerImageLock struct {
	Contract  string `json:"contract"`
	Release   string `json:"release"`
	Image     string `json:"image"`
	BaseImage string `json:"base_image"`
	OMP       struct {
		Version     string `json:"version"`
		Source      string `json:"source"`
		AMD64SHA256 string `json:"linux_amd64_sha256"`
		ARM64SHA256 string `json:"linux_arm64_sha256"`
	} `json:"omp"`
}

type SandboxRunResult struct {
	Runtime         string
	ImageDigest     string
	OMPVersion      string
	Output          string
	Truncated       bool
	StartedAt       string
	FinishedAt      string
	Command         []string
	Security        map[string]any
	Credential      CredentialLease
	Environment     string
	Receipt         string
	SandboxEvidence string
}

type codedError struct {
	Code    string
	Message string
}

func (failureErr codedError) Error() string { return failureErr.Message }

func taskSpecHome(repository Repository) (string, error) {
	home := os.Getenv("TASKSPEC_HOME")
	if home == "" {
		home = repository.Root
	}
	abs, err := filepath.Abs(home)
	if err != nil {
		return "", err
	}
	if _, err := os.Stat(filepath.Join(abs, "VERSION")); err != nil {
		return "", fmt.Errorf("Task-Spec installation root is invalid: %w", err)
	}
	return abs, nil
}

func imageLockPath(repository Repository) (string, error) {
	if explicit := os.Getenv("TASKSPEC_MESH_IMAGE_LOCK"); explicit != "" {
		return filepath.Abs(explicit)
	}
	home, err := taskSpecHome(repository)
	if err != nil {
		return "", err
	}
	return filepath.Join(home, "release", "mesh", "image.lock"), nil
}

func loadImageLock(repository Repository) (workerImageLock, string, string, error) {
	path, err := imageLockPath(repository)
	if err != nil {
		return workerImageLock{}, "", "", err
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return workerImageLock{}, "", "", err
	}
	var lock workerImageLock
	if err := json.Unmarshal(raw, &lock); err != nil {
		return workerImageLock{}, "", "", err
	}
	if lock.Contract != "TaskMeshWorkerImageLock/v1" || lock.Image == "" || lock.OMP.Version == "" || len(lock.OMP.AMD64SHA256) != 64 || len(lock.OMP.ARM64SHA256) != 64 {
		return workerImageLock{}, "", "", fmt.Errorf("invalid TaskMesh worker image lock")
	}
	digest := sha256.Sum256(raw)
	return lock, path, "sha256:" + hex.EncodeToString(digest[:]), nil
}

func containerRuntime() (string, string, error) {
	for _, runtime := range []string{"docker", "podman"} {
		path, err := exec.LookPath(runtime)
		if err != nil {
			continue
		}
		command := exec.Command(path, "info")
		if err := command.Run(); err != nil {
			continue
		}
		versionCommand := exec.Command(path, "version", "--format", "{{.Server.Version}}")
		output, err := versionCommand.Output()
		if err != nil {
			versionCommand = exec.Command(path, "version", "--format", "{{.Version}}")
			output, err = versionCommand.Output()
		}
		if err == nil {
			return runtime, strings.TrimSpace(string(output)), nil
		}
	}
	return "", "", fmt.Errorf("Docker or Podman daemon is unavailable")
}

func atomicJSON(path string, value any, mode os.FileMode) error {
	raw, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	temporary, err := os.CreateTemp(filepath.Dir(path), "."+filepath.Base(path)+".*")
	if err != nil {
		return err
	}
	temporaryPath := temporary.Name()
	defer os.Remove(temporaryPath)
	if err := temporary.Chmod(mode); err != nil {
		temporary.Close()
		return err
	}
	if _, err := temporary.Write(raw); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Sync(); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return os.Rename(temporaryPath, path)
}

func runCombined(ctx context.Context, executable string, arguments ...string) ([]byte, error) {
	command := exec.CommandContext(ctx, executable, arguments...)
	return command.CombinedOutput()
}

func (store *Store) setupCommand(request CommandRequest) CommandResponse {
	if len(request.Arguments) != 1 || request.Arguments[0] != "sandbox" {
		return failure("MESH_USAGE", "setup requires sandbox")
	}
	setup, err := store.setupSandbox(context.Background())
	if err != nil {
		return failure("SANDBOX_UNAVAILABLE", err.Error())
	}
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_SANDBOX_READY", Message: "pinned TaskMesh worker sandbox verified", Data: map[string]any{"sandbox": setup}}
}

func (store *Store) setupSandbox(ctx context.Context) (SandboxSetup, error) {
	runtime, runtimeVersion, err := containerRuntime()
	if err != nil {
		return SandboxSetup{}, err
	}
	lock, _, lockDigest, err := loadImageLock(store.repository)
	if err != nil {
		return SandboxSetup{}, err
	}
	home, err := taskSpecHome(store.repository)
	if err != nil {
		return SandboxSetup{}, err
	}
	dockerfile := filepath.Join(home, "release", "mesh", "Dockerfile")
	if _, err := os.Stat(dockerfile); err != nil {
		return SandboxSetup{}, err
	}
	imageRef := lock.Image + ":" + lock.Release
	iidFile, err := os.CreateTemp(store.repository.StateDir, ".mesh-image-id.*")
	if err != nil {
		return SandboxSetup{}, err
	}
	iidPath := iidFile.Name()
	iidFile.Close()
	defer os.Remove(iidPath)
	arguments := []string{
		"build", "--pull=false", "--iidfile", iidPath, "-t", imageRef,
		"--build-arg", "OMP_VERSION=" + lock.OMP.Version,
		"--build-arg", "OMP_LINUX_AMD64_SHA256=" + lock.OMP.AMD64SHA256,
		"--build-arg", "OMP_LINUX_ARM64_SHA256=" + lock.OMP.ARM64SHA256,
		"-f", dockerfile, home,
	}
	buildContext, cancel := context.WithTimeout(ctx, 10*time.Minute)
	defer cancel()
	if output, err := runCombined(buildContext, runtime, arguments...); err != nil {
		return SandboxSetup{}, fmt.Errorf("build pinned worker image: %s: %w", strings.TrimSpace(string(output)), err)
	}
	rawID, err := os.ReadFile(iidPath)
	if err != nil {
		return SandboxSetup{}, err
	}
	imageDigest := strings.TrimSpace(string(rawID))
	if !strings.HasPrefix(imageDigest, "sha256:") || len(imageDigest) != 71 {
		return SandboxSetup{}, fmt.Errorf("worker image did not resolve to a content digest")
	}
	probe, err := runCombined(ctx, runtime, "run", "--rm", "--entrypoint", "/usr/local/bin/omp", imageDigest, "--version")
	if err != nil || strings.TrimSpace(string(probe)) != "omp/"+lock.OMP.Version {
		return SandboxSetup{}, fmt.Errorf("pinned OMP probe failed: %s", strings.TrimSpace(string(probe)))
	}
	setup := SandboxSetup{
		Contract: "TaskMeshSandboxSetup/v1", Runtime: runtime, RuntimeVer: runtimeVersion,
		ImageRef: imageRef, ImageDigest: imageDigest, LockDigest: lockDigest,
		OMPVersion: lock.OMP.Version, VerifiedAt: NowUTC(), Verified: true,
	}
	if err := atomicJSON(filepath.Join(store.repository.StateDir, "sandbox.json"), setup, 0o600); err != nil {
		return SandboxSetup{}, err
	}
	return setup, nil
}

func (store *Store) loadSandboxSetup() (SandboxSetup, error) {
	path := filepath.Join(store.repository.StateDir, "sandbox.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return SandboxSetup{}, err
	}
	var setup SandboxSetup
	if err := json.Unmarshal(raw, &setup); err != nil {
		return SandboxSetup{}, err
	}
	_, _, lockDigest, err := loadImageLock(store.repository)
	if err != nil {
		return SandboxSetup{}, err
	}
	if setup.Contract != "TaskMeshSandboxSetup/v1" || !setup.Verified || setup.LockDigest != lockDigest || !strings.HasPrefix(setup.ImageDigest, "sha256:") {
		return SandboxSetup{}, fmt.Errorf("sandbox setup is stale or does not match release/mesh/image.lock")
	}
	runtime, _, err := containerRuntime()
	if err != nil || runtime != setup.Runtime {
		return SandboxSetup{}, fmt.Errorf("verified %s runtime is unavailable", setup.Runtime)
	}
	output, err := runCombined(context.Background(), runtime, "image", "inspect", "--format", "{{.Id}}", setup.ImageDigest)
	if err != nil || strings.TrimSpace(string(output)) != setup.ImageDigest {
		return SandboxSetup{}, fmt.Errorf("pinned worker image is unavailable or changed")
	}
	return setup, nil
}

func (store *Store) autonomousPreflight(arguments []string) (string, error) {
	if option(arguments, "--adapter", "") != "" && option(arguments, "--adapter", "") != "omp-rpc" {
		return "NO_ELIGIBLE_EXECUTOR", fmt.Errorf("autonomous mode supports only the omp-rpc adapter")
	}
	if !validRouteToken(option(arguments, "--provider", "")) || !validRouteToken(option(arguments, "--model", "")) {
		return "CREDENTIAL_BOUNDARY_UNVERIFIED", fmt.Errorf("autonomous mode requires explicit bounded --provider and --model values")
	}
	if _, err := store.loadSandboxSetup(); err != nil {
		return "SANDBOX_UNAVAILABLE", err
	}
	if _, _, err := gatewayConfiguration(); err != nil {
		return "CREDENTIAL_BOUNDARY_UNVERIFIED", err
	}
	if _, _, _, err := privateKeyOutsideRepository(store.repository); err != nil {
		return "CREDENTIAL_BOUNDARY_UNVERIFIED", err
	}
	return "", nil
}

func normalizeGatewayForContainer(runtimeName, raw string) (string, error) {
	parsed, err := url.Parse(raw)
	if err != nil {
		return "", err
	}
	host, port, err := net.SplitHostPort(parsed.Host)
	if err != nil {
		return raw, nil
	}
	if host == "127.0.0.1" || host == "localhost" || host == "::1" {
		if runtimeName == "podman" {
			host = "host.containers.internal"
		} else {
			host = "host.docker.internal"
		}
		parsed.Host = net.JoinHostPort(host, port)
	}
	return parsed.String(), nil
}

type containerInspect struct {
	Image  string `json:"Image"`
	Config struct {
		User string   `json:"User"`
		Env  []string `json:"Env"`
	} `json:"Config"`
	HostConfig struct {
		NetworkMode    string            `json:"NetworkMode"`
		ReadonlyRootfs bool              `json:"ReadonlyRootfs"`
		CapDrop        []string          `json:"CapDrop"`
		SecurityOpt    []string          `json:"SecurityOpt"`
		PidsLimit      int64             `json:"PidsLimit"`
		NanoCPUs       int64             `json:"NanoCpus"`
		Memory         int64             `json:"Memory"`
		Tmpfs          map[string]string `json:"Tmpfs"`
	} `json:"HostConfig"`
	Mounts []struct {
		Type        string `json:"Type"`
		Source      string `json:"Source"`
		Destination string `json:"Destination"`
		RW          bool   `json:"RW"`
	} `json:"Mounts"`
}

func inspectSecurity(ctx context.Context, runtimeName, container, network, workspace, imageDigest string) (map[string]any, error) {
	raw, err := runCombined(ctx, runtimeName, "inspect", container)
	if err != nil {
		return nil, err
	}
	var values []containerInspect
	if err := json.Unmarshal(raw, &values); err != nil || len(values) != 1 {
		return nil, fmt.Errorf("decode worker container inspection")
	}
	value := values[0]
	networkRaw, err := runCombined(ctx, runtimeName, "network", "inspect", network)
	if err != nil {
		return nil, err
	}
	var networks []struct {
		Internal bool `json:"Internal"`
	}
	if err := json.Unmarshal(networkRaw, &networks); err != nil || len(networks) != 1 {
		return nil, fmt.Errorf("decode worker network inspection")
	}
	failures := []string{}
	require := func(condition bool, message string) {
		if !condition {
			failures = append(failures, message)
		}
	}
	require(networks[0].Internal, "attempt network is not internal")
	require(value.HostConfig.ReadonlyRootfs, "root filesystem is not read-only")
	require(contains(value.HostConfig.CapDrop, "ALL"), "capabilities are not all dropped")
	noNew := false
	for _, option := range value.HostConfig.SecurityOpt {
		if strings.HasPrefix(option, "no-new-privileges") {
			noNew = true
		}
	}
	require(noNew, "no-new-privileges is absent")
	require(value.HostConfig.PidsLimit == 128, "PID limit differs")
	require(value.HostConfig.NanoCPUs == 1_000_000_000, "CPU limit differs")
	require(value.HostConfig.Memory == 512*1024*1024, "memory limit differs")
	require(value.HostConfig.Tmpfs["/tmp"] != "", "bounded tmpfs is absent")
	require(value.Config.User == "65532:65532", "worker user is not the unprivileged TaskMesh UID")
	require(value.Image == imageDigest, "worker image differs from the verified image digest")
	writable := []string{}
	dockerSocket := false
	for _, mount := range value.Mounts {
		if mount.Destination == "/var/run/docker.sock" {
			dockerSocket = true
		}
		if mount.RW {
			writable = append(writable, mount.Destination)
		}
	}
	require(!dockerSocket, "Docker socket is mounted")
	require(len(writable) == 1 && writable[0] == "/workspace", "worker has a writable mount beyond /workspace")
	workspaceReal, _ := filepath.EvalSymlinks(workspace)
	foundWorkspace := false
	for _, mount := range value.Mounts {
		if mount.Destination == "/workspace" {
			sourceReal, _ := filepath.EvalSymlinks(mount.Source)
			foundWorkspace = sourceReal == workspaceReal && mount.RW
		}
	}
	require(foundWorkspace, "attempt workspace mount changed")
	credentialEnvironment := 0
	for _, raw := range value.Config.Env {
		name := strings.ToUpper(strings.SplitN(raw, "=", 2)[0])
		if strings.Contains(name, "API_KEY") || strings.Contains(name, "PRIVATE_KEY") || strings.Contains(name, "SIGNING_KEY") || strings.HasSuffix(name, "_TOKEN") {
			credentialEnvironment++
		}
	}
	require(credentialEnvironment == 0, "credential-bearing environment entered the worker")
	security := map[string]any{
		"network": "attempt_proxy_only", "network_internal": networks[0].Internal,
		"read_only_root": value.HostConfig.ReadonlyRootfs, "capabilities_dropped": contains(value.HostConfig.CapDrop, "ALL"),
		"no_new_privileges": noNew, "writable_mounts": writable, "docker_socket_mounted": dockerSocket,
		"credential_environment_count": credentialEnvironment, "worker_user": value.Config.User,
		"limits":   map[string]any{"cpus": 1, "memory_mb": 512, "pids": 128, "timeout_sec": int(executionTimeout().Seconds()), "tmpfs_mb": 64},
		"failures": failures,
	}
	if len(failures) > 0 {
		return security, errors.New(strings.Join(failures, "; "))
	}
	return security, nil
}

func (store *Store) runSandbox(ctx context.Context, lease Lease, handoff, prompt, provider, model string, setup SandboxSetup) (SandboxRunResult, error) {
	gatewayURL, gatewayToken, err := gatewayConfiguration()
	if err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: err.Error()}
	}
	containerGateway, err := normalizeGatewayForContainer(setup.Runtime, gatewayURL)
	if err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: err.Error()}
	}
	credential, capability, err := store.issueCredential(lease, provider, model, gatewayURL)
	if err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: err.Error()}
	}
	capabilityPath, err := writeSecretFile(store.repository, lease.AttemptID+".capability", capability)
	if err != nil {
		return SandboxRunResult{}, err
	}
	upstreamPath, err := writeSecretFile(store.repository, lease.AttemptID+".upstream", gatewayToken)
	if err != nil {
		os.Remove(capabilityPath)
		return SandboxRunResult{}, err
	}
	defer os.Remove(capabilityPath)
	defer os.Remove(upstreamPath)
	short := strings.ReplaceAll(strings.Split(lease.AttemptID, "-")[0], "_", "-")
	networkName, proxyName, workerName := "taskmesh-"+short, "taskmesh-proxy-"+short, "taskmesh-worker-"+short
	cleanup := func() {
		_, _ = runCombined(context.Background(), setup.Runtime, "rm", "-f", workerName)
		_, _ = runCombined(context.Background(), setup.Runtime, "rm", "-f", proxyName)
		_, _ = runCombined(context.Background(), setup.Runtime, "network", "rm", networkName)
	}
	cleanup()
	defer cleanup()
	if output, err := runCombined(ctx, setup.Runtime, "network", "create", "--internal", networkName); err != nil {
		return SandboxRunResult{}, codedError{Code: "SANDBOX_UNAVAILABLE", Message: strings.TrimSpace(string(output))}
	}
	proxyArguments := []string{
		"create", "--name", proxyName, "--network", networkName, "--network-alias", "credential-proxy",
		"--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--pids-limit", "64",
		"--cpus", "0.5", "--memory", "128m", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
		"--mount", "type=bind,src=" + capabilityPath + ",dst=/run/taskmesh/capability,readonly",
		"--mount", "type=bind,src=" + upstreamPath + ",dst=/run/taskmesh/upstream,readonly",
		"--env", "TASKMESH_CAPABILITY_FILE=/run/taskmesh/capability", "--env", "TASKMESH_UPSTREAM_TOKEN_FILE=/run/taskmesh/upstream",
		"--env", "TASKMESH_UPSTREAM_URL=" + containerGateway, "--env", "TASKMESH_ALLOWED_MODEL=" + model,
		"--env", "TASKMESH_EXPIRES_AT=" + credential.ExpiresAt, setup.ImageDigest, "proxy",
	}
	if setup.Runtime == "docker" {
		proxyArguments = append(proxyArguments[:len(proxyArguments)-2], append([]string{"--add-host", "host.docker.internal:host-gateway"}, proxyArguments[len(proxyArguments)-2:]...)...)
	}
	if output, err := runCombined(ctx, setup.Runtime, proxyArguments...); err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: strings.TrimSpace(string(output))}
	}
	externalNetwork := "bridge"
	if setup.Runtime == "podman" {
		externalNetwork = "podman"
	}
	if output, err := runCombined(ctx, setup.Runtime, "network", "connect", externalNetwork, proxyName); err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: strings.TrimSpace(string(output))}
	}
	if output, err := runCombined(ctx, setup.Runtime, "start", proxyName); err != nil {
		return SandboxRunResult{}, codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: strings.TrimSpace(string(output))}
	}
	relativeHandoff, err := filepath.Rel(lease.Workspace, handoff)
	if err != nil || strings.HasPrefix(relativeHandoff, "..") {
		return SandboxRunResult{}, codedError{Code: "HANDOFF_STALE", Message: "handoff is outside the attempt workspace"}
	}
	promptDir := filepath.Join(lease.Workspace, ".taskspec", "mesh", "prompts")
	if err := os.MkdirAll(promptDir, 0o700); err != nil {
		return SandboxRunResult{}, err
	}
	promptPath := filepath.Join(promptDir, lease.AttemptID+".txt")
	if err := os.WriteFile(promptPath, []byte(prompt), 0o600); err != nil {
		return SandboxRunResult{}, err
	}
	relativePrompt, _ := filepath.Rel(lease.Workspace, promptPath)
	workerArguments := []string{
		"create", "--name", workerName, "--network", networkName, "--read-only", "--cap-drop", "ALL",
		"--security-opt", "no-new-privileges:true", "--pids-limit", "128", "--cpus", "1", "--memory", "512m",
		"--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777",
		"--mount", "type=bind,src=" + lease.Workspace + ",dst=/workspace",
		"--mount", "type=bind,src=" + capabilityPath + ",dst=/run/taskmesh/capability,readonly",
		"--workdir", "/workspace", "--env", "HOME=/tmp/home", "--env", "TASKMESH_CAPABILITY_FILE=/run/taskmesh/capability",
		"--env", "TASKMESH_HANDOFF_PATH=/workspace/" + filepath.ToSlash(relativeHandoff),
		"--env", "TASKMESH_PROMPT_PATH=/workspace/" + filepath.ToSlash(relativePrompt),
		"--env", "TASKMESH_PROVIDER=" + provider, "--env", "TASKMESH_MODEL=" + model,
		"--env", "TASKMESH_OMP_VERSION=" + setup.OMPVersion, "--env", "TASKMESH_TIMEOUT_SEC=" + strconv.Itoa(int(executionTimeout().Seconds())),
	}
	if os.Getenv("TASKSPEC_MESH_FAKE_WORKER") == "1" {
		workerArguments = append(workerArguments, "--env", "TASKMESH_FAKE_WORKER=1")
	}
	if delay := os.Getenv("TASKSPEC_MESH_FAKE_WORKER_DELAY_SEC"); delay != "" {
		workerArguments = append(workerArguments, "--env", "TASKMESH_FAKE_WORKER_DELAY_SEC="+delay)
	}
	workerArguments = append(workerArguments, setup.ImageDigest, "worker")
	if output, err := runCombined(ctx, setup.Runtime, workerArguments...); err != nil {
		return SandboxRunResult{}, codedError{Code: "SANDBOX_UNAVAILABLE", Message: strings.TrimSpace(string(output))}
	}
	security, err := inspectSecurity(ctx, setup.Runtime, workerName, networkName, lease.Workspace, setup.ImageDigest)
	if err != nil {
		return SandboxRunResult{}, codedError{Code: "SANDBOX_UNAVAILABLE", Message: err.Error()}
	}
	store.setCredentialState(lease.AttemptID, "active")
	started := NowUTC()
	command := exec.CommandContext(ctx, setup.Runtime, "start", "-a", workerName)
	output := &boundedBuffer{remaining: 1024 * 1024}
	command.Stdout, command.Stderr = output, output
	runErr := command.Run()
	finished := NowUTC()
	if runErr != nil {
		state := "revoked"
		if time.Now().UTC().After(mustTime(credential.ExpiresAt)) {
			state = "expired"
		}
		store.setCredentialState(lease.AttemptID, state)
		code := "EXECUTION_FAILED"
		if state == "expired" {
			code = "CREDENTIAL_BOUNDARY_UNVERIFIED"
		}
		return SandboxRunResult{Runtime: setup.Runtime, ImageDigest: setup.ImageDigest, OMPVersion: setup.OMPVersion, Output: output.String(), Truncated: output.truncated, StartedAt: started, FinishedAt: finished, Command: []string{"taskmesh-worker", lease.AttemptID, "omp-rpc"}, Security: security, Credential: credential}, codedError{Code: code, Message: strings.TrimSpace(output.String())}
	}
	store.setCredentialState(lease.AttemptID, "revoked")
	return SandboxRunResult{Runtime: setup.Runtime, ImageDigest: setup.ImageDigest, OMPVersion: setup.OMPVersion, Output: output.String(), Truncated: output.truncated, StartedAt: started, FinishedAt: finished, Command: []string{"taskmesh-worker", lease.AttemptID, "omp-rpc"}, Security: security, Credential: credential}, nil
}

func mustTime(raw string) time.Time {
	value, _ := time.Parse(time.RFC3339Nano, raw)
	return value
}

func (store *Store) finalizeSandboxEvidence(lease Lease, handoff, artifact, artifactDigest string, result *SandboxRunResult) error {
	privateKey, publicKey, trustRegistry, err := privateKeyOutsideRepository(store.repository)
	if err != nil {
		return codedError{Code: "CREDENTIAL_BOUNDARY_UNVERIFIED", Message: err.Error()}
	}
	handoffRaw, err := os.ReadFile(handoff)
	if err != nil {
		return err
	}
	var handoffValue map[string]any
	if err := json.Unmarshal(handoffRaw, &handoffValue); err != nil {
		return err
	}
	authorization, ok := handoffValue["authorization"].(map[string]any)
	if !ok {
		return fmt.Errorf("handoff authorization is missing")
	}
	source, ok := handoffValue["source"].(map[string]any)
	if !ok {
		return fmt.Errorf("handoff source is missing")
	}
	artifacts := filepath.Join(store.repository.StateDir, "artifacts")
	attestationPath := filepath.Join(artifacts, lease.AttemptID+"-environment-attestation.json")
	attestation := map[string]any{
		"contract": "EnvironmentAttestation/v1", "observed_at": result.FinishedAt, "result": "pass", "verified": true,
		"runtime":      map[string]any{"name": result.Runtime, "version": runtimeVersion(result.Runtime), "kernel": runtimeKernel(result.Runtime)},
		"image_digest": result.ImageDigest,
		"isolation": map[string]any{"network": "attempt_proxy_only", "read_only_root": true, "capabilities_dropped": true, "no_new_privileges": true,
			"writable_mounts": []string{lease.Workspace, "/tmp"}, "limits": result.Security["limits"]},
		"command": result.Command, "artifact_digest": artifactDigest,
	}
	commandDigest, _ := digestJSON(result.Command)
	attestation["command_digest"] = commandDigest
	if err := atomicJSON(attestationPath, attestation, 0o600); err != nil {
		return err
	}
	environmentContractPath := filepath.Join(artifacts, lease.AttemptID+"-environment-contract.json")
	environmentContract := map[string]any{"contract": "EnvironmentContract/v1", "runtime": map[string]any{"name": result.Runtime, "image_digest": result.ImageDigest}, "network": map[string]any{"mode": "attempt_proxy_only"}, "filesystem": map[string]any{"workspace": lease.Workspace, "writes": []string{"authorized-task-scope"}}}
	if err := atomicJSON(environmentContractPath, environmentContract, 0o600); err != nil {
		return err
	}
	credentialPath := filepath.Join(artifacts, lease.AttemptID+"-credential-lease.json")
	credentialRecord := result.Credential
	credentialRecord.State = "active"
	if err := atomicJSON(credentialPath, credentialRecord, 0o600); err != nil {
		return err
	}
	cli, err := taskSpecCLI(store.repository)
	if err != nil {
		return err
	}
	unsigned := filepath.Join(artifacts, lease.AttemptID+"-environment-receipt-unsigned.json")
	receipt := filepath.Join(artifacts, lease.AttemptID+"-environment-receipt.json")
	baseEnvironment, _ := sanitizedEnvironment()
	create := exec.Command("bash", cli, "receipt", "environment", "--task-id", lease.TaskID, "--contract", environmentContractPath, "--provider", "taskmesh-"+result.Runtime+"-attestor", "--attestation", attestationPath, "--handoff", handoff, "--out", unsigned)
	create.Dir, create.Env = lease.Workspace, baseEnvironment
	if output, err := create.CombinedOutput(); err != nil {
		return fmt.Errorf("create environment receipt: %s: %w", strings.TrimSpace(string(output)), err)
	}
	sign := exec.Command("bash", cli, "receipt", "sign", unsigned, "--private-key", privateKey, "--public-key", publicKey, "--out", receipt)
	sign.Dir, sign.Env = lease.Workspace, baseEnvironment
	if output, err := sign.CombinedOutput(); err != nil {
		return fmt.Errorf("sign environment receipt: %s: %w", strings.TrimSpace(string(output)), err)
	}
	home, err := taskSpecHome(store.repository)
	if err != nil {
		return err
	}
	verify := exec.Command("python3", filepath.Join(home, "src", "evidence", "environment_attestation.py"), "verify", attestationPath, "--receipt", receipt, "--trust-registry", trustRegistry)
	verify.Dir, verify.Env = lease.Workspace, baseEnvironment
	if output, err := verify.CombinedOutput(); err != nil {
		return fmt.Errorf("verify environment evidence: %s: %w", strings.TrimSpace(string(output)), err)
	}
	attestationRaw, _ := os.ReadFile(attestationPath)
	attestationHash := sha256.Sum256(attestationRaw)
	evidencePath := filepath.Join(artifacts, lease.AttemptID+"-sandbox-evidence.json")
	evidence := map[string]any{
		"contract": "SandboxEvidence/v1", "subject": map[string]any{
			"task_id": lease.TaskID, "task_revision_digest": lease.TaskRevisionDigest,
			"authorization_ref": authorization["ref"], "attempt_id": lease.AttemptID, "base_commit": source["base_commit"],
		}, "runtime": result.Runtime, "image_digest": result.ImageDigest,
		"attestation": map[string]any{"path": attestationPath, "digest": "sha256:" + hex.EncodeToString(attestationHash[:]), "signature_ref": receipt},
		"verified":    true, "observed_at": result.FinishedAt,
	}
	if err := atomicJSON(evidencePath, evidence, 0o600); err != nil {
		return err
	}
	result.Environment, result.Receipt, result.SandboxEvidence = attestationPath, receipt, evidencePath
	_ = artifact
	return nil
}

func runtimeVersion(runtimeName string) string {
	output, _ := runCombined(context.Background(), runtimeName, "version", "--format", "{{.Server.Version}}")
	return strings.TrimSpace(string(output))
}

func runtimeKernel(runtimeName string) string {
	output, _ := runCombined(context.Background(), runtimeName, "info", "--format", "{{.KernelVersion}}")
	value := strings.TrimSpace(string(output))
	if value == "" {
		value = "unknown"
	}
	return value
}
