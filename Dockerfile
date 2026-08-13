FROM python:3.12-slim

ARG WILFRED_HOME_ASSISTANT_REF=60882a1efba3c3a248047ff69c8ca83352263da7

LABEL org.opencontainers.image.title="Wilfred"
LABEL org.opencontainers.image.description="Standalone public Wilfred Butler runtime"
LABEL org.opencontainers.image.source="https://github.com/keriol/butler-wilfred"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HOME=/tmp

WORKDIR /opt/wilfred

RUN groupadd --system wilfred     && useradd         --system         --gid wilfred         --no-create-home         wilfred

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install         --no-cache-dir         --upgrade         pip         setuptools         wheel     && python -m pip install         --no-cache-dir         ".[http,openai]"     && python -m pip install         --no-cache-dir         "httpx>=0.28,<1"     && python -m pip install         --no-cache-dir         --no-deps         "wilfred-home-assistant @ https://github.com/keriol/wilfred-home-assistant/archive/${WILFRED_HOME_ASSISTANT_REF}.tar.gz"     && python -m pip check

USER wilfred

EXPOSE 8000

HEALTHCHECK     --interval=10s     --timeout=3s     --start-period=5s     --retries=3     CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

ENTRYPOINT ["wilfred"]
CMD ["status"]
