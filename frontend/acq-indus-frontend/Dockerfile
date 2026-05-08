# Étape 1 : Build de l'application
FROM node:20-alpine AS build

WORKDIR /app

# Copie des fichiers de dépendances
COPY package*.json ./
RUN npm install

# Copie du reste du code et build
COPY . .
RUN npm run build

# Étape 2 : Serveur de production Nginx
FROM nginx:stable-alpine

# Copie des fichiers compilés depuis l'étape précédente vers le dossier Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copie d'une config Nginx personnalisée pour gérer le routage React (optionnel mais conseillé)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]