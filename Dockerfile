# A recipe for building an image of this app. Docker runs each instruction in order
# and caches the result, so unchanged steps are skipped on later builds.

FROM python:3.12-slim

WORKDIR /app

# Dependencies are copied and installed BEFORE the source code. Docker caches this
# layer, so editing main.py does not trigger a full reinstall of every package.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 0.0.0.0, not 127.0.0.1: inside a container, 127.0.0.1 means "this container only"
# and the port mapping would never reach the app.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
