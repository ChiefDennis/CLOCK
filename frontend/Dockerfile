# Dockerfile

# STAGE 1: Build the application
# We use the official node image as a parent image. The version should match your project's requirements.
# 'as builder' names this stage, so we can refer to it later.
FROM node:22-alpine AS builder

# ---- Declare build arguments ----
# These ARG instructions make the variables from 'docker-compose.yml' available
# to the subsequent RUN commands in this build stage.
ARG NG_APP_API_BASE_URL
ARG NG_APP_API_AUTH_URL

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
# This step is separated to leverage Docker's layer caching.
# Dependencies are only re-installed if these files change.
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the app's source code
COPY . .

# ---- Replace placeholders before building ----
RUN sed -i "s|__NG_APP_API_BASE_URL__|${NG_APP_API_BASE_URL}|g" src/environments/environment.ts && \
    sed -i "s|__NG_APP_API_AUTH_URL__|${NG_APP_API_AUTH_URL}|g" src/environments/environment.ts
# --------------------------------------------------


# Build the application for production
# This command generates the static files in the 'dist/' directory.

RUN npm run build -- --configuration production

# STAGE 2: Serve the application with Nginx
# We use the latest stable Nginx image.
FROM nginx:1.29.3

# ---- NEW: Install 'gettext' which provides the 'envsubst' utility ----
RUN apt-get update && apt-get install -y gettext-base
# --------------------------------------------------------------------

RUN rm -rf /usr/share/nginx/html/*

# ---- Copy the template file instead of the static config ----
COPY nginx/nginx.conf.template /etc/nginx/conf.d/default.conf.template
# ----------------------------------------------------------------------

COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 /usr/share/nginx/html

EXPOSE 80

# ---- Process the template before starting Nginx ----
CMD ["/bin/sh", "-c", "envsubst '$BACKEND_HOST $BACKEND_PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
# ------------------------------------------------------------------------------