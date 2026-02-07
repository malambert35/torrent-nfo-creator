import os
import logging
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from utils.torrent_creator import create_torrent
from utils.nfo_generator import generate_nfo
from utils.hardlink_manager import create_hardlink
from utils.discord_notifier import send_discord_notification

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
    try:
        path = request.args.get('path', CONFIG['MEDIA_PATH'])
        path_obj = Path(path)
        if not path_obj.exists():
            return jsonify({'error': 'Path does not exist'}), 404

        items = []
        for item in sorted(path_obj.iterdir()):
            if item.is_dir():
                items.append({'name': item.name, 'path': str(item), 'type': 'directory'})
            elif item.suffix.lower() in VIDEO_EXTS:
                items.append({'name': item.name, 'path': str(item), 'type': 'file', 'size': item.stat().st_size})

        return jsonify({
            'current_path': str(path_obj),
            'parent_path': str(path_obj.parent) if path_obj.parent != path_obj else None,
            'items': items
        })
    except Exception as e:
        logger.exception('Error browsing files')
        return jsonify({'error': str(e)}), 500

@app.route('/create', methods=['POST'])
def create():
    try:
        data = request.get_json(force=True)
        video_path = data.get('video_path')
        tracker_url = data.get('tracker_url', CONFIG['TRACKER_URL'])
        piece_size = int(data.get('piece_size', CONFIG['PIECE_SIZE']) or 0)
        private = bool(data.get('private', CONFIG['PRIVATE_TORRENT']))
        create_link = bool(data.get('create_hardlink', CONFIG['AUTO_HARDLINK']))

        if not video_path or not Path(video_path).exists():
            return jsonify({'error': 'Invalid video file path'}), 400

        video_file = Path(video_path)
        video_name = video_file.stem
        results = {}

        # Create folder named after the video file in torrents directory
        torrent_folder = Path(CONFIG['TORRENT_PATH']) / video_name
        torrent_folder.mkdir(parents=True, exist_ok=True)

        # NFO goes inside the folder
        nfo_path = torrent_folder / f"{video_name}.nfo"
        results['nfo'] = generate_nfo(str(video_file), str(nfo_path), CONFIG['NFO_TEMPLATE'])

        # Torrent goes inside the folder
        torrent_path = torrent_folder / f"{video_name}.torrent"
        results['torrent'] = create_torrent(str(video_file), str(torrent_path), tracker_url, piece_size, private)

        # Hardlink goes to HARDLINK_PATH (separate location)
        if create_link:
            hardlink_path = Path(CONFIG['HARDLINK_PATH']) / video_file.name
            
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
        critical_success = results.get('nfo', {}).get('success', False) and results.get('torrent', {}).get('success', False)
        
        # Send Discord notification
        if CONFIG['DISCORD_WEBHOOK_URL'] and critical_success:
            send_discord_notification(
                CONFIG['DISCORD_WEBHOOK_URL'],
                video_name,
                {'success': critical_success, **results}
            )
        
        return jsonify({'success': critical_success, 'results': results}), (200 if critical_success else 500)

    except Exception as e:
        logger.exception('Error in create')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure all directories exist
    for p in [CONFIG['MEDIA_PATH'], CONFIG['TORRENT_PATH'], CONFIG['NFO_PATH'], 
              CONFIG['HARDLINK_PATH'], CONFIG['CONFIG_PATH']]:
        Path(p).mkdir(parents=True, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
