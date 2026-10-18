FROM node:22-bookworm-slim AS frontend
WORKDIR /build
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 RELAY_MODE=cloud PORT=8080
COPY requirements.cloud.txt ./
RUN pip install --no-cache-dir -r requirements.cloud.txt
COPY relay ./relay
COPY fixtures ./fixtures
COPY --from=frontend /build/dist ./dist
COPY infra/entrypoint.py ./entrypoint.py
RUN useradd -m -u 10001 relay
USER relay
CMD ["python","entrypoint.py"]
