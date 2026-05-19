FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

EXPOSE 8080
ENTRYPOINT ["termimock"]
CMD ["--headless", "--host", "0.0.0.0", "--port", "8080"]

