# For more information, please refer to https://aka.ms/vscode-docker-python
FROM continuumio/anaconda3

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Workdir
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Install the module
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "m2m", "/bin/bash", "-c"]
RUN pip install -e .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "m2m", "streamlit", "run", "app/m2m_main_page.py", "--server.port=8501", "--server.address=0.0.0.0"]
