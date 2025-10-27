FROM ghcr.io/berriai/litellm:main-stable
WORKDIR /app

COPY litellm_config.template.yaml /app/
COPY inject_tools.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

EXPOSE 4000
CMD ["/app/run.sh"]
