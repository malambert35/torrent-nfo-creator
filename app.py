import os
import logging
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from utils.torrent_creator import create_torrent
from utils.nfo_generator import generate_nfo
from utils.hardlink_manager import create_hardlink
from utils.discord_notifier import send_discord_notification
from utils.radarr_integration import get_radarr_generated_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CONFIG = {
    'MEDIA_PATH': os.getenv('MEDIA_PATH', '/media'),
    'TORRENT_PATH': os.getenv('TORRENT_PATH', '/torrents'),
    'NFO_PATH': os.getenv('NFO_PATH', '/nfo'),
    'HARDLINK_PATH': os.getenv('HARDLINK_PATH', '/hardlinks'),
    'CONFIG_PATH': os.getenv('CONFIG_PATH', '/config'),
    'TRACKER_URL': os.getenv('TRACKER_URL', ''),
    'PIECE_SIZE': int(os.getenv('PIECE_SIZE', '0')),
    'PRIVATE_TORRENT': os.getenv('PRIVATE_TORRENT', 'false').lower() == 'true',
    'AUTO_HARDLINK': os.getenv('AUTO_HARDLINK', 'true').lower() == 'true',
    'NFO_TEMPLATE': os.getenv('NFO_TEMPLATE', 'full'),
    'DISCORD_WEBHOOK_URL': os.getenv('DISCORD_WEBHOOK_URL', ''),
    'RADARR_URL': os.getenv('RADARR_URL', ''),
    'RADARR_API_KEY': os.getenv('RADARR_API_KEY', ''),
    'SONARR_URL': os.getenv('SONARR_URL', ''),
    'SONARR_API_KEY': os.getenv('SONARR_API_KEY', ''),
    'USE_RADARR_NAMES': os.getenv('USE_RADARR_NAMES', 'false').lower() == 'true',
    'PUID': int(os.getenv('PUID', '99')),
    'PGID': int(os.getenv('PGID', '100'))
}

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}

@app.route('/')
def index():
    return render_template('index.html', config=CONFIG)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/browse', methods=['GET'])
def browse_files():
    """Browse media directory for video files"""
    try:
        path = request.args.get('path', CONFIG['MEDIA_PATH'])
        path_obj = Path(path)
        
        if not path_obj.exists():
            return jsonify({'error': 'Path does not exist'}), 404

        items = []
        for item in sorted(path_obj.iterdir()):
            if item.is_dir():
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory'
                })
            elif item.suffix.lower() in VIDEO_EXTS:
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'file',
                    'size': item.stat().st_size
                })

        return jsonify({
            'current_path': str(path_obj),
            'parent_path': str(path_obj.parent) if path_obj.parent != path_obj else None,
            'items': items
        })
        
    except Exception as e:
        logger.exception('Error browsing files')
        return jsonify({'error': str(e)}), 500

@app.route('/radarr/lookup', methods=['POST'])
def radarr_lookup():
    """Lookup movie info from Radarr and get release name (sourceTitle priority)"""
    try:
        data = request.get_json(force=True)
        video_path = data.get('video_path')
        
        if not CONFIG['USE_RADARR_NAMES'] or not CONFIG['RADARR_API_KEY']:
            return jsonify({
                'success': False,
                'message': 'Radarr integration not enabled'
            })
        
        if not video_path or not Path(video_path).exists():
            return jsonify({'error': 'Invalid video file path'}), 400
        
        # Get release name (sourceTitle priority) and movie info
        release_name, movie_info = get_radarr_generated_name(video_path, use_source_title=True)
        
        if not movie_info:
            return jsonify({
                'success': False,
                'message': 'Movie not found in Radarr',
                'original_name': Path(video_path).stem
            })
        
        return jsonify({
            'success': True,
            'standardized_name': release_name,
            'original_name': Path(video_path).stem,
            'movie_info': {
                'title': movie_info.get('title'),
                'year': movie_info.get('year'),
                'quality': movie_info.get('movieFile', {}).get('quality', {}).get('quality', {}).get('name'),
                'tmdb_id': movie_info.get('tmdbId'),
                'imdb_id': movie_info.get('imdbId')
            }
        })
        
    except Exception as e:
        logger.exception('Error looking up Radarr info')
        return jsonify({'error': str(e)}), 500

@app.route('/create', methods=['POST'])
def create():
    """Create torrent, NFO, and hardlink"""
    try:
        data = request.get_json(force=True)
        video_path = data.get('video_path')
        tracker_url = data.get('tracker_url', CONFIG['TRACKER_URL'])
        piece_size = int(data.get('piece_size', CONFIG['PIECE_SIZE']) or 0)
        private = bool(data.get('private', CONFIG['PRIVATE_TORRENT']))
        create_link = bool(data.get('create_hardlink', CONFIG['AUTO_HARDLINK']))
        use_radarr = bool(data.get('use_radarr_name', CONFIG['USE_RADARR_NAMES']))

        if not video_path or not Path(video_path).exists():
            return jsonify({'error': 'Invalid video file path'}), 400

        video_file = Path(video_path)
        original_name = video_file.stem
        video_name = original_name
        radarr_movie = None
        source_title_used = False
        
        # Try to get release name (sourceTitle priority) from Radarr if enabled
        if use_radarr and CONFIG['RADARR_API_KEY'] and CONFIG['RADARR_URL']:
            try:
                release_name, radarr_movie = get_radarr_generated_name(
                    video_path, 
                    use_source_title=True
                )
                
                if radarr_movie:
                    logger.info(f"Using Radarr release name: {release_name}")
                    video_name = release_name
                    # Check if it's likely a sourceTitle (contains dots and quality info)
                    source_title_used = '.' in release_name and any(
                        q in release_name.upper() 
                        for q in ['1080P', '720P', '2160P', 'WEB', 'BLURAY', 'HDTV']
                    )
                else:
                    logger.info("Movie not found in Radarr, using original filename")
            except Exception as e:
                logger.error(f"Radarr lookup failed: {e}, using original filename")
        
        results = {}
        results['name_info'] = {
            'original': original_name,
            'final': video_name,
            'radarr_used': video_name != original_name,
            'source_title_used': source_title_used
        }

        # Create folder named after the video file in torrents directory
        torrent_folder = Path(CONFIG['TORRENT_PATH']) / video_name
        torrent_folder.mkdir(parents=True, exist_ok=True)

        # Create hardlink with the release name in the torrent folder
        renamed_video_path = torrent_folder / f"{video_name}{video_file.suffix}"
        
        if renamed_video_path.exists():
            logger.info(f"Renamed video file already exists: {renamed_video_path}")
        else:
            # Create hardlink with the new name
            try:
                import os
                os.link(str(video_file), str(renamed_video_path))
                logger.info(f"Created hardlink: {video_file} -> {renamed_video_path}")
            except Exception as e:
                logger.error(f"Failed to create hardlink, copying file instead: {e}")
                import shutil
                shutil.copy2(str(video_file), str(renamed_video_path))
        
        # Now use the renamed file for NFO and torrent creation
        video_path_for_processing = str(renamed_video_path)

        # NFO goes inside the folder - pass movie info for enhanced NFO
        nfo_path = torrent_folder / f"{video_name}.nfo"
        nfo_extra_info = {
            'release_name': video_name,
            'original_filename': video_file.name,
            'radarr_movie': radarr_movie
        }
        results['nfo'] = generate_nfo(
            video_path_for_processing,  # Use renamed file
            str(nfo_path), 
            CONFIG['NFO_TEMPLATE'],
            extra_info=nfo_extra_info
        )

        # Torrent goes inside the folder - based on renamed file
        torrent_path = torrent_folder / f"{video_name}.torrent"
        results['torrent'] = create_torrent(
            video_path_for_processing,  # Use renamed file
            str(torrent_path),
            tracker_url,
            piece_size,
            private
        )

        # Additional hardlink to HARDLINK_PATH (separate location) if requested
        if create_link:
            hardlink_path = Path(CONFIG['HARDLINK_PATH']) / f"{video_name}{video_file.suffix}"
            
            if hardlink_path.exists():
                results['hardlink'] = {
                    'success': True,
                    'message': 'File already exists (skipped)',
                    'target': str(hardlink_path),
                    'method': 'skipped'
                }
            else:
                results['hardlink'] = create_hardlink(str(video_file), str(hardlink_path))

        # Check if critical operations succeeded (NFO and Torrent)
        critical_success = (
            results.get('nfo', {}).get('success', False) and
            results.get('torrent', {}).get('success', False)
        )
        
        # Send Discord notification
        if CONFIG['DISCORD_WEBHOOK_URL'] and critical_success:
            send_discord_notification(
                CONFIG['DISCORD_WEBHOOK_URL'],
                video_name,
                {'success': critical_success, **results}
            )
        
        return jsonify({
            'success': critical_success,
            'results': results
        }), (200 if critical_success else 500)

    except Exception as e:
        logger.exception('Error in create')
        return jsonify({'error': str(e)}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive data)"""
    safe_config = {
        'MEDIA_PATH': CONFIG['MEDIA_PATH'],
        'TORRENT_PATH': CONFIG['TORRENT_PATH'],
        'HARDLINK_PATH': CONFIG['HARDLINK_PATH'],
        'TRACKER_URL': CONFIG['TRACKER_URL'],
        'PIECE_SIZE': CONFIG['PIECE_SIZE'],
        'PRIVATE_TORRENT': CONFIG['PRIVATE_TORRENT'],
        'AUTO_HARDLINK': CONFIG['AUTO_HARDLINK'],
        'NFO_TEMPLATE': CONFIG['NFO_TEMPLATE'],
        'USE_RADARR_NAMES': CONFIG['USE_RADARR_NAMES'],
        'RADARR_ENABLED': bool(CONFIG['RADARR_URL'] and CONFIG['RADARR_API_KEY']),
        'DISCORD_ENABLED': bool(CONFIG['DISCORD_WEBHOOK_URL'])
    }
    return jsonify(safe_config)

if __name__ == '__main__':
    # Ensure all directories exist
    for p in [CONFIG['MEDIA_PATH'], CONFIG['TORRENT_PATH'], CONFIG['NFO_PATH'], 
              CONFIG['HARDLINK_PATH'], CONFIG['CONFIG_PATH']]:
        try:
            Path(p).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create directory {p}: {e}")
    
    # Log configuration
    logger.info("=" * 60)
    logger.info("Torrentify - Configuration")
    logger.info("=" * 60)
    logger.info(f"Media Path: {CONFIG['MEDIA_PATH']}")
    logger.info(f"Torrent Path: {CONFIG['TORRENT_PATH']}")
    logger.info(f"Hardlink Path: {CONFIG['HARDLINK_PATH']}")
    logger.info(f"Radarr Integration: {'Enabled' if CONFIG['RADARR_URL'] and CONFIG['RADARR_API_KEY'] else 'Disabled'}")
    logger.info(f"Discord Notifications: {'Enabled' if CONFIG['DISCORD_WEBHOOK_URL'] else 'Disabled'}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
