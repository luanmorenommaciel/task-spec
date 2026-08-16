package mesh

import (
	"context"
	"database/sql"
	"time"
)

func (store *Store) RecoverExpired(ctx context.Context) error {
	transaction, err := store.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer transaction.Rollback()
	if err := recoverExpiredTx(transaction, "recovery-"+NewID(), time.Now().UTC()); err != nil {
		return err
	}
	return transaction.Commit()
}

func recoverExpiredTx(transaction *sql.Tx, requestID string, now time.Time) error {
	rows, err := transaction.Query(
		"SELECT " + leaseColumns + " FROM leases WHERE state IN ('leased','preparing','running','verifying','awaiting_supervision')",
	)
	if err != nil {
		return err
	}
	expired := []Lease{}
	for rows.Next() {
		lease, scanErr := scanLease(rows)
		if scanErr != nil {
			rows.Close()
			return scanErr
		}
		expires, parseErr := time.Parse(time.RFC3339Nano, lease.ExpiresAt)
		if parseErr != nil || !expires.After(now) {
			expired = append(expired, lease)
		}
	}
	if err := rows.Close(); err != nil {
		return err
	}
	for _, lease := range expired {
		if _, err := transaction.Exec("UPDATE leases SET state = 'lost', heartbeat_at = ? WHERE attempt_id = ? AND fencing_token = ?", now.Format(time.RFC3339Nano), lease.AttemptID, lease.FencingToken); err != nil {
			return err
		}
		if err := appendRunEvent(transaction, requestID, lease.RunID, lease.AttemptID, lease.FencingToken, "LEASE_LOST", map[string]any{"reason": "expired"}); err != nil {
			return err
		}
	}
	return nil
}
