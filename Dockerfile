FROM ghcr.io/berriai/litellm:main-stable
WORKDIR /app

COPY litellm_config.template.yaml /app/
COPY inject_tools.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

# <-- fix for Responses API litellm_proxy provider
ENV LITELLM_PROXY_API_BASE="http://127.0.0.1:4000"

EXPOSE 4000
ENTRYPOINT ["/app/run.sh"]