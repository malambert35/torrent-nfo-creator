import subprocess
import logging

logger = logging.getLogger(__name__)

def generate_nfo(video_path, output_path, template='full'):
    """
    Generate NFO file using mediainfo
    
    Args:
        video_path: Path to video file
        output_path: Path where NFO file will be saved
        template: Output format (full, basic, or custom)
    
    Returns:
        dict with status and message
    """
    try:
        cmd = ['mediainfo']
        
        if template == 'full':
            cmd.append('--Full')
        
        cmd.extend(['--LogFile=' + output_path, video_path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info(f"NFO created successfully: {output_path}")
        return {
            'success': True,
            'path': output_path,
            'message': 'NFO file created successfully'
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating NFO: {e.stderr}")
        return {
            'success': False,
            'error': e.stderr
        }
    except Exception as e:
        logger.error(f"Unexpected error creating NFO: {e}")
        return {
            'success': False,
            'error': str(e)
        }
