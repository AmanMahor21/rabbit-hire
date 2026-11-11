# Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_URL=/api
ARG VITE_APP_NAME="Rabbit Hire"
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_NAME=$VITE_APP_NAME

# Install dependencies first for optimal Docker layer caching
COPY package*.json ./
RUN npm ci

# Copy application source and build production bundle
COPY . .
RUN npm run build

# Production Serving Stage
FROM nginx:alpine

# Copy compiled static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]