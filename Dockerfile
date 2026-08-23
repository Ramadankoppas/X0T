# ==========================================
# Stage 2: Final Runtime Image
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

#Healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم غير جذر للـ Security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /home/appuser appuser

COPY --from=builder /app /app

# إنشاء مجلد الرفع وإعطاء الصلاحيات للمستخدم
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]