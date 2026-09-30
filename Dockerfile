FROM node:22-alpine AS base
WORKDIR /app
COPY package.json ./
COPY src ./src
COPY test ./test
COPY scripts ./scripts

FROM base AS lint
RUN npm run lint

FROM base AS test
RUN mkdir -p reports && npm test

FROM node:22-alpine AS production
ENV NODE_ENV=production PORT=3000
WORKDIR /app
COPY --from=base /app/package.json ./
COPY --from=base /app/src ./src
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD node -e "fetch('http://127.0.0.1:3000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "src/server.js"]
