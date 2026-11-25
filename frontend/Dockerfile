# Bước 1: build React thành file tĩnh
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Bước 2: nginx phục vụ file tĩnh + chuyển /api sang backend. Image cuối không chứa Node
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
