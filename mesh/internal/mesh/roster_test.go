package mesh

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadRosterMissingIsNil(t *testing.T) {
	root := t.TempDir()
	roster, err := LoadRoster(Repository{Root: root})
	if err != nil {
		t.Fatal(err)
	}
	if roster != nil {
		t.Fatalf("expected no roster, got %+v", roster)
	}
}

func TestLoadRosterAndModelFor(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "tasks", ".mesh", "roster.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	body := `{
	  "contract": "TaskMeshRoster/v1",
	  "require_named_model": true,
	  "bands": {
	    "XS": {
	      "mode": "autonomous",
	      "candidates": [
	        {"adapter": "omp-rpc", "model": "deepseek-v4-flash", "provider": "omp"},
	        {"adapter": "grok-native", "model": "grok-4.6"}
	      ]
	    },
	    "S": {
	      "mode": "supervised",
	      "candidates": [
	        {"adapter": "grok-native", "model": "grok-4.6"},
	        {"adapter": "omp-rpc", "model": "deepseek-v4-pro", "provider": "omp"}
	      ]
	    }
	  },
	  "kinds": {
	    "design": {"mode": "supervised", "prefer": ["grok-native", "claude-native"]}
	  }
	}`
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	roster, err := LoadRoster(Repository{Root: root})
	if err != nil || roster == nil {
		t.Fatalf("load roster: %v %#v", err, roster)
	}
	if !roster.RequireNamedModel {
		t.Fatal("expected require_named_model")
	}
	got, ok := roster.modelFor("omp-rpc", "XS", "")
	if !ok || got.Model != "deepseek-v4-flash" || got.Provider != "omp" {
		t.Fatalf("xs omp: %+v ok=%v", got, ok)
	}
	got, ok = roster.modelFor("grok-native", "S", "design")
	if !ok || got.Model != "grok-4.6" {
		t.Fatalf("s grok: %+v ok=%v", got, ok)
	}
	order := roster.preferredAdapters("S", "design")
	if len(order) < 2 || order[0] != "grok-native" {
		t.Fatalf("prefer order: %v", order)
	}
}

func TestLoadRosterRejectsEmptyContract(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, ".taskspec", "mesh-roster.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(`{"contract":"nope","bands":{"S":{"candidates":[{"adapter":"omp-rpc","model":"x"}]}}}`), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadRoster(Repository{Root: root}); err == nil {
		t.Fatal("expected invalid contract")
	}
}
