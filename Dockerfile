FROM node:22-bookworm-slim AS development

WORKDIR /workspace

ENV CI=1
ENV FORCE_COLOR=1
ENV NPM_CONFIG_UPDATE_NOTIFIER=false

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

CMD ["npm", "run", "check"]
