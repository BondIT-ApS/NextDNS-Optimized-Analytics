#!/bin/sh

# Create a runtime configuration that can be read by the app
cat > /usr/share/nginx/html/config.js << EOF
window.ENV = {
  API_BASE_URL: "${API_BASE_URL:-/api}",
  LOCAL_API_KEY: "${LOCAL_API_KEY:-}",
  ENVIRONMENT: "${NODE_ENV:-production}"
};
EOF

# Start Nginx
nginx -g 'daemon off;'