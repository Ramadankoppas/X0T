# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

# جلب أداة uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# زمن انتظار الشبكة
ENV UV_HTTP_TIMEOUT=300

COPY pyproject.toml uv.lock* ./

# تثبيت dependencies
RUN uv sync --no-dev

# نسخ المشروع
COPY . .


# ==========================================
# Stage 2: Final Runtime Image
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

# curl مطلوب للـ Healthcheck في Coolify
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم غير root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system \
        --uid 1001 \
        --ingroup appgroup \
        --home /home/appuser \
        appuser

# نسخ التطبيق والـ virtual environment
COPY --from=builder /app /app

# إنشاء مجلد الرفع
RUN mkdir -p /app/uploads && \
    chown -R appuser:appgroup /app

# Environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]