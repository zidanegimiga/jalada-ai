# Build from apps/web: docker build apps/web
FROM node:24-trixie-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:24-trixie-slim AS build
WORKDIR /app
ARG API_URL=http://localhost:8000
ENV API_URL=$API_URL
# "on" adds the Ask tab, for an API running with JALADA_AGENT_ENABLED=true.
ARG ASSISTANT=off
ENV ASSISTANT=$ASSISTANT
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-trixie-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
