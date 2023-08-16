FROM python:3.11-slim
WORKDIR /app
ENV COLORTERM=truecolor

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY *.py ./
COPY *.css ./

ENTRYPOINT ["python", "app.py"]