package mesh

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

type Daemon struct {
	repository     Repository
	store          *Store
	productVersion string
	cancelMu       sync.Mutex
	cancels        map[string]context.CancelFunc
	attempts       sync.WaitGroup
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
	return &Daemon{repository: repository, store: store, productVersion: productVersion, cancels: map[string]context.CancelFunc{}}, nil
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
		if result.OK && (command.Command == "run" || command.Command == "resume") && hasOption(command.Arguments, "--execute") {
			daemon.launchAttempts(result)
		}
		if command.Command == "cancel" && len(command.Arguments) > 0 {
			daemon.cancelAttempt(command.Arguments[0])
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

func (daemon *Daemon) launchAttempts(result CommandResponse) {
	raw, err := json.Marshal(result.Data["attempts"])
	if err != nil {
		return
	}
	var attempts []struct {
		Lease Lease `json:"lease"`
	}
	if err := json.Unmarshal(raw, &attempts); err != nil {
		return
	}
	for _, attempt := range attempts {
		lease := attempt.Lease
		attemptID := attempt.Lease.AttemptID
		ctx, cancel := context.WithCancel(context.Background())
		daemon.cancelMu.Lock()
		daemon.cancels[attemptID] = cancel
		daemon.cancelMu.Unlock()
		daemon.attempts.Add(1)
		go func() {
			defer daemon.attempts.Done()
			defer cancel()
			defer func() {
				daemon.cancelMu.Lock()
				delete(daemon.cancels, attemptID)
				daemon.cancelMu.Unlock()
			}()
			go daemon.renewExecutingLease(ctx, lease, cancel)
			_ = daemon.store.ExecuteAttempt(ctx, attemptID)
		}()
	}
}

// The daemon renews only attempts it is actively executing. A stopped daemon
// cannot keep a lease alive, and workers never receive renewal authority.
func (daemon *Daemon) renewExecutingLease(ctx context.Context, lease Lease, cancel context.CancelFunc) {
	issued, issuedErr := time.Parse(time.RFC3339Nano, lease.IssuedAt)
	expires, expiresErr := time.Parse(time.RFC3339Nano, lease.ExpiresAt)
	if issuedErr != nil || expiresErr != nil || !expires.After(issued) {
		cancel()
		return
	}
	ttl := int(expires.Sub(issued).Seconds())
	if ttl < 1 {
		ttl = 1
	}
	interval := time.Duration(ttl) * time.Second / 3
	if interval > time.Minute {
		interval = time.Minute
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		if ctx.Err() != nil {
			return
		}
		result, err := daemon.store.Process(ctx, CommandRequest{RequestID: "renew-" + NewID(), Command: "heartbeat", Arguments: []string{"--attempt-id", lease.AttemptID, "--fencing-token", fmt.Sprint(lease.FencingToken), "--lease-ttl", fmt.Sprint(ttl)}})
		if err != nil || !result.OK {
			current, loadErr := daemon.store.loadAttempt(lease.AttemptID)
			if loadErr == nil && current.FencingToken == lease.FencingToken && contains([]string{"accepted", "integrated"}, current.State) {
				return
			}
			cancel()
			return
		}
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}
	}
}

func (daemon *Daemon) cancelExecutions() {
	daemon.cancelMu.Lock()
	cancels := make([]context.CancelFunc, 0, len(daemon.cancels))
	for _, cancel := range daemon.cancels {
		cancels = append(cancels, cancel)
	}
	daemon.cancelMu.Unlock()
	for _, cancel := range cancels {
		cancel()
	}
}

func (daemon *Daemon) cancelAttempt(attemptID string) {
	daemon.cancelMu.Lock()
	cancel := daemon.cancels[attemptID]
	daemon.cancelMu.Unlock()
	if cancel != nil {
		cancel()
	}
}

func (daemon *Daemon) Serve(ctx context.Context) error {
	defer daemon.store.Close()
	defer func() {
		daemon.cancelExecutions()
		done := make(chan struct{})
		go func() { daemon.attempts.Wait(); close(done) }()
		select {
		case <-done:
		case <-time.After(6 * time.Second):
		}
	}()
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
		daemon.cancelExecutions()
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
