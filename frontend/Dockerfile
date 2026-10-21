FROM node:22-alpine AS compilar
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Dirección de la API: se fija al compilar
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
ENV PORT=80
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=compilar /app/dist /usr/share/nginx/html
EXPOSE 80
