# Stage 1: Builder - This stage installs all dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install PyTorch and PyG first
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install torch_geometric

# Install the rest of the packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final - This stage creates the final, clean image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages and executables
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your application code
COPY ./src ./src
# --- REMOVED: No longer copying artifacts at build time ---
# COPY ./artifacts ./artifacts 
COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

