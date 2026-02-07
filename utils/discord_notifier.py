import requests
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def send_discord_notification(webhook_url, video_name, results):
    """
    Send Discord notification when torrent is created
    
    Args:
        webhook_url: Discord webhook URL
        video_name: Name of the video file
        results: Dict with nfo, torrent, hardlink results
    
    Returns:
        bool: Success status
    """
    if not webhook_url:
        return False
    
    try:
        # Build status message
        nfo_status = "✅" if results.get('nfo', {}).get('success') else "❌"
        torrent_status = "✅" if results.get('torrent', {}).get('success') else "❌"
        hardlink_status = "✅" if results.get('hardlink', {}).get('success') else "❌"
        
        # Get methods/messages
        hardlink_method = results.get('hardlink', {}).get('method', 'N/A')
        hardlink_msg = results.get('hardlink', {}).get('message', '')
        
        # Create embed
        embed = {
            "title": "🎬 New Torrent Created",
            "description": f"**{video_name}**",
            "color": 0x8bc34a if results.get('success') else 0xff9800,
            "fields": [
                {
                    "name": f"{nfo_status} NFO File",
                    "value": results.get('nfo', {}).get('path', 'Failed')[-100:],
                    "inline": False
                },
                {
                    "name": f"{torrent_status} Torrent File",
                    "value": results.get('torrent', {}).get('path', 'Failed')[-100:],
                    "inline": False
                },
                {
                    "name": f"{hardlink_status} Hardlink/Symlink",
                    "value": f"{results.get('hardlink', {}).get('target', 'Failed')[-80:]}\n*Method: {hardlink_method}*",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Torrent-nfo-creator • Automated Torrent Creator"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        payload = {
            "username": "Torrent-nfo-creator",
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Discord notification sent for: {video_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False
