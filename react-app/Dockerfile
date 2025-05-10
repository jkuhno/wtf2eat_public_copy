FROM node:19.4-bullseye AS base
WORKDIR /usr/src/app
COPY package*.json .
RUN npm install
COPY . .

FROM base AS dev
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM base AS prod
ARG VITE_APP_BACKEND_ADDRESS
ENV VITE_APP_BACKEND_ADDRESS $VITE_APP_BACKEND_ADDRESS
ARG VITE_CF_TURNSTILE_SITE
ENV VITE_CF_TURNSTILE_SITE $VITE_CF_TURNSTILE_SITE
RUN npm run build

# Step 2: Serve with Nginx
FROM nginxinc/nginx-unprivileged
COPY --from=prod /usr/src/app/dist /usr/share/nginx/html
COPY nginx.conf  /etc/nginx/nginx.conf
COPY cert/ /etc/ssl/certs/
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]