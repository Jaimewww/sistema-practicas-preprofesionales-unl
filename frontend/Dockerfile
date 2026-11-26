# Frontend image for the internship tracking system (Angular).
#
# Multi-stage: Node builds the bundle, nginx serves it as static files.
# The build uses environment.real.ts (useMock=false) so the container talks to
# the real API at http://localhost:8000/api/v1, the same URL `npm run start:real`
# uses. The production build is kept (optimized assets) by copying the real
# environment over the default one before building.

FROM node:22-alpine AS build

WORKDIR /app

# package.json + lock first so a source change does not reinstall node_modules.
COPY package.json package-lock.json ./
RUN npm ci

COPY . ./
RUN cp src/environments/environment.real.ts src/environments/environment.ts \
    && npx ng build --configuration production

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80
