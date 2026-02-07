import requests
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


def get_radarr_movie_info(api_key, radarr_url, file_path):
    """
    Get movie information from Radarr by file path
    
    Args:
        api_key: Radarr API key
        radarr_url: Radarr base URL (http://192.168.1.100:7878)
        file_path: Full path to the video file
    
    Returns:
        dict with movie info or None
    """
    try:
        headers = {'X-Api-Key': api_key}
        
        # Get all movies from Radarr
        response = requests.get(
            f"{radarr_url}/api/v3/movie",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        movies = response.json()
        
        # Find movie by file path
        file_path_str = str(file_path)
        for movie in movies:
            if movie.get('hasFile') and movie.get('movieFile'):
                movie_path = movie['movieFile'].get('path', '')
                if file_path_str in movie_path or Path(movie_path).name == Path(file_path).name:
                    return movie
        
        logger.warning(f"Movie not found in Radarr for: {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error connecting to Radarr: {e}")
        return None


def generate_release_name(movie_info, file_path):
    """
    Generate standardized release name from Radarr movie info
    
    Args:
        movie_info: Movie data from Radarr API
        file_path: Original file path
    
    Returns:
        str: Standardized release name
    """
    try:
        # Basic info
        title = movie_info.get('title', '').replace(' ', '.')
        year = movie_info.get('year', '')
        
        # Quality info from movieFile
        movie_file = movie_info.get('movieFile', {})
        quality = movie_file.get('quality', {}).get('quality', {}).get('name', 'Unknown')
        
        # Parse video/audio from mediaInfo
        media_info = movie_file.get('mediaInfo', {})
        
        # Video codec
        video_codec = media_info.get('videoCodec', 'x264')
        if 'HEVC' in video_codec or 'H.265' in video_codec:
            video_codec = 'x265'
        elif 'AVC' in video_codec or 'H.264' in video_codec:
            video_codec = 'x264'
        
        # Audio codec
        audio_codec = media_info.get('audioCodec', '')
        audio_channels = media_info.get('audioChannels', '')
        
        audio_str = ''
        if audio_codec:
            if 'DTS-HD' in audio_codec or 'DTS-MA' in audio_codec:
                audio_str = 'DTS-HD.MA'
            elif 'DTS' in audio_codec:
                audio_str = 'DTS'
            elif 'TrueHD' in audio_codec or 'Atmos' in audio_codec:
                audio_str = 'TrueHD.Atmos'
            elif 'AC3' in audio_codec or 'DD' in audio_codec:
                audio_str = 'AC3'
            elif 'AAC' in audio_codec:
                audio_str = 'AAC'
            
            if audio_channels:
                audio_str += f'.{audio_channels}'
        
        # HDR info
        video_dynamic_range = media_info.get('videoDynamicRange', '')
        hdr_str = ''
        if 'HDR' in video_dynamic_range:
            hdr_str = 'HDR'
        if 'DV' in video_dynamic_range or 'Dolby' in video_dynamic_range:
            hdr_str = 'DV.HDR' if hdr_str else 'DV'
        
        # Source (BluRay, WEB-DL, etc.)
        source = 'BluRay'
        if 'WEB' in quality:
            source = 'WEB-DL'
        elif 'Remux' in quality:
            source = 'BluRay.REMUX'
        
        # Resolution
        resolution = quality
        if '2160p' in quality:
            resolution = '2160p'
        elif '1080p' in quality:
            resolution = '1080p'
        elif '720p' in quality:
            resolution = '720p'
        
        # Group name (use original if present, else custom)
        group = 'Torrentify'
        original_name = Path(file_path).stem
        group_match = re.search(r'-([A-Z0-9]+)$', original_name)
        if group_match:
            group = group_match.group(1)
        
        # Build release name
        parts = [title, str(year), resolution]
        
        if hdr_str:
            parts.append(hdr_str)
        
        parts.append(source)
        
        if audio_str:
            parts.append(audio_str)
        
        parts.append(video_codec)
        
        release_name = '.'.join(parts) + f'-{group}'
        
        # Clean up
        release_name = re.sub(r'\.+', '.', release_name)
        
        return release_name
        
    except Exception as e:
        logger.error(f"Error generating release name: {e}")
        return Path(file_path).stem


def get_sonarr_episode_info(api_key, sonarr_url, file_path):
    """
    Get TV show episode information from Sonarr
    Similar to Radarr but for TV shows
    """
    try:
        headers = {'X-Api-Key': api_key}
        
        # Get episode file info
        response = requests.get(
            f"{sonarr_url}/api/v3/episodefile",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        episode_files = response.json()
        
        file_path_str = str(file_path)
        for ep_file in episode_files:
            if file_path_str in ep_file.get('path', ''):
                # Get full episode details
                episode_id = ep_file.get('episodeId')
                if episode_id:
                    ep_response = requests.get(
                        f"{sonarr_url}/api/v3/episode/{episode_id}",
                        headers=headers,
                        timeout=10
                    )
                    return ep_response.json()
        
        return None
        
    except Exception as e:
        logger.error(f"Error connecting to Sonarr: {e}")
        return None
