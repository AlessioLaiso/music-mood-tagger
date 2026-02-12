# Use Python 3.9 Slim (Linux)
FROM python:3.9-slim

# Install system dependencies (FFmpeg is required for audio analysis)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install the AI libraries (Linux versions)
RUN pip install essentia-tensorflow mutagen numpy wget

WORKDIR /app
CMD ["python", "tagger.py"]