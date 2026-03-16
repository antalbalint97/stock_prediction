# Use official slim Python image for smaller footprint
FROM python:3.10-slim

# Set environment variable BEFORE using it
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set working directory inside the container
WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

CMD ["bash"]
