# ServiceHub AI frontend image.
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies first (leverages Docker layer caching).
COPY package*.json ./
RUN npm ci

# Copy application source and build.
COPY . .
RUN npm run build

# Production stage - serve with nginx.
FROM nginx:alpine

# Copy built assets from builder stage.
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]