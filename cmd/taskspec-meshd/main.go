package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"

	"github.com/luanmorenomaciel/task-spec/internal/mesh"
)

var productVersion = "3.9.0"

func main() {
	os.Exit(run(os.Args[1:]))
}

func run(arguments []string) int {
	if len(arguments) == 1 && arguments[0] == "--version-json" {
		printJSON(mesh.APIIdentity{Contract: mesh.APIContract, ProductVersion: productVersion, APIVersion: mesh.APIVersion, Capabilities: []string{"durable-events", "idempotent-commands", "sqlite-wal"}})
		return 0
	}
	repositoryPath, jsonOutput, remaining, err := globalArguments(arguments)
	if err != nil {
		return printError("MESH_USAGE", err.Error(), 2, jsonOutput)
	}
	repository, err := mesh.ResolveRepository(repositoryPath)
	if err != nil {
		return printError("MESH_REPOSITORY_NOT_FOUND", err.Error(), 3, jsonOutput)
	}
	if len(remaining) == 0 {
		return printError("MESH_USAGE", "missing TaskMesh command", 2, jsonOutput)
	}
	if remaining[0] == "serve" {
		if len(remaining) != 2 || remaining[1] != "--foreground" {
			return printError("MESH_USAGE", "serve requires --foreground", 2, jsonOutput)
		}
		daemon, err := mesh.NewDaemon(repository, productVersion)
		if err != nil {
			return printError("MESH_STATE_ERROR", err.Error(), 3, jsonOutput)
		}
		if !jsonOutput {
			fmt.Printf("TASKMESH_SERVING repository=%s socket=%s\n", repository.Root, repository.Socket)
		}
		if err := daemon.Serve(context.Background()); err != nil {
			return printError("MESH_DAEMON_FAILED", err.Error(), 3, jsonOutput)
		}
		return 0
	}
	if err := ensureDaemon(repository); err != nil {
		return printError("MESH_DAEMON_FAILED", err.Error(), 3, jsonOutput)
	}
	requestID, commandArguments := extractRequestID(remaining[1:])
	request := mesh.CommandRequest{RequestID: requestID, Command: remaining[0], Arguments: commandArguments}
	response, err := mesh.Call(repository.Socket, request)
	if err != nil {
		return printError("MESH_API_UNAVAILABLE", err.Error(), 3, jsonOutput)
	}
	if jsonOutput {
		printJSON(response)
	} else {
		printHuman(response)
	}
	if !response.OK {
		return 1
	}
	return 0
}

func globalArguments(arguments []string) (string, bool, []string, error) {
	repository, jsonOutput := "", false
	remaining := []string{}
	for index := 0; index < len(arguments); index++ {
		switch arguments[index] {
		case "--repository":
			if index+1 >= len(arguments) {
				return "", jsonOutput, nil, fmt.Errorf("--repository requires a path")
			}
			index++
			repository = arguments[index]
		case "--json":
			jsonOutput = true
		default:
			remaining = append(remaining, arguments[index])
		}
	}
	if repository == "" {
		return "", jsonOutput, nil, fmt.Errorf("--repository is required")
	}
	return repository, jsonOutput, remaining, nil
}

func ensureDaemon(repository mesh.Repository) error {
	if identity, err := mesh.Health(repository.Socket); err == nil {
		if identity.Contract != mesh.APIContract || identity.ProductVersion != productVersion {
			return fmt.Errorf("MESH_VERSION_MISMATCH: daemon reports %s %s", identity.Contract, identity.ProductVersion)
		}
		return nil
	}
	if err := repository.Prepare(); err != nil {
		return err
	}
	executable, err := os.Executable()
	if err != nil {
		return err
	}
	logFile, err := os.OpenFile(repository.Log, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer logFile.Close()
	command := exec.Command(executable, "--repository", repository.Root, "serve", "--foreground")
	command.Stdout, command.Stderr = logFile, logFile
	command.Dir = repository.Root
	command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	if err := command.Start(); err != nil {
		return err
	}
	for attempts := 0; attempts < 100; attempts++ {
		identity, healthErr := mesh.Health(repository.Socket)
		if healthErr == nil {
			if identity.ProductVersion != productVersion {
				return fmt.Errorf("MESH_VERSION_MISMATCH: daemon reports %s", identity.ProductVersion)
			}
			return nil
		}
		time.Sleep(25 * time.Millisecond)
	}
	return fmt.Errorf("daemon did not become ready; inspect %s", filepath.Clean(repository.Log))
}

func extractRequestID(arguments []string) (string, []string) {
	requestID := ""
	remaining := []string{}
	for index := 0; index < len(arguments); index++ {
		if arguments[index] == "--request-id" && index+1 < len(arguments) {
			index++
			requestID = arguments[index]
			continue
		}
		remaining = append(remaining, arguments[index])
	}
	if requestID == "" {
		requestID = mesh.NewID()
	}
	return requestID, remaining
}

func printJSON(value any) { _ = json.NewEncoder(os.Stdout).Encode(value) }

func printError(code, message string, exitCode int, jsonOutput bool) int {
	value := map[string]any{"contract": "TaskMeshError/v1", "api": mesh.APIContract, "code": code, "message": message}
	if jsonOutput {
		printJSON(value)
	} else {
		fmt.Fprintf(os.Stderr, "TASKMESH_ERROR=%s: %s\n", code, message)
	}
	return exitCode
}

func printHuman(response mesh.CommandResponse) {
	fmt.Printf("%s: %s\n", response.Code, response.Message)
	if response.Code == "MESH_DOCTOR_READY" {
		for _, name := range []string{"repository", "database", "socket", "journal_mode", "event_count"} {
			fmt.Printf("  %s: %v\n", name, response.Data[name])
		}
	}
	if response.Code == "MESH_WATCH_READY" {
		raw, _ := json.Marshal(response.Data["events"])
		var events []mesh.Event
		if json.Unmarshal(raw, &events) == nil {
			for _, event := range events {
				identity := event.RunID
				if event.AttemptID != "" {
					identity = event.AttemptID
				}
				fmt.Printf("  %06d  %-28s  %s\n", event.Sequence, event.Type, identity)
			}
		}
	}
	if response.Code == "MESH_FINISHED" {
		if route, ok := response.Data["merge_route"].(map[string]any); ok {
			fmt.Printf("  target: %v @ %v\n", route["target_branch"], route["target_commit"])
			fmt.Printf("  integration: %v\n", route["integration_branch"])
			fmt.Println("  target mutated: false")
		}
	}
	if response.NextCommand != "" {
		fmt.Printf("NEXT=%s\n", response.NextCommand)
	}
}
