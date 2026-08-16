package mesh

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type Daemon struct {
	repository     Repository
	store          *Store
	productVersion string
}

func NewDaemon(repository Repository, productVersion string) (*Daemon, error) {
	store, err := OpenStore(repository)
	if err != nil {
		return nil, err
	}
	if err := store.RecoverExpired(context.Background()); err != nil {
		store.Close()
		return nil, err
	}
	return &Daemon{repository: repository, store: store, productVersion: productVersion}, nil
}

func (daemon *Daemon) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/health", func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodGet {
			http.Error(writer, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		writeJSON(writer, http.StatusOK, APIIdentity{
			Contract: APIContract, ProductVersion: daemon.productVersion, APIVersion: APIVersion,
			Capabilities: []string{"durable-events", "idempotent-commands", "sqlite-wal"},
			Repository:   daemon.repository.Root, DaemonPID: os.Getpid(),
		})
	})
	mux.HandleFunc("/v1/command", func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost {
			http.Error(writer, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var command CommandRequest
		decoder := json.NewDecoder(http.MaxBytesReader(writer, request.Body, 1024*1024))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&command); err != nil || command.RequestID == "" || command.Command == "" {
			writeJSON(writer, http.StatusBadRequest, failure("MESH_API_INVALID", "invalid command request"))
			return
		}
		result, err := daemon.store.Process(request.Context(), command)
		if err != nil {
			writeJSON(writer, http.StatusInternalServerError, failure("MESH_STATE_ERROR", err.Error()))
			return
		}
		status := http.StatusOK
		if !result.OK {
			status = http.StatusConflict
		}
		writeJSON(writer, status, result)
	})
	mux.HandleFunc("/v1/events", func(writer http.ResponseWriter, request *http.Request) {
		events, err := daemon.store.Events()
		if err != nil {
			writeJSON(writer, http.StatusInternalServerError, failure("MESH_STATE_ERROR", err.Error()))
			return
		}
		writeJSON(writer, http.StatusOK, map[string]any{"contract": "TaskMeshEventLog/v1", "events": events})
	})
	return mux
}

func (daemon *Daemon) Serve(ctx context.Context) error {
	defer daemon.store.Close()
	if err := daemon.repository.Prepare(); err != nil {
		return err
	}
	if existing, err := net.DialTimeout("unix", daemon.repository.Socket, 250*time.Millisecond); err == nil {
		existing.Close()
		return errors.New("TaskMesh daemon is already serving this repository")
	}
	_ = os.Remove(daemon.repository.Socket)
	listener, err := net.Listen("unix", daemon.repository.Socket)
	if err != nil {
		return err
	}
	defer func() {
		listener.Close()
		os.Remove(daemon.repository.Socket)
	}()
	if err := os.Chmod(daemon.repository.Socket, 0o600); err != nil {
		return err
	}
	server := &http.Server{Handler: daemon.Handler(), ReadHeaderTimeout: 5 * time.Second}
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)
	defer signal.Stop(shutdown)
	go func() {
		select {
		case <-ctx.Done():
		case <-shutdown:
		}
		deadline, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		server.Shutdown(deadline)
	}()
	err = server.Serve(listener)
	if errors.Is(err, http.ErrServerClosed) {
		return nil
	}
	return err
}

func writeJSON(writer http.ResponseWriter, status int, value any) {
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(status)
	_ = json.NewEncoder(writer).Encode(value)
}
