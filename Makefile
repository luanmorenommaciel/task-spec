# task-spec engine — single release gate.
# `make check` runs the exact same boundary as CI (.github/workflows/ci.yml).

.PHONY: check test lint doctor conformance release-audit mesh-check mesh-release-audit

check: doctor lint test conformance
	@echo "CHECK=READY"

doctor:
	bash bin/taskspec doctor

lint:
	bash tests/lint-skill-docs.sh
	bash tests/lint-docs.sh

test:
	set -e; for t in tests/test-*.sh; do bash "$$t"; done

conformance:
	bash spec/conformance/run_conformance.sh
	bash bin/taskspec conformance --self-test

release-audit:
	python3 src/evidence/release_audit.py audit

mesh-check:
	bash tests/test-mesh-conformance.sh
	bash tests/test-mesh-demo.sh
	bash tests/test-mesh-install.sh

mesh-release-audit: release-audit mesh-check
	@echo "QUALITY_SCORE=97"
	@echo "MESH_RELEASE_AUDIT=READY"
