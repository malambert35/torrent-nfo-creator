# Torrent & NFO Creator for Unraid

A Docker container with web interface for creating torrent files and NFO files from video files using mediainfo CLI. Automatically creates hardlinks in your torrent folder.

## Features

- 🎬 Web-based file browser for selecting video files
- 📦 Automatic torrent file creation using mktorrent
- 📝 NFO generation using MediaInfo CLI
- 🔗 Automatic hardlink creation to torrent folder
- ⚙️ Configurable tracker URLs and torrent options
- 🐳 Optimized for Unraid with template included

## Installation on Unraid

### Method 1: Community Applications (Future)
Search for "Torrent NFO Creator" in Community Applications

### Method 2: Template Repository
1. Go to Docker tab → Template Repositories
2. Add: `https://raw.githubusercontent.com/malambert35/unraid-templates/main/`
3. Click "Add Container" and select "torrent-nfo-creator"

### Method 3: Manual Docker Compose
1. Create directory: `/mnt/user/appdata/torrent-nfo-creator/`
2. Copy `docker-compose.yml` to that directory
3. Run: `docker-compose up -d`

## Configuration

### Volume Mappings
- `/media` - Your source video files (read-only recommended)
- `/torrents` - Output for torrent files and hardlinks
- `/nfo` - Output for NFO files (optional)
- `/config` - Application configuration

**Important**: `/media` and `/torrents` must be on the same filesystem for hardlinks to work!

### Environment Variables
- `TRACKER_URL` - Default tracker announce URL
- `PIECE_SIZE` - Torrent piece size in KB (0 = auto)
- `PRIVATE_TORRENT` - Create private torrents (true/false)
- `AUTO_HARDLINK` - Automatically create hardlinks (true/false)
- `NFO_TEMPLATE` - MediaInfo format (full/basic/custom)
- `PUID` / `PGID` - User/Group ID for file permissions

## Usage

1. Access web interface at `http://your-unraid-ip:5000`
2. Browse and select a video file
3. Configure tracker URL and options
4. Click "Create Torrent & NFO"
5. Files will be created in configured locations

## Building

```bash
docker build -t malambert35/torrent-nfo-creator .
docker push malambert35/torrent-nfo-creator
