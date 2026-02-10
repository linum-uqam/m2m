# Dockerfile for m2m (Meso to Macro Toolkit)
# Uses official ANTs image which has ANTs tools pre-compiled
# Then installs Python and antspyx on top

FROM antsx/ants:latest

# Set metadata
LABEL maintainer="Joël Lefebvre <lefebvre.joel@uqam.ca>"
LABEL description="LINUM's Meso to Macro Toolkit - Neuroimaging analysis tools"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    M2M_CACHE_DIR=/data/cache \
    ANTSPATH=/opt/ants/bin/ \
    PATH=/opt/ants/bin:$PATH

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Create directories for data and scripts
RUN mkdir -p /app /data/cache /data/input /data/output /scripts && \
    chmod 777 /data /scripts

# Set working directory
WORKDIR /app

# Create a virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Activate virtual environment and upgrade pip
RUN . /app/venv/bin/activate && python -m pip install --upgrade pip

# Install setuptools and wheel for building packages
RUN python3 -m pip install setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies from requirements (filter out antspyx to avoid reinstall)
RUN grep -v "antspyx" requirements.txt > requirements-filtered.txt || cp requirements.txt requirements-filtered.txt
RUN pip install -r requirements-filtered.txt

# Install antspyx after pinned deps, without pulling its own dependencies
RUN pip install --no-deps antspyx
# Copy the m2m application
COPY . .

# Install m2m package
RUN pip install -e .

# Expose Streamlit default port
EXPOSE 8501

# Set volumes for data persistence and scripts
VOLUME ["/data/cache", "/data/input", "/data/output", "/scripts"]

# Default command: Run Streamlit app (can be overridden)
CMD ["streamlit", "run", "app/m2m_main_page.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
