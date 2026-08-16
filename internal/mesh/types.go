package mesh

import (
	"crypto/rand"
	"encoding/hex"
	"time"
)

const (
	APIContract = "TaskMeshAPI/v1alpha1"
	APIVersion  = "v1alpha1"
)

type APIIdentity struct {
	Contract       string   `json:"contract"`
	ProductVersion string   `json:"product_version"`
	APIVersion     string   `json:"api_version"`
	Capabilities   []string `json:"capabilities"`
	Repository     string   `json:"repository,omitempty"`
	DaemonPID      int      `json:"daemon_pid,omitempty"`
}

type CommandRequest struct {
	RequestID string   `json:"request_id"`
	Command   string   `json:"command"`
	Arguments []string `json:"arguments"`
}

type CommandResponse struct {
	Contract    string         `json:"contract"`
	RequestID   string         `json:"request_id"`
	OK          bool           `json:"ok"`
	Code        string         `json:"code"`
	Message     string         `json:"message"`
	Data        map[string]any `json:"data,omitempty"`
	NextCommand string         `json:"next_command,omitempty"`
}

type Event struct {
	Contract      string         `json:"contract"`
	RunID         string         `json:"run_id,omitempty"`
	Sequence      int64          `json:"sequence"`
	EventID       string         `json:"event_id"`
	RequestID     string         `json:"-"`
	AttemptID     string         `json:"attempt_id,omitempty"`
	FencingToken  int64          `json:"fencing_token,omitempty"`
	Type          string         `json:"type"`
	ObservedAt    string         `json:"observed_at"`
	Payload       map[string]any `json:"payload"`
	PayloadDigest string         `json:"payload_digest"`
}

type Run struct {
	Contract            string `json:"contract"`
	RunID               string `json:"run_id"`
	Repository          string `json:"repository"`
	GraphRevisionDigest string `json:"graph_revision_digest"`
	Target              struct {
		Branch string `json:"branch"`
		Commit string `json:"commit"`
	} `json:"target"`
	IntegrationBranch string `json:"integration_branch"`
	Mode              string `json:"mode"`
	MaxParallel       int    `json:"max_parallel"`
	State             string `json:"state"`
	CreatedAt         string `json:"created_at"`
}

type Lease struct {
	Contract           string `json:"contract"`
	RunID              string `json:"run_id"`
	TaskID             string `json:"task_id"`
	TaskRevisionDigest string `json:"task_revision_digest"`
	AttemptID          string `json:"attempt_id"`
	FencingToken       int64  `json:"fencing_token"`
	Owner              string `json:"owner"`
	IssuedAt           string `json:"issued_at"`
	ExpiresAt          string `json:"expires_at"`
	HeartbeatAt        string `json:"heartbeat_at"`
	State              string `json:"state"`
	Adapter            string `json:"-"`
	Branch             string `json:"-"`
	Workspace          string `json:"-"`
	AcceptanceRecord   string `json:"-"`
}

type DispatchCandidate struct {
	Adapter          string   `json:"adapter"`
	Eligible         bool     `json:"eligible"`
	RejectionReasons []string `json:"rejection_reasons"`
	StaticScore      float64  `json:"static_score"`
}

type DispatchDecision struct {
	Contract              string              `json:"contract"`
	TaskID                string              `json:"task_id"`
	TaskRevisionDigest    string              `json:"task_revision_digest"`
	PolicyDigest          string              `json:"policy_digest"`
	Candidates            []DispatchCandidate `json:"candidates"`
	Selected              *string             `json:"selected"`
	AdvisorResponseDigest *string             `json:"advisor_response_digest,omitempty"`
	Explanation           string              `json:"explanation"`
	DecidedAt             string              `json:"decided_at"`
}

func NewID() string {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		panic(err)
	}
	raw[6] = (raw[6] & 0x0f) | 0x40
	raw[8] = (raw[8] & 0x3f) | 0x80
	encoded := hex.EncodeToString(raw[:])
	return encoded[0:8] + "-" + encoded[8:12] + "-" + encoded[12:16] + "-" + encoded[16:20] + "-" + encoded[20:32]
}

func NowUTC() string {
	return time.Now().UTC().Format(time.RFC3339Nano)
}
