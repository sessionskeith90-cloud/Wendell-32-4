# ============================================================
# WENDELL Core 33 — Multi-stage Docker build
# Stage 1: Build Rust agents
# Stage 2: Python runtime + Rust binaries
# ============================================================

# ── Stage 1: Rust build ─────────────────────────────────────
FROM rust:1.78-slim AS rust-builder
WORKDIR /build
COPY Cargo.toml ./
COPY agents/ agents/
COPY src/ src/
RUN cargo build --release

# ── Stage 2: Python runtime ─────────────────────────────────
FROM python:3.11-slim
LABEL maintainer="WENDELL Core Team"

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Rust binaries from builder
COPY --from=rust-builder /build/target/release/agent* /app/bin/
COPY --from=rust-builder /build/target/release/hia /app/bin/
COPY --from=rust-builder /build/target/release/hia_shadow /app/bin/
COPY --from=rust-builder /build/target/release/afia /app/bin/
COPY --from=rust-builder /build/target/release/afia_shadow /app/bin/

# Copy Python application
COPY base_agent.py .
COPY agent_wendell.py .
COPY agent_integrator.py .
COPY agent_34_rest_api_gateway.py .
COPY omnisleuth.py .
COPY evaluate.py .
COPY generate_test.py .
COPY security/ security/
COPY lib/ lib/
COPY agents/*.py agents/
COPY templates/ templates/
COPY static/ static/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5001}/api/health || exit 1

# Azure App Service uses PORT env var
ENV PORT=5001
EXPOSE 5001

# Copy WSGI entry point
COPY wsgi.py .

# Start the Wendell dashboard agent via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "--timeout", "120", "wsgi:app"]
