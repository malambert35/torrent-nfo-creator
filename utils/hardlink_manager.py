import subprocess
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_hardlink(source_path, target_path):
    """
    Create a hardlink, with fallback to symlink or copy if cross-device
    
    Args:
        source_path: Original file path
        target_path: Hardlink/link destination path
    
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
        
        # Method 1: Try hardlink with cp -al
        try:
            cmd = ['cp', '-al', str(source), str(target)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Hardlink created: {source} -> {target}")
            return {
                'success': True,
                'source': str(source),
                'target': str(target),
                'message': 'Hardlink created successfully',
                'method': 'hardlink'
            }
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            
            # Check if it's a cross-device error
            if 'cross-device' in error_msg.lower() or 'Invalid cross-device link' in error_msg:
                logger.warning(f"Cross-device detected, using symlink instead")
                
                # Method 2: Create symbolic link (recommended - no extra space)
                os.symlink(source.resolve(), target)
                logger.info(f"Symlink created: {source} -> {target}")
                return {
                    'success': True,
                    'source': str(source),
                    'target': str(target),
                    'message': '✓ Symbolic link created (different filesystems detected)',
                    'method': 'symlink'
                }
            else:
                # Other error - try symlink anyway
                logger.warning(f"cp -al failed, trying symlink: {error_msg}")
                os.symlink(source.resolve(), target)
                return {
                    'success': True,
                    'source': str(source),
                    'target': str(target),
                    'message': '✓ Symbolic link created',
                    'method': 'symlink'
                }
        
    except Exception as e:
        logger.exception(f"All methods failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
