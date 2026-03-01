# Use Python 3.12 so the 'cgi' module exists (removed in 3.13+)
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
ENV PORT=5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
