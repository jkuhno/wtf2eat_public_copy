# Base image for building the binary
FROM python:3.12-slim-bookworm AS build

WORKDIR /app




# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

FROM build AS dev

EXPOSE 8000

CMD ["fastapi", "dev", "api_server/app.py", "--host", "0.0.0.0", "--port", "8080"]


FROM build AS prod

RUN apt-get update && apt-get install -y build-essential libffi-dev python3-dev

RUN pip install pyinstaller

# Use PyInstaller to create a single-file binary
RUN pyinstaller --onefile \
 --hidden-import uvicorn \
 --hidden-import fastapi \
 --hidden-import pydantic \
 --hidden-import pydantic.deprecated.decorator \
 --hidden-import passlib.handlers.bcrypt \
 --name app app.py --log-level DEBUG

# ---------------------
# Final minimal image
FROM debian:bookworm-slim

WORKDIR /app

# Copy the built binary from the builder stage
COPY --from=prod /app/dist/app /app/app

# Run the binary directly
CMD ["/app/app"]
