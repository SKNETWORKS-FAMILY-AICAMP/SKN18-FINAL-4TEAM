FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/vue-app/package.json frontend/vue-app/package-lock.json ./
RUN npm ci

COPY frontend/vue-app/ ./

ARG VITE_API_BASE=/api/
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm run build

FROM nginx:1.25-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
