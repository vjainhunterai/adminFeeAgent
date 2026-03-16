# =========================================================
# Frontend Dockerfile — Multi-stage (Build + Nginx)
# =========================================================
# WHAT THIS DOES:
#   Stage 1 "build":
#     - Installs node_modules
#     - Runs "npm run build" → produces static HTML/JS/CSS
#       into /app/dist
#   Stage 2 "production":
#     - Copies those static files into Nginx
#     - Nginx serves them on port 80
#     - Nginx also reverse-proxies /api/* to the backend
# =========================================================

# -------- Stage 1: Build the React app --------
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json first (cached layer — re-installs only when deps change)
COPY package.json package-lock.json* ./
RUN npm install

# Copy all source code and build
COPY . .
RUN npm run build
# Output: /app/dist/  (static files)

# -------- Stage 2: Serve with Nginx --------
FROM nginx:1.25-alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy our built React files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
