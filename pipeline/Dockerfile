# AWS Lambda container image for the nightly pipeline.
# No HEALTHCHECK on purpose: see .trivyignore.yaml.
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY dwellwise_pipeline ${LAMBDA_TASK_ROOT}/dwellwise_pipeline
COPY sql ${LAMBDA_TASK_ROOT}/sql

# Never run as root. Lambda adds its own sandbox user on top; CI invokes the
# image as this user to prove the runtime still starts.
USER 65532:65532

CMD ["dwellwise_pipeline.handler.handler"]
