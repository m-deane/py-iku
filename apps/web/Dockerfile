FROM node:20-alpine

# Install pnpm
RUN npm install -g pnpm@8.15.9

WORKDIR /app

# Copy package manifests for cache efficiency
COPY package.json pnpm-lock.yaml* ./
COPY apps/web/package.json ./apps/web/package.json

# Install deps
RUN pnpm install --filter apps-web --ignore-scripts || pnpm install --ignore-scripts

COPY apps/web/ ./apps/web/

WORKDIR /app/apps/web

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
