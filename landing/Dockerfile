# Use nginx to serve static HTML files
FROM nginx:alpine

# Copy HTML files to nginx html directory
COPY index.html /usr/share/nginx/html/index.html
COPY choisir-bail.html /usr/share/nginx/html/choisir-bail.html

# Create nginx configuration for proper routing
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /choisir-bail { \
        try_files /choisir-bail.html =404; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
