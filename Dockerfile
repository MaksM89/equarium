FROM python:3.11-slim AS base

COPY requirements.txt .
RUN python -m pip install -U --progress-bar off pip && \
    pip install --no-cache-dir -r requirements.txt --progress-bar off --default-timeout=100
COPY src/database src/database

FROM base AS auth
COPY src/*.py /src/
COPY src/authorization/* /src/authorization/
CMD ["uvicorn", "src.authorization.web:app", "--host", "0.0.0.0"]

FROM base AS trans
COPY src/*.py /src/
COPY src/transaction/* /src/transaction/
CMD ["uvicorn", "src.transaction.web:app", "--host", "0.0.0.0"]

FROM base AS dbup
COPY alembic.ini .
COPY src/migrations/* .
CMD ["alembic", "upgrade", "head"]

FROM base AS tester
RUN pip install --no-cache-dir -r requirements.dev.txt --progress-bar off --default-timeout=100