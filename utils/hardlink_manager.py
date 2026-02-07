import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_hardlink(source_path, target_path):
    """
    Create a hardlink using cp -al command
    
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
                'success': True,
                'message': 'File already exists (skipped)',
                'target': str(target)
            }
        
        # Ensure target directory exists
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Use cp -al to create hardlink
        cmd = ['cp', '-al', str(source), str(target)]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        logger.info(f"Hardlink created: {source} -> {target}")
        return {
            'success': True,
            'source': str(source),
            'target': str(target),
            'message': 'Hardlink created successfully',
            'method': 'cp -al'
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Error creating hardlink with cp -al: {error_msg}")
        return {
            'success': False,
            'error': f'cp -al failed: {error_msg}'
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error creating hardlink: {e}")
        return {
            'success': False,
            'error': str(e)
        }
