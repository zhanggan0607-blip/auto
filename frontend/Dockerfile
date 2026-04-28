FROM node:20-alpine AS builder

ARG VERSION=v1.0.0

LABEL maintainer="Bid Auto System"
LABEL version="${VERSION}"

WORKDIR /app

COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

ARG VERSION=v1.0.0

LABEL maintainer="Bid Auto System"
LABEL version="${VERSION}"
LABEL description="天齐AI投标平台 - 前端"

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
