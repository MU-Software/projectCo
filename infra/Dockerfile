ARG PYTHON_VERSION=3.12
FROM --platform=linux/arm64 python:${PYTHON_VERSION}-slim-bookworm
SHELL [ "/bin/bash", "-euxvc"]

ENV PATH="${PATH}:/root/.local/bin:" \
    TZ=Asia/Seoul \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONUNBUFFERED=1

COPY --chown=nobody:nobody pyproject.toml poetry.lock /

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl wget ca-certificates gnupg lsb-release gcc git libpq-dev \
    # Install poetry
    && curl -sSL https://install.python-poetry.org | python - \
    && poetry config virtualenvs.create false  \
    && poetry config installer.max-workers 10 \
    && poetry install --only main --no-interaction --no-ansi --no-root \
    # Install sentry-cli
    && curl -sL https://sentry.io/get-cli/ | bash \
    # Clean up apt
    && apt-get autoremove -y \
    && apt-get autoclean -y \
    && apt-get clean -y \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

ARG GIT_HASH
ENV DEPLOYMENT_GIT_HASH=$GIT_HASH

# Make docker to always copy app directory so that source code can be refreshed.
ARG IMAGE_BUILD_DATETIME=unknown
ENV DEPLOYMENT_IMAGE_BUILD_DATETIME=$IMAGE_BUILD_DATETIME

# Copy main app
COPY --chown=nobody:nobody ../alembic.ini ./alembic.ini
COPY --chown=nobody:nobody ../src/ /src

# The reason for using nobody user is to avoid running the app as root, which can be a security risk.
USER nobody
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:18000", "src:create_app()", "--worker-class", "uvicorn.workers.UvicornWorker"]
