package mesh

import (
	"bytes"
	"context"
	"errors"
	"sync"
)

var errExecutorPermissionDenied = errors.New("EXECUTOR_PERMISSION_DENIED: the harness reported a blocked tool call; inspect the retained artifact before retrying")

// denialOutput observes complete native JSONL events while the existing command
// runner executes. Output retention and event parsing have separate bounds, so
// an early verbose response cannot hide a later small denial event.
type denialOutput struct {
	mu         sync.Mutex
	output     *boundedBuffer
	cancel     context.CancelFunc
	pending    []byte
	discarding bool
	denied     bool
}

func (writer *denialOutput) Write(raw []byte) (int, error) {
	n, err := writer.output.Write(raw)
	writer.mu.Lock()
	defer writer.mu.Unlock()
	const maxEventBytes = 2 * 1024 * 1024
	for len(raw) > 0 && !writer.denied {
		end := bytes.IndexByte(raw, '\n')
		part := raw
		if end >= 0 {
			part = raw[:end]
		}
		if len(writer.pending)+len(part) > maxEventBytes {
			writer.pending = nil
			writer.discarding = true
		}
		if !writer.discarding {
			writer.pending = append(writer.pending, part...)
		}
		if end < 0 {
			break
		}
		if !writer.discarding && reportedExecutionDenial(string(writer.pending)) {
			writer.denied = true
			writer.cancel()
		}
		writer.pending = nil
		writer.discarding = false
		raw = raw[end+1:]
	}
	return n, err
}

func (writer *denialOutput) Denied() bool {
	writer.mu.Lock()
	defer writer.mu.Unlock()
	return writer.denied
}

// Finish checks a final JSON event when an adapter omitted the trailing newline.
func (writer *denialOutput) Finish() {
	writer.mu.Lock()
	defer writer.mu.Unlock()
	if !writer.discarding && reportedExecutionDenial(string(writer.pending)) {
		writer.denied = true
	}
	writer.pending = nil
}
