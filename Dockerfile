FROM python:3.8 as builder

# Exporting poetry as a requirements.txt
WORKDIR /stage-2022-mahdi
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt

FROM python:3.8

ENV PYTHONUNBUFFERED=1
WORKDIR /module
COPY --from=builder /module/requirements.txt .
RUN pip install -r requirements.txt

# Copy the source file
# TODO: Replace by the latest version source
COPY . . 

# Install module
RUN pip install -e .