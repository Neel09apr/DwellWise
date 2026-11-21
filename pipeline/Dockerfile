# The nightly pipeline: one short-lived container per run, started by a
# scheduled GitHub Actions workflow. No HEALTHCHECK on purpose: see .trivyignore.yaml.
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dwellwise_pipeline dwellwise_pipeline
COPY sql sql

# Never run as root.
USER 65532:65532

ENTRYPOINT ["python", "-m", "dwellwise_pipeline"]
CMD ["run"]
