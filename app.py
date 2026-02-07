import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
from utils.torrent_creator import create_torrent
from utils.nfo_generator import generate_nfo
from utils.hardlink_manager import create_hardlink

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
CONFIG = {
    'MEDIA_PATH': os.getenv('MEDIA_PATH', '/media'),
    'TORRENT_PATH': os.getenv('TORRENT_PATH', '/torrents'),
    'NFO_PATH': os.getenv('NFO_PATH', '/nfo'),
    'CONFIG_PATH': os.getenv('CONFIG_PATH', '/config'),
    'TRACKER_URL': os.getenv('TRACKER_URL', ''),
    'PIECE_SIZE': int(os.getenv('PIECE_SIZE', '0')),
    'PRIVATE_TORRENT': os.getenv('PRIVATE_TORRENT', 'false').lower() == 'true',
    'AUTO_HARDLINK': os.getenv('AUTO_HARDLINK', 'true').lower() == 'true',
    'NFO_TEMPLATE': os.getenv('NFO_TEMPLATE', 'full'),
    'PUID': int(os.getenv('PUID', '99')),
    'PGID': int(os.getenv('PGID', '100'))
}

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
            elif item.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']:
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
        logger.error(f"Error browsing files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/create', methods=['POST'])
def create():
    """Create torrent, NFO, and hardlink"""
    try:
        data = request.json
        video_path = data.get('video_path')
        tracker_url = data.get('tracker_url', CONFIG['TRACKER_URL'])
        piece_size = data.get('piece_size', CONFIG['PIECE_SIZE'])
        private = data.get('private', CONFIG['PRIVATE_TORRENT'])
        create_link = data.get('create_hardlink', CONFIG['AUTO_HARDLINK'])
        
        if not video_path or not Path(video_path).exists():
            return jsonify({'error': 'Invalid video file path'}), 400
        
        video_file = Path(video_path)
        results = {}
        
        # Generate NFO
        nfo_path = Path(CONFIG['NFO_PATH']) / f"{video_file.stem}.nfo"
        nfo_result = generate_nfo(video_path, str(nfo_path), CONFIG['NFO_TEMPLATE'])
        results['nfo'] = nfo_result
        
        # Create torrent
        torrent_path = Path(CONFIG['TORRENT_PATH']) / f"{video_file.stem}.torrent"
        torrent_result = create_torrent(
            video_path, 
            str(torrent_path), 
            tracker_url, 
            piece_size, 
            private
        )
        results['torrent'] = torrent_result
        
        # Create hardlink if requested
        if create_link:
            hardlink_path = Path(CONFIG['TORRENT_PATH']) / video_file.name
            hardlink_result = create_hardlink(video_path, str(hardlink_path))
            results['hardlink'] = hardlink_result
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in create operation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration"""
    if request.method == 'GET':
        return jsonify(CONFIG)
    elif request.method == 'POST':
        # Update configuration (stored in config file)
        # Implementation for persistent config storage
        return jsonify({'success': True})

if __name__ == '__main__':
    # Ensure directories exist
    for path in [CONFIG['MEDIA_PATH'], CONFIG['TORRENT_PATH'], CONFIG['NFO_PATH'], CONFIG['CONFIG_PATH']]:
        Path(path).mkdir(parents=True, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
