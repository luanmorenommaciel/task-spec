package mesh

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

type Store struct {
	db         *sql.DB
	repository Repository
}

func OpenStore(repository Repository) (*Store, error) {
	if err := repository.Prepare(); err != nil {
		return nil, err
	}
	database, err := sql.Open("sqlite", "file:"+repository.Database+"?_pragma=busy_timeout(5000)&_txlock=immediate")
	if err != nil {
		return nil, err
	}
	for _, statement := range []string{
		"PRAGMA journal_mode=WAL", "PRAGMA synchronous=FULL", "PRAGMA foreign_keys=ON",
		`CREATE TABLE IF NOT EXISTS commands (
            request_id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )`,
		`CREATE TABLE IF NOT EXISTS events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            request_id TEXT NOT NULL,
            run_id TEXT,
            attempt_id TEXT,
            fencing_token INTEGER,
            event_type TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_digest TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
		`CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            graph_revision_digest TEXT NOT NULL,
            target_branch TEXT NOT NULL,
            target_commit TEXT NOT NULL,
            integration_branch TEXT NOT NULL,
            mode TEXT NOT NULL,
            max_parallel INTEGER NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            integration_workspace TEXT
        )`,
		`CREATE TABLE IF NOT EXISTS leases (
            attempt_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL REFERENCES runs(run_id),
            task_id TEXT NOT NULL,
            task_revision_digest TEXT NOT NULL,
            fencing_token INTEGER NOT NULL,
            owner TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            heartbeat_at TEXT NOT NULL,
            state TEXT NOT NULL,
            adapter TEXT,
            branch TEXT,
            workspace TEXT,
            decision_json TEXT,
            acceptance_record TEXT
        )`,
		`CREATE TABLE IF NOT EXISTS lease_fences (
            task_revision_digest TEXT PRIMARY KEY,
            token INTEGER NOT NULL
        )`,
		`CREATE TABLE IF NOT EXISTS credential_leases (
            lease_id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL UNIQUE REFERENCES leases(attempt_id),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            audience TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            state TEXT NOT NULL,
            broker_ref TEXT
        )`,
		`CREATE UNIQUE INDEX IF NOT EXISTS one_authoritative_lease
            ON leases(task_revision_digest)
            WHERE state IN ('leased', 'preparing', 'running', 'verifying', 'awaiting_supervision')`,
	} {
		if _, err := database.Exec(statement); err != nil {
			database.Close()
			return nil, fmt.Errorf("initialize TaskMesh database: %w", err)
		}
	}
	for _, migration := range []struct{ table, column string }{
		{"events", "run_id TEXT"}, {"events", "attempt_id TEXT"}, {"events", "fencing_token INTEGER"},
		{"runs", "integration_workspace TEXT"}, {"runs", "finished_at TEXT"}, {"leases", "adapter TEXT"}, {"leases", "branch TEXT"},
		{"leases", "workspace TEXT"}, {"leases", "decision_json TEXT"}, {"leases", "acceptance_record TEXT"},
	} {
		if _, err := database.Exec("ALTER TABLE " + migration.table + " ADD COLUMN " + migration.column); err != nil && !strings.Contains(err.Error(), "duplicate column") {
			database.Close()
			return nil, fmt.Errorf("migrate TaskMesh %s: %w", migration.table, err)
		}
	}
	if _, err := database.Exec("INSERT OR REPLACE INTO metadata(key, value) VALUES ('repository', ?)", repository.Root); err != nil {
		database.Close()
		return nil, err
	}
	return &Store{db: database, repository: repository}, nil
}

func (store *Store) Close() error { return store.db.Close() }

func canonicalJSON(value any) ([]byte, error) {
	return json.Marshal(value)
}

func digestJSON(value any) (string, error) {
	raw, err := canonicalJSON(value)
	if err != nil {
		return "", err
	}
	digest := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(digest[:]), nil
}

func (store *Store) Process(ctx context.Context, request CommandRequest) (CommandResponse, error) {
	if request.Command == "accept" {
		return store.processSupervisedAccept(ctx, request)
	}
	transaction, err := store.db.BeginTx(ctx, nil)
	if err != nil {
		return CommandResponse{}, err
	}
	defer transaction.Rollback()
	if err := recoverExpiredTx(transaction, "recovery-"+request.RequestID, time.Now().UTC()); err != nil {
		return CommandResponse{}, err
	}
	var retained string
	err = transaction.QueryRowContext(ctx, "SELECT response_json FROM commands WHERE request_id = ?", request.RequestID).Scan(&retained)
	if err == nil {
		var response CommandResponse
		if decodeErr := json.Unmarshal([]byte(retained), &response); decodeErr != nil {
			return CommandResponse{}, decodeErr
		}
		return response, nil
	}
	if err != sql.ErrNoRows {
		return CommandResponse{}, err
	}

	response := store.execute(transaction, request)
	response.RequestID = request.RequestID
	raw, err := canonicalJSON(response)
	if err != nil {
		return CommandResponse{}, err
	}
	if _, err := transaction.ExecContext(ctx,
		"INSERT INTO commands(request_id, command, response_json, created_at) VALUES (?, ?, ?, ?)",
		request.RequestID, request.Command, string(raw), NowUTC()); err != nil {
		return CommandResponse{}, err
	}
	if err := transaction.Commit(); err != nil {
		return CommandResponse{}, err
	}
	return response, nil
}

func (store *Store) execute(transaction *sql.Tx, request CommandRequest) CommandResponse {
	response := CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: true, Code: "MESH_OK", Message: "TaskMesh command completed"}
	switch request.Command {
	case "init":
		payload := map[string]any{"repository": store.repository.Root, "state_dir": store.repository.StateDir}
		if err := appendEvent(transaction, request.RequestID, "MESH_INITIALIZED", payload); err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		response.Code, response.Message, response.Data = "MESH_INIT_OK", "TaskMesh repository state is ready", payload
	case "doctor":
		var journal string
		if err := transaction.QueryRow("PRAGMA journal_mode").Scan(&journal); err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		var eventCount int64
		if err := transaction.QueryRow("SELECT COUNT(*) FROM events").Scan(&eventCount); err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		response.Code, response.Message = "MESH_DOCTOR_READY", "TaskMesh daemon and durable state are ready"
		response.Data = map[string]any{"repository": store.repository.Root, "database": store.repository.Database, "socket": store.repository.Socket, "journal_mode": strings.ToLower(journal), "event_count": eventCount, "daemon_pid": os.Getpid()}
	case "status":
		response = store.statusView(transaction, request)
	case "watch":
		response = store.watchView(transaction, request)
	case "frontier":
		frontier, err := ResolveFrontier(store.repository)
		if err != nil {
			return failure("GRAPH_INVALID", err.Error())
		}
		response.Code, response.Message, response.Data = "MESH_FRONTIER_READY", "authorized ready frontier resolved", map[string]any{"frontier": frontier}
	case "run":
		response = store.startRun(transaction, request)
	case "setup":
		response = store.setupCommand(request)
	case "adapters":
		response = store.adaptersCommand(request)
	case "explain":
		frontier, err := ResolveFrontier(store.repository)
		if err != nil {
			return failure("GRAPH_INVALID", err.Error())
		}
		taskID := option(request.Arguments, "--task", "")
		task, ok := frontier.Eligible(taskID)
		if !ok {
			return failure("TASK_NOT_ELIGIBLE", "explain requires an authorized ready leaf")
		}
		response = explainRoute(task, request.Arguments)
	case "heartbeat":
		response = store.heartbeat(transaction, request)
	case "submit":
		response = store.submit(transaction, request)
	case "cancel":
		response = store.cancel(transaction, request)
	case "resume":
		response = store.resume(transaction, request)
	case "record-acceptance":
		response = store.recordAcceptance(transaction, request)
	case "integrate":
		response = store.integrate(transaction, request)
	case "finish":
		response = store.finish(transaction, request)
	default:
		response = failure("MESH_NOT_IMPLEMENTED", "command is declared but not implemented in this runtime slice")
		response.NextCommand = "taskspec mesh --help"
	}
	return response
}

func failure(code, message string) CommandResponse {
	return CommandResponse{Contract: "TaskMeshCommandResult/v1", OK: false, Code: code, Message: message}
}

func appendEvent(transaction *sql.Tx, requestID, eventType string, payload map[string]any) error {
	return appendRunEvent(transaction, requestID, "", "", 0, eventType, payload)
}

func appendRunEvent(transaction *sql.Tx, requestID, runID, attemptID string, fencingToken int64, eventType string, payload map[string]any) error {
	raw, err := canonicalJSON(payload)
	if err != nil {
		return err
	}
	digest, err := digestJSON(payload)
	if err != nil {
		return err
	}
	_, err = transaction.Exec(
		"INSERT INTO events(event_id, request_id, run_id, attempt_id, fencing_token, event_type, observed_at, payload_json, payload_digest) VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, 0), ?, ?, ?, ?)",
		NewID(), requestID, runID, attemptID, fencingToken, eventType, NowUTC(), string(raw), digest,
	)
	return err
}

type rowQuerier interface {
	Query(query string, args ...any) (*sql.Rows, error)
}

func eventsFrom(query rowQuerier) ([]Event, error) {
	rows, err := query.Query("SELECT sequence, event_id, request_id, COALESCE(run_id, ''), COALESCE(attempt_id, ''), COALESCE(fencing_token, 0), event_type, observed_at, payload_json, payload_digest FROM events ORDER BY sequence")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := []Event{}
	for rows.Next() {
		var event Event
		var payload string
		if err := rows.Scan(&event.Sequence, &event.EventID, &event.RequestID, &event.RunID, &event.AttemptID, &event.FencingToken, &event.Type, &event.ObservedAt, &payload, &event.PayloadDigest); err != nil {
			return nil, err
		}
		event.Contract = "TaskMeshEvent/v1"
		if event.RunID == "" {
			event.Contract = "TaskMeshRepositoryEvent/v1"
		}
		if err := json.Unmarshal([]byte(payload), &event.Payload); err != nil {
			return nil, err
		}
		events = append(events, event)
	}
	return events, rows.Err()
}

func (store *Store) Events() ([]Event, error) { return eventsFrom(store.db) }

func latestSequence(events []Event) int64 {
	if len(events) == 0 {
		return 0
	}
	return events[len(events)-1].Sequence
}
