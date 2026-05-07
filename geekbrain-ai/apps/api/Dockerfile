FROM public.ecr.aws/lambda/python:3.11

COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir .

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY geekbrain.db ${LAMBDA_TASK_ROOT}/geekbrain.db

CMD ["lambda_handler.handler"]
