FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    HOST=0.0.0.0 \
    PORT=8800 \
    DATABASE_PATH=/app/backend/instance/hengchi_quant.db
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY backend /app/backend
COPY frontend /app/frontend
COPY static /app/static
COPY fixtures /app/fixtures
WORKDIR /app/backend
EXPOSE 8800
CMD ["hypercorn", "app.main:app", "--bind", "0.0.0.0:8800"]
