# The nightly pipeline: one short-lived container per run, started by a
# scheduled GitHub Actions workflow. No HEALTHCHECK on purpose: see .trivyignore.yaml.
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

# Patch the base image's Debian packages (a fixed CVE should not wait for the next
# python:3.15-slim rebuild), then remove pip: nothing installs at run time, and pip
# carries its own vendored copies of urllib3, msgpack and setuptools that scanners flag.
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y pip

COPY dwellwise_pipeline dwellwise_pipeline
COPY sql sql

# Never run as root.
USER 65532:65532

ENTRYPOINT ["python", "-m", "dwellwise_pipeline"]
CMD ["run"]
