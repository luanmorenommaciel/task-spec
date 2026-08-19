package mesh

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// SelectedRoute is the runtime pick: adapter plus named model. It is not a
// DispatchDecision field; that contract stays adapter-only.
type SelectedRoute struct {
	Adapter      string `json:"adapter"`
	Mode         string `json:"mode"`
	Model        string `json:"model"`
	Provider     string `json:"provider"`
	Source       string `json:"source"`
	RosterDigest string `json:"roster_digest,omitempty"`
	Kind         string `json:"kind,omitempty"`
	Effort       string `json:"effort,omitempty"`
}

type RosterCandidate struct {
	Adapter  string `json:"adapter"`
	Model    string `json:"model"`
	Provider string `json:"provider,omitempty"`
}

type RosterBand struct {
	Mode       string            `json:"mode,omitempty"`
	Candidates []RosterCandidate `json:"candidates"`
}

type RosterKind struct {
	Mode   string   `json:"mode,omitempty"`
	Prefer []string `json:"prefer"`
}

type Roster struct {
	Contract          string                `json:"contract"`
	RequireNamedModel bool                  `json:"require_named_model"`
	Failover          string                `json:"failover,omitempty"`
	Bands             map[string]RosterBand `json:"bands"`
	Kinds             map[string]RosterKind `json:"kinds,omitempty"`
	Digest            string                `json:"-"`
	Path              string                `json:"-"`
}

func rosterPaths(repository Repository) []string {
	if explicit := os.Getenv("TASKSPEC_MESH_ROSTER"); explicit != "" {
		return []string{explicit}
	}
	return []string{
		filepath.Join(repository.Root, "tasks", ".mesh", "roster.json"),
		filepath.Join(repository.Root, ".taskspec", "mesh-roster.json"),
	}
}

func LoadRoster(repository Repository) (*Roster, error) {
	for _, path := range rosterPaths(repository) {
		raw, err := os.ReadFile(path)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return nil, fmt.Errorf("read mesh roster %s: %w", path, err)
		}
		var roster Roster
		if err := json.Unmarshal(raw, &roster); err != nil {
			return nil, fmt.Errorf("decode mesh roster %s: %w", path, err)
		}
		if roster.Contract != "TaskMeshRoster/v1" {
			return nil, fmt.Errorf("invalid mesh roster contract in %s", path)
		}
		if len(roster.Bands) == 0 {
			return nil, fmt.Errorf("mesh roster %s has no bands", path)
		}
		sum := sha256.Sum256(raw)
		roster.Digest, roster.Path = "sha256:"+hex.EncodeToString(sum[:]), path
		return &roster, nil
	}
	return nil, nil
}

func (roster *Roster) bandFor(effort string) (RosterBand, string, bool) {
	if roster == nil {
		return RosterBand{}, "", false
	}
	if effort == "" {
		effort = "S"
	}
	if band, ok := roster.Bands[effort]; ok && len(band.Candidates) > 0 {
		return band, effort, true
	}
	if band, ok := roster.Bands["S"]; ok && len(band.Candidates) > 0 {
		return band, "S", true
	}
	return RosterBand{}, effort, false
}

func (roster *Roster) modelFor(adapter, effort, kind string) (RosterCandidate, bool) {
	if roster == nil {
		return RosterCandidate{}, false
	}
	band, _, ok := roster.bandFor(effort)
	if !ok {
		return RosterCandidate{}, false
	}
	preferred := []string{}
	if kind != "" {
		if override, exists := roster.Kinds[kind]; exists {
			preferred = append(preferred, override.Prefer...)
		}
	}
	search := append(append([]string{}, preferred...), adapter)
	for _, name := range search {
		for _, candidate := range band.Candidates {
			if candidate.Adapter == name && strings.TrimSpace(candidate.Model) != "" {
				if name == adapter || candidate.Adapter == adapter {
					if candidate.Adapter == adapter {
						return candidate, true
					}
				}
			}
		}
	}
	for _, candidate := range band.Candidates {
		if candidate.Adapter == adapter && strings.TrimSpace(candidate.Model) != "" {
			return candidate, true
		}
	}
	return RosterCandidate{}, false
}

func (roster *Roster) preferredAdapters(effort, kind string) []string {
	if roster == nil {
		return nil
	}
	seen, order := map[string]bool{}, []string{}
	appendUnique := func(name string) {
		if name == "" || seen[name] {
			return
		}
		seen[name] = true
		order = append(order, name)
	}
	if kind != "" {
		if override, ok := roster.Kinds[kind]; ok {
			for _, name := range override.Prefer {
				appendUnique(name)
			}
		}
	}
	if band, _, ok := roster.bandFor(effort); ok {
		for _, candidate := range band.Candidates {
			appendUnique(candidate.Adapter)
		}
	}
	return order
}
