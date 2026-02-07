# 🎬 Torrent-nfo-creator

**Torrent-nfo-creator** est un outil Docker tout-en-un pour créer automatiquement des torrents, fichiers NFO et fiches BBCode pour vos films, avec intégration complète Radarr et TMDb.

![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Fonctionnalités principales

### 🎯 Création automatisée
- **Torrents** : Génération de fichiers `.torrent` privés ou publics
- **NFO** : Fichiers NFO enrichis avec MediaInfo complet et métadonnées Radarr
- **BBCode** : Fiches de description au format BBCode (style FicheGen) prêtes à copier-coller
- **Hardlinks** : Création de hardlinks intelligents pour éviter la duplication

### 🎬 Intégration Radarr
- Récupération automatique du **sourceTitle** (nom de release original avant renommage)
- Renommage automatique des fichiers avec le nom de release original
- Métadonnées enrichies : titre, année, qualité, édition, TMDb ID, IMDb ID
- Support complet de l'API Radarr v3

### 🌐 Intégration TMDb
- Récupération automatique des informations complètes du film
- Synopsis en français, genres, réalisateur, acteurs
- Posters et photos des acteurs
- Notes et nombre de votes
- Liens vers bandes-annonces YouTube

### 📄 Génération de fiches BBCode
- Format compatible avec les trackers privés français
- Style **FicheGen** professionnel
- Informations techniques détaillées (codec, audio, sous-titres)
- Drapeaux emoji pour les langues
- Liens TMDb et YouTube intégrés

### 🔔 Notifications Discord
- Alertes en temps réel après chaque création
- Résumé des opérations effectuées
- Statut succès/échec

---

## 🚀 Installation rapide

### Prérequis
- Docker et Docker Compose
- Radarr configuré (optionnel mais recommandé)
- Clé API TMDb (gratuite)

### Docker Compose

```yaml
version: '3.8'

services:
  torrentify:
    image: ghcr.io/yourusername/torrentify:latest
    container_name: torrentify
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - /path/to/your/media:/media
      - /path/to/output/torrents:/torrents
      - /path/to/hardlinks:/hardlinks
      - ./config:/config
    environment:
      # Chemins
      - MEDIA_PATH=/media
      - TORRENT_PATH=/torrents
      - HARDLINK_PATH=/hardlinks
      
      # Tracker
      - TRACKER_URL=http://tracker.example.com:6969/announce
      - PRIVATE_TORRENT=true
      - PIECE_SIZE=0
      
      # Radarr Integration
      - RADARR_URL=http://radarr:7878
      - RADARR_API_KEY=your_radarr_api_key_here
      - USE_RADARR_NAMES=true
      
      # TMDb Integration
      - TMDB_API_KEY=your_tmdb_api_key_here
      
      # Discord Notifications
      - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
      
      # Options
      - AUTO_HARDLINK=true
      - NFO_TEMPLATE=full
      - PUID=1000
      - PGID=1000
