FROM python:3.11-slim-buster

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501"]
