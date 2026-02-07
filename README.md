# Torrentify - Créateur Automatique de Torrents et NFO pour Unraid

Un container Docker avec interface web pour créer des fichiers torrent et NFO à partir de fichiers vidéo en utilisant MediaInfo CLI. Crée automatiquement des hardlinks (ou symlinks) dans votre dossier désigné avec support des notifications Discord.

![Docker Pulls](https://img.shields.io/docker/pulls/malambert35/torrent-nfo-creator)
![GitHub](https://img.shields.io/github/license/malambert35/torrent-nfo-creator)

## ✨ Fonctionnalités

- 🎬 **Navigateur de fichiers web** avec recherche en temps réel pour sélectionner vos vidéos
- 📦 **Création automatique de torrents** avec mktorrent
- 📝 **Génération de NFO personnalisés** avec formatage professionnel utilisant MediaInfo CLI
- 🔗 **Système de liens intelligent** - hardlinks, symlinks ou copie (fallback automatique)
- 📁 **Sortie organisée** - torrents et NFOs dans des sous-dossiers nommés
- 🔔 **Notifications Discord** via webhooks quand les torrents sont créés
- ⚙️ **URLs de tracker configurables** et options de torrent
- 🔍 **Recherche en temps réel** pour trouver rapidement vos vidéos
- 🐳 **Optimisé pour Unraid** avec template inclus
- 🎯 **Support torrents privés/publics**
- 🔧 **Tailles de pièces personnalisables** ou calcul automatique

## 📋 Prérequis

- Docker
- Unraid 6.9+ (ou tout système compatible Docker)
- URL webhook Discord (optionnel, pour les notifications)

## 🚀 Démarrage Rapide

### Option 1: Template Docker Unraid (Recommandé)

1. Allez dans l'onglet **Docker** → **Add Container**
2. Repository: `malambert35/torrent-nfo-creator:latest`
3. Configurez les chemins et variables (voir section Configuration)
4. Cliquez sur **Apply**

### Option 2: Docker Compose

Créez `docker-compose.yml`:

```yaml
version: '3.8'

services:
  torrent-nfo-creator:
    image: malambert35/torrent-nfo-creator:latest
    container_name: torrent-nfo-creator
    ports:
      - "5000:5000"
    volumes:
      - /mnt/user/data/Films:/media:ro
      - /mnt/user/data/Torrents/Torrentify:/torrents:rw
      - /mnt/user/data/Torrents:/hardlinks:rw
      - /mnt/user/appdata/torrent-nfo-creator:/config:rw
    environment:
      - PUID=99
      - PGID=100
      - TRACKER_URL=
      - PIECE_SIZE=0
      - PRIVATE_TORRENT=false
      - AUTO_HARDLINK=true
      - NFO_TEMPLATE=full
      - DISCORD_WEBHOOK_URL=
    restart: unless-stopped
