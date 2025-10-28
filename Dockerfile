FROM ghcr.io/berriai/litellm:main-stable
WORKDIR /app

ENV LITELLM_PROXY_API_BASE="https://api.openai.com/v1"

COPY litellm_config.template.yaml /app/
COPY inject_tools.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

EXPOSE 4000
ENTRYPOINT ["/app/run.sh"]