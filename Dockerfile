# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

# جلب أداة uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# تعيين زمن الانتظار للشبكة لتجنب انقطاع التحميل
ENV UV_HTTP_TIMEOUT=300

COPY pyproject.toml uv.lock* ./

# 🟢 تثبيت الحزم داخل الـ Builder فقط (سواء كانت CPU أو عادية)
RUN uv sync --no-dev

# نسخ كود المشروع
COPY . .

# ==========================================
# Stage 2: Final Runtime Image
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

# إنشاء مستخدم غير جذر للـ Security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /home/appuser appuser


COPY --from=builder /app /app

# إنشاء مجلد الرفع وإعطاء الصلاحيات للمستخدم
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app

# ضبط متغيرات البيئة المسارات
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

USER appuser

EXPOSE 8000

# التشغيل المباشر من الـ .venv
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]