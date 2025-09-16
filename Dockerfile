# Stage 1: Builder - This stage installs all dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install PyTorch and PyG first, as they have specific dependencies
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install torch_geometric

# Copy the requirements file and install the rest of the packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final - This stage creates the final, clean image
FROM python:3.11-slim

WORKDIR /app

# Copy the installed packages (libraries) from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# --- THIS IS THE FIX ---
# Copy the executables (like uvicorn) from the builder stage
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your application code and artifacts
COPY ./src ./src
COPY ./artifacts ./artifacts
COPY app.py .

# Expose the port the app runs on
EXPOSE 8000

# The command to run when the container starts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]