package mesh

import (
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

var routeToken = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}$`)

func validRouteToken(value string) bool { return routeToken.MatchString(value) }

func gatewayConfiguration() (string, string, error) {
	rawURL := os.Getenv("TASKSPEC_MESH_GATEWAY_URL")
	token := os.Getenv("TASKSPEC_MESH_GATEWAY_TOKEN")
	parsed, err := url.Parse(rawURL)
	if err != nil || parsed.Host == "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" || parsed.Scheme != "http" && parsed.Scheme != "https" {
		return "", "", fmt.Errorf("TASKSPEC_MESH_GATEWAY_URL must be an explicit http(s) OMP auth-gateway URL")
	}
	if len(token) < 16 {
		return "", "", fmt.Errorf("TASKSPEC_MESH_GATEWAY_TOKEN is unavailable or too short")
	}
	return rawURL, token, nil
}

func privateKeyOutsideRepository(repository Repository) (string, string, string, error) {
	privateKey := os.Getenv("TASKSPEC_MESH_ATTESTOR_PRIVATE_KEY")
	publicKey := os.Getenv("TASKSPEC_MESH_ATTESTOR_PUBLIC_KEY")
	registry := os.Getenv("TASKSPEC_MESH_TRUST_REGISTRY")
	for name, value := range map[string]string{
		"TASKSPEC_MESH_ATTESTOR_PRIVATE_KEY": privateKey,
		"TASKSPEC_MESH_ATTESTOR_PUBLIC_KEY":  publicKey,
		"TASKSPEC_MESH_TRUST_REGISTRY":       registry,
	} {
		if value == "" {
			return "", "", "", fmt.Errorf("%s is required for autonomous evidence", name)
		}
		if info, err := os.Stat(value); err != nil || !info.Mode().IsRegular() {
			return "", "", "", fmt.Errorf("%s does not name a readable regular file", name)
		}
	}
	realPrivate, err := filepath.EvalSymlinks(privateKey)
	if err != nil {
		return "", "", "", err
	}
	relative, err := filepath.Rel(repository.Root, realPrivate)
	if err == nil && relative != ".." && !filepath.IsAbs(relative) && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return "", "", "", fmt.Errorf("attestor private key must remain outside the repository")
	}
	return realPrivate, publicKey, registry, nil
}

func randomCapability() (string, error) {
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}

func (store *Store) issueCredential(lease Lease, provider, model, brokerRef string) (CredentialLease, string, error) {
	if !validRouteToken(provider) || !validRouteToken(model) {
		return CredentialLease{}, "", fmt.Errorf("provider and model must use bounded route tokens")
	}
	now := time.Now().UTC()
	expires := now.Add(30 * time.Minute)
	if leaseExpiry, err := time.Parse(time.RFC3339Nano, lease.ExpiresAt); err == nil && leaseExpiry.Before(expires) {
		expires = leaseExpiry
	}
	if raw := os.Getenv("TASKSPEC_MESH_CREDENTIAL_TTL_SEC"); raw != "" {
		if duration, err := time.ParseDuration(raw + "s"); err == nil && duration > 0 && now.Add(duration).Before(expires) {
			expires = now.Add(duration)
		}
	}
	if !expires.After(now) {
		return CredentialLease{}, "", fmt.Errorf("credential lease would already be expired")
	}
	ref := brokerRef
	credential := CredentialLease{
		Contract: "CredentialLease/v1", LeaseID: NewID(), AttemptID: lease.AttemptID,
		Provider: provider, Model: model, Audience: "taskmesh-credential-proxy",
		Scopes: []string{"models.read", "inference.create"}, IssuedAt: now.Format(time.RFC3339Nano),
		ExpiresAt: expires.Format(time.RFC3339Nano), State: "issued", BrokerRef: &ref,
	}
	scopes, _ := json.Marshal(credential.Scopes)
	if _, err := store.db.Exec(
		"INSERT INTO credential_leases(lease_id, attempt_id, provider, model, audience, scopes_json, issued_at, expires_at, state, broker_ref) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		credential.LeaseID, credential.AttemptID, credential.Provider, credential.Model, credential.Audience,
		string(scopes), credential.IssuedAt, credential.ExpiresAt, credential.State, ref,
	); err != nil {
		return CredentialLease{}, "", err
	}
	token, err := randomCapability()
	if err != nil {
		return CredentialLease{}, "", err
	}
	return credential, token, nil
}

func (store *Store) setCredentialState(attemptID, state string) {
	_, _ = store.db.Exec("UPDATE credential_leases SET state = ? WHERE attempt_id = ?", state, attemptID)
}

func writeSecretFile(repository Repository, name, value string) (string, error) {
	directory := filepath.Join(repository.RuntimeDir, "credentials")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return "", err
	}
	if err := os.Chmod(directory, 0o700); err != nil {
		return "", err
	}
	path := filepath.Join(directory, name)
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return "", err
	}
	if _, err := file.WriteString(value + "\n"); err != nil {
		file.Close()
		return "", err
	}
	if err := file.Close(); err != nil {
		return "", err
	}
	return path, nil
}
