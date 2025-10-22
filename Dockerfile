FROM python:3.12-slim
WORKDIR /opt/planka_manager
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "planka_manager.py"]