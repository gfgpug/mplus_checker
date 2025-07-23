FROM python:3.12-alpine

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock /app/

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy the rest of the application
COPY . /app/

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]