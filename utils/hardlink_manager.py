import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_hardlink(source_path, target_path):
    """
    Create a hardlink from source to target
    
    Args:
        source_path: Original file path
        target_path: Hardlink destination path
    
    Returns:
        dict with status and message
    """
    try:
        source = Path(source_path)
        target = Path(target_path)
        
        if not source.exists():
            return {
                'success': False,
                'error': 'Source file does not exist'
            }
        
        if target.exists():
            return {
                'success': False,
                'error': 'Target file already exists'
            }
        
        # Create hardlink
        os.link(source, target)
        
        logger.info(f"Hardlink created: {source} -> {target}")
        return {
            'success': True,
            'source': str(source),
            'target': str(target),
            'message': 'Hardlink created successfully'
        }
        
    except OSError as e:
        if e.errno == 18:  # EXDEV - Cross-device link
            error_msg = 'Cannot create hardlink across different filesystems'
        else:
            error_msg = str(e)
        
        logger.error(f"Error creating hardlink: {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        logger.error(f"Unexpected error creating hardlink: {e}")
        return {
            'success': False,
            'error': str(e)
        }
