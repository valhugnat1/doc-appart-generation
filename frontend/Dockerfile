# =============================================================================
# Frontend Dockerfile - Multi-environment support
# =============================================================================
# Build args allow overriding .env.production values at build time
# =============================================================================

# Build stage
FROM node:20-alpine AS build-stage

WORKDIR /app

# Build arguments (can override .env.production defaults)
ARG VITE_API_BASE_URL
ARG VITE_APP_TITLE
ARG VITE_ENABLE_DEBUG=false
ARG BUILD_MODE=production

# Set environment variables for Vite build
# These override .env.production only if explicitly set
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_TITLE=${VITE_APP_TITLE}
ENV VITE_ENABLE_DEBUG=${VITE_ENABLE_DEBUG}

# Install dependencies
COPY package*.json ./
RUN npm ci --silent

# Copy source files
COPY . .

# Build with specified mode (production, staging, etc.)
RUN npm run build -- --mode ${BUILD_MODE}

# Production stage
FROM nginx:alpine AS production-stage

# Copy built assets
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]