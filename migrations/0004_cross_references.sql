-- SPEC-006 (2026-11-11): cross-service references between the finance cells (investments).
-- Append-only: do not edit once applied.

-- The relay sends a record's events in insert order (the row lock makes it the commit order).
ALTER TABLE investments.outbox ADD COLUMN seq bigint GENERATED ALWAYS AS IDENTITY;
DROP INDEX investments.outbox_unrelayed;
CREATE INDEX outbox_unrelayed ON investments.outbox (seq) WHERE relayed_at IS NULL;

-- SPEC-006: cross-service references, fed by finance.events.v1.
CREATE TABLE investments.ref_targets (
    workspace_id   uuid NOT NULL,
    target         text NOT NULL,
    record_id      bigint NOT NULL,
    status         text,
    deleted        boolean NOT NULL DEFAULT false,
    record_version bigint NOT NULL DEFAULT 0,
    event_seq      bigint NOT NULL DEFAULT 0,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, target, record_id)
);
CREATE TABLE investments.ref_sources (
    workspace_id    uuid NOT NULL,
    source          text NOT NULL,
    source_id       bigint NOT NULL,
    field           text NOT NULL,
    target_resource text NOT NULL,
    target_id       bigint,
    deleted         boolean NOT NULL DEFAULT false,
    record_version  bigint NOT NULL DEFAULT 0,
    event_seq       bigint NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, source, source_id, field)
);
CREATE INDEX ref_sources_live ON investments.ref_sources (workspace_id, target_resource, target_id) WHERE NOT deleted;
CREATE TABLE investments.ref_offsets (
    topic       text NOT NULL,
    partition   integer NOT NULL,
    next_offset bigint NOT NULL,
    PRIMARY KEY (topic, partition)
);
ALTER TABLE investments.ref_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments.ref_targets FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON investments.ref_targets USING (workspace_id = investments.current_workspace());
CREATE POLICY publisher_sync ON investments.ref_targets TO investments_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON investments.ref_targets TO investments_api;
GRANT SELECT, INSERT, UPDATE ON investments.ref_targets TO investments_publisher;
ALTER TABLE investments.ref_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments.ref_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON investments.ref_sources USING (workspace_id = investments.current_workspace());
CREATE POLICY publisher_sync ON investments.ref_sources TO investments_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON investments.ref_sources TO investments_api;
GRANT SELECT, INSERT, UPDATE ON investments.ref_sources TO investments_publisher;
GRANT SELECT, INSERT, UPDATE ON investments.ref_offsets TO investments_publisher;

-- Rows written before SPEC-005 announce themselves once, so other cells learn their ids.
ALTER TABLE investments.outbox NO FORCE ROW LEVEL SECURITY;
ALTER TABLE investments.investments NO FORCE ROW LEVEL SECURITY;
INSERT INTO investments.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'investments.investment.snapshot', 'empire:investments:investment:' || id, 'confidential', jsonb_build_object('investment_type', investment_type, 'scope', scope, 'account_id', account_id, 'currency', currency, 'acquired_on', acquired_on, 'status', status, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM investments.investments ORDER BY id;
ALTER TABLE investments.investments FORCE ROW LEVEL SECURITY;
ALTER TABLE investments.market_price_snapshots NO FORCE ROW LEVEL SECURITY;
INSERT INTO investments.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'investments.market-price.snapshot', 'empire:investments:market-price:' || id, 'confidential', jsonb_build_object('currency', currency, 'source_type', source_type, 'quality', quality, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM investments.market_price_snapshots ORDER BY id;
ALTER TABLE investments.market_price_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE investments.valuation_snapshots NO FORCE ROW LEVEL SECURITY;
INSERT INTO investments.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'investments.valuation.snapshot', 'empire:investments:valuation:' || id, 'confidential', jsonb_build_object('investment_id', investment_id, 'market_price_id', market_price_id, 'currency', currency, 'valuation_method', valuation_method, 'coverage_status', coverage_status, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM investments.valuation_snapshots ORDER BY id;
ALTER TABLE investments.valuation_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE investments.outbox FORCE ROW LEVEL SECURITY;
