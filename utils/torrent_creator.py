import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_torrent(video_path, output_path, tracker_url, piece_size=0, private=False):
    """
    Create a torrent file using mktorrent
    
    Args:
        video_path: Path to video file
        output_path: Path where torrent file will be saved
        tracker_url: Tracker announce URL
        piece_size: Piece size in KB (0 for auto)
        private: Whether to create a private torrent
    
    Returns:
        dict with status and message
    """
    try:
        cmd = ['mktorrent', '-o', output_path]
        
        if tracker_url:
            cmd.extend(['-a', tracker_url])
        
        if piece_size > 0:
            cmd.extend(['-l', str(piece_size)])
        
        if private:
            cmd.append('-p')
        
        cmd.append(video_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info(f"Torrent created successfully: {output_path}")
        return {
            'success': True,
            'path': output_path,
            'message': 'Torrent file created successfully'
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating torrent: {e.stderr}")
        return {
            'success': False,
            'error': e.stderr
        }
    except Exception as e:
        logger.error(f"Unexpected error creating torrent: {e}")
        return {
            'success': False,
            'error': str(e)
        }
