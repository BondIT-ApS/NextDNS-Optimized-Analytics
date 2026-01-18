#!/bin/sh

# Create a runtime configuration that can be read by the app
cat > /usr/share/nginx/html/config.js << EOF
window.ENV = {
  API_BASE_URL: "${API_BASE_URL:-/api}",
  ENVIRONMENT: "${NODE_ENV:-production}"
  // SECURITY: API keys must NOT be exposed to frontend
  // Frontend uses JWT tokens for authentication
};
EOF

# Start Nginx
nginx -g 'daemon off;'