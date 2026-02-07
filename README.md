# Torrent & NFO Creator for Unraid

A Docker container with web interface for creating torrent files and NFO files from video files using mediainfo CLI. Automatically creates hardlinks in your designated folder.

![Docker Pulls](https://img.shields.io/docker/pulls/malambert35/torrent-nfo-creator)
![GitHub](https://img.shields.io/github/license/malambert35/torrent-nfo-creator)

## Features

- 🎬 **Web-based file browser** with real-time search for selecting video files
- 📦 **Automatic torrent creation** using mktorrent
- 📝 **NFO generation** using MediaInfo CLI with full video metadata
- 🔗 **Automatic hardlink creation** to separate folder (preserves disk space)
- ⚙️ **Configurable tracker URLs** and torrent options
- 📁 **Separate output folders** for torrents, NFOs, and hardlinks
- 🔍 **Real-time file search** to quickly find videos
- 🐳 **Optimized for Unraid** with template included
- 🎯 **Private/Public torrent support**
- 🔧 **Customizable piece sizes** or auto-calculation

## Screenshots

Access the web interface at `http://your-unraid-ip:5000`

## Requirements

- Docker
- Unraid 6.9+ (or any Docker-compatible system)
- Source and hardlink folders must be on the same filesystem for hardlinks to work

## Quick Start

### Option 1: Unraid Docker Template (Recommended)

1. Go to **Docker** tab → **Add Container**
2. Set **Repository**: `malambert35/torrent-nfo-creator:latest`
3. Configure paths and variables (see Configuration section below)
4. Click **Apply**

### Option 2: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  torrent-nfo-creator:
    image: malambert35/torrent-nfo-creator:latest
    container_name: torrent-nfo-creator
    ports:
      - "5000:5000"
    volumes:
      - /mnt/user/media:/media:ro
      - /mnt/user/torrents:/torrents:rw
      - /mnt/user/nfo:/nfo:rw
      - /mnt/user/hardlinks:/hardlinks:rw
      - /mnt/user/appdata/torrent-nfo-creator:/config:rw
    environment:
      - PUID=99
      - PGID=100
      - TRACKER_URL=
      - PIECE_SIZE=0
      - PRIVATE_TORRENT=false
      - AUTO_HARDLINK=true
      - NFO_TEMPLATE=full
    restart: unless-stopped
