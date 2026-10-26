FROM python:3.12-slim AS build
WORKDIR /build
ARG PIP_NO_INDEX=0
COPY wheels/ /wheels/
COPY pyproject.toml README.md requirements-lock.txt ./
COPY src ./src
RUN pip install --no-cache-dir --find-links=/wheels setuptools wheel \
    && pip install --no-cache-dir --find-links=/wheels -r requirements-lock.txt \
    && pip install --no-cache-dir --no-build-isolation --no-deps . \
    && pip check

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local /usr/local
COPY --chmod=644 app.py ./
# Mount a verified aggregate-only export read-only at /app/runs/demo.
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EXPOSE 8501
USER 65534:65534
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s CMD python -c "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').read() == b'ok'"
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
