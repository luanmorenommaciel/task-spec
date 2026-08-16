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
	database, err := sql.Open("sqlite", "file:"+repository.Database+"?_pragma=busy_timeout(5000)")
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
            event_type TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_digest TEXT NOT NULL
        )`,
		`CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
	} {
		if _, err := database.Exec(statement); err != nil {
			database.Close()
			return nil, fmt.Errorf("initialize TaskMesh database: %w", err)
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
	transaction, err := store.db.BeginTx(ctx, nil)
	if err != nil {
		return CommandResponse{}, err
	}
	defer transaction.Rollback()
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
		events, err := eventsFrom(transaction)
		if err != nil {
			return failure("MESH_STATE_ERROR", err.Error())
		}
		response.Code, response.Message = "MESH_STATUS_READY", "TaskMesh durable view rebuilt from events"
		response.Data = map[string]any{"contract": "TaskMeshRepositoryView/v1", "repository": store.repository.Root, "events": events, "latest_sequence": latestSequence(events)}
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
	raw, err := canonicalJSON(payload)
	if err != nil {
		return err
	}
	digest, err := digestJSON(payload)
	if err != nil {
		return err
	}
	_, err = transaction.Exec(
		"INSERT INTO events(event_id, request_id, event_type, observed_at, payload_json, payload_digest) VALUES (?, ?, ?, ?, ?, ?)",
		NewID(), requestID, eventType, NowUTC(), string(raw), digest,
	)
	return err
}

type rowQuerier interface {
	Query(query string, args ...any) (*sql.Rows, error)
}

func eventsFrom(query rowQuerier) ([]Event, error) {
	rows, err := query.Query("SELECT sequence, event_id, request_id, event_type, observed_at, payload_json, payload_digest FROM events ORDER BY sequence")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := []Event{}
	for rows.Next() {
		var event Event
		var payload string
		if err := rows.Scan(&event.Sequence, &event.EventID, &event.RequestID, &event.Type, &event.ObservedAt, &payload, &event.PayloadDigest); err != nil {
			return nil, err
		}
		event.Contract = "TaskMeshEvent/v1"
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
