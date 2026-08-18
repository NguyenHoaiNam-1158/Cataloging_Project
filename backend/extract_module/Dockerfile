FROM python:3.12-slim

WORKDIR /app

COPY extract_module/requirements.txt ./extract_module/requirements.txt
RUN pip install --no-cache-dir -r extract_module/requirements.txt

COPY extract_module ./extract_module

CMD ["python", "-m", "extract_module.extract_main"]
