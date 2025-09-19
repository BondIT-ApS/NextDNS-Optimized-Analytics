#!/bin/sh

# Inject environment variables into static JS file
sed -i "s|__LOCAL_API_KEY__|$LOCAL_API_KEY|g" /usr/share/nginx/html/script.js
sed -i "s|__BACKEND_API_URL__|$BACKEND_API_URL|g" /usr/share/nginx/html/script.js

# Start Nginx
nginx -g 'daemon off;'
