FROM public.ecr.aws/lambda/python:3.11

RUN pip install --no-cache-dir fastapi mangum

COPY monitoring_api.py ${LAMBDA_TASK_ROOT}/
COPY geekbrain.db ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_handler.handler"]
