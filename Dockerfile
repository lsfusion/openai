# Dockerfile
FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app
COPY litellm_config.template.yaml /app/litellm_config.template.yaml
COPY inject_tools.py /app/inject_tools.py
COPY run.sh /app/run.sh

RUN chmod +x /app/run.sh

EXPOSE 4000
CMD ["/app/run.sh"]
