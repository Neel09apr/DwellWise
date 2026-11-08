# AWS Lambda container image for the nightly pipeline.
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY dwellwise_pipeline ${LAMBDA_TASK_ROOT}/dwellwise_pipeline
COPY sql ${LAMBDA_TASK_ROOT}/sql

CMD ["dwellwise_pipeline.handler.handler"]
