# --- Etapa 1: Build ---------------------------------
FROM node:18-alpine AS builder
WORKDIR /app

# Copia lock + package para cachear instalación
COPY package.json package-lock.json ./
# Si usas pnpm, en lugar de npm ci pon: RUN npm install -g pnpm && pnpm install
RUN npm ci

# Copia el resto del código y genera la build
COPY . .
RUN npm run build

# --- Etapa 2: Production ---------------------------
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Sólo instalamos dependencias de producción
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copiamos artefactos de la build
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./next.config.mjs

# Exponemos el puerto que usa Next.js (por defecto 3000)
EXPOSE 3001

# Arrancamos el servidor Next.js
CMD ["npm", "run", "start"]
