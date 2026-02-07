import logging
from pathlib import Path
import subprocess
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def get_tmdb_data(tmdb_id):
    """Fetch additional data from TMDb API"""
    try:
        import requests
        
        # Tu devras ajouter ta clé API TMDb dans les variables d'environnement
        import os
        tmdb_api_key = os.getenv('TMDB_API_KEY', '')
        
        if not tmdb_api_key:
            logger.warning("TMDb API key not configured")
            return None
        
        # Get movie details
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params = {
            'api_key': tmdb_api_key,
            'language': 'fr-FR',
            'append_to_response': 'credits,release_dates,videos'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"Error fetching TMDb data: {e}")
        return None


def format_duration(minutes):
    """Convert minutes to h:mm format"""
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h{mins:02d}"


def get_country_flag(country_code):
    """Convert country code to flag emoji"""
    flags = {
        'en': '🇺🇸',
        'fr': '🇫🇷',
        'es': '🇪🇸',
        'de': '🇩🇪',
        'it': '🇮🇹',
        'pt': '🇵🇹',
        'ja': '🇯🇵',
        'ko': '🇰🇷',
        'zh': '🇨🇳',
        'ru': '🇷🇺'
    }
    return flags.get(country_code.lower(), '🌐')


def generate_bbcode_description(video_path, radarr_movie=None, release_name=None):
    """
    Generate BBCode description matching the FicheGen format
    """
    try:
        video_file = Path(video_path)
        
        # Get MediaInfo data
        cmd = ['mediainfo', '--Output=JSON', str(video_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        media_data = json.loads(result.stdout)
        
        tracks = media_data.get('media', {}).get('track', [])
        general_track = next((t for t in tracks if t.get('@type') == 'General'), {})
        video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
        audio_tracks = [t for t in tracks if t.get('@type') == 'Audio']
        text_tracks = [t for t in tracks if t.get('@type') == 'Text']
        
        # Get TMDb data if available
        tmdb_data = None
        if radarr_movie and radarr_movie.get('tmdbId'):
            tmdb_data = get_tmdb_data(radarr_movie.get('tmdbId'))
        
        # Build BBCode
        bbcode = ""
        
        # ============ HEADER ============
        title = radarr_movie.get('title', release_name or video_file.stem) if radarr_movie else (release_name or video_file.stem)
        year = radarr_movie.get('year', '') if radarr_movie else ''
        
        bbcode += f"[center][b][font=Verdana][color=#3d85c6][size=29]{title}[/size]\n"
        bbcode += f"    \n"
        bbcode += f"    [size=18]({year})[/size][/color][/font][/b]\n\n"
        
        # Poster
        poster_url = None
        if radarr_movie and radarr_movie.get('images'):
            poster_url = next((img.get('remoteUrl') for img in radarr_movie.get('images', []) if img.get('coverType') == 'poster'), None)
        
        if poster_url:
            bbcode += f"[img]{poster_url}[/img]\n\n"
        
        # Tagline
        tagline = tmdb_data.get('tagline', '') if tmdb_data else ''
        if tagline:
            bbcode += f'[color=#ea9999][i][b][font=Verdana][size=29]\n"{tagline}"[/size][/font][/b][/i][/color]\n\n'
        
        # Separator
        bbcode += "[img]https://i.imgur.com/EXBOmiU.png[/img]\n\n"
        
        # ============ MOVIE INFO ============
        bbcode += "[font=Verdana][size=13]"
        
        # Original title
        original_title = radarr_movie.get('originalTitle', title) if radarr_movie else title
        bbcode += f"[b][color=#3d85c6]Titre original :[/color][/b] [i]{original_title}[/i]\n"
        
        # Country
        if tmdb_data and tmdb_data.get('production_countries'):
            countries = ', '.join([c.get('name', '') for c in tmdb_data.get('production_countries', [])])
            bbcode += f"[b][color=#3d85c6]Pays :[/color][/b] [i]{countries}[/i]\n"
        
        # Genres
        if radarr_movie and radarr_movie.get('genres'):
            genres_list = [f"[i][url=/torrents?tags={g.get('name')}]{g.get('name')}[/url][/i]" for g in radarr_movie.get('genres', [])]
            genres_str = ', '.join(genres_list)
            bbcode += f"[b][color=#3d85c6]Genres :[/color][/b] {genres_str}\n"
        
        # Release date
        if tmdb_data and tmdb_data.get('release_date'):
            release_date_str = tmdb_data.get('release_date')
            try:
                from datetime import datetime
                release_date = datetime.strptime(release_date_str, '%Y-%m-%d')
                formatted_date = release_date.strftime('%d %B %Y')
                # Translate month to French
                months_fr = {
                    'January': 'janvier', 'February': 'février', 'March': 'mars',
                    'April': 'avril', 'May': 'mai', 'June': 'juin',
                    'July': 'juillet', 'August': 'août', 'September': 'septembre',
                    'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
                }
                for en, fr in months_fr.items():
                    formatted_date = formatted_date.replace(en, fr)
                bbcode += f"[b][color=#3d85c6]Date de sortie :[/color][/b] [i]{formatted_date}[/i]\n"
            except:
                pass
        
        # Duration
        runtime = radarr_movie.get('runtime') if radarr_movie else None
        if runtime:
            bbcode += f"[b][color=#3d85c6]Durée :[/color][/b] [i]{format_duration(runtime)}[/i]\n"
        
        # Director
        if tmdb_data and tmdb_data.get('credits', {}).get('crew'):
            directors = [c.get('name') for c in tmdb_data['credits']['crew'] if c.get('job') == 'Director']
            if directors:
                bbcode += f"[b][color=#3d85c6] Réalisateur :[/color][/b] [i]{', '.join(directors)}[/i]\n"
        
        # Actors
        if tmdb_data and tmdb_data.get('credits', {}).get('cast'):
            actors = [c.get('name') for c in tmdb_data['credits']['cast'][:5]]
            if actors:
                bbcode += f"[b][color=#3d85c6]Acteurs :[/color][/b] [i] {', '.join(actors)}[/i]\n\n"
            
            # Actor images
            actor_images = []
            for actor in tmdb_data['credits']['cast'][:5]:
                profile_path = actor.get('profile_path')
                if profile_path:
                    actor_images.append(f"[img]https://image.tmdb.org/t/p/w185{profile_path}[/img]")
            
            if actor_images:
                bbcode += ' '.join(actor_images) + '\n'
        
        # Rating
        if tmdb_data and tmdb_data.get('vote_average'):
            rating = tmdb_data.get('vote_average')
            vote_count = tmdb_data.get('vote_count', 0)
            rating_rounded = round(rating * 10)
            bbcode += f"[img]https://img.streetprez.com/note/{rating_rounded}.svg[/img] [i]{rating:.2f} ({vote_count})[/i] \n\n"
        
        # Links
        links = []
        if radarr_movie and radarr_movie.get('tmdbId'):
            links.append(f"[url=https://www.themoviedb.org/movie/{radarr_movie.get('tmdbId')}][img]https://i.imgur.com/mxI05s2.png[/img][/url]")
        
        if tmdb_data and tmdb_data.get('videos', {}).get('results'):
            youtube_key = next((v.get('key') for v in tmdb_data['videos']['results'] if v.get('site') == 'YouTube' and v.get('type') == 'Trailer'), None)
            if youtube_key:
                links.append(f"[url=https://www.youtube.com/watch?v={youtube_key}][img]https://i.imgur.com/jKQt520.png[/img][/url]")
        
        if links:
            bbcode += ' │ '.join(links) + '\n\n'
        
        # Separator
        bbcode += "[img]https://i.imgur.com/W3pvv6q.png[/img]\n\n"
        
        # ============ SYNOPSIS ============
        if radarr_movie and radarr_movie.get('overview'):
            bbcode += f"{radarr_movie.get('overview')}\n\n\n"
        
        # ============ TECHNICAL INFO ============
        bbcode += "[img]https://i.imgur.com/KMZsqZn.png[/img]\n"
        
        # Source
        quality_name = ''
        if radarr_movie:
            movie_file = radarr_movie.get('movieFile', {})
            quality = movie_file.get('quality', {}).get('quality', {})
            quality_name = quality.get('name', '')
        
        source = 'BluRay' if 'bluray' in quality_name.lower() else 'WEB' if 'web' in quality_name.lower() else 'Unknown'
        bbcode += f"[b][color=#3d85c6]Source :[/color][/b] [i]{source}[/i]\n"
        
        # Video quality
        resolution = video_track.get('Height', '')
        quality_str = f"{resolution}p" if resolution else 'N/A'
        bbcode += f"[b][color=#3d85c6]Qualité vidéo :[/color][/b] [i]{quality_str}/i[/i]\n"
        
        # Format
        container = general_track.get('Format', 'N/A')
        bbcode += f"[b][color=#3d85c6]Format vidéo :[/color][/b] [i]{container.upper()}[/i]\n"
        
        # Codec
        codec = video_track.get('Format', 'N/A')
        bbcode += f"[b][color=#3d85c6]Codec vidéo :[/color][/b] [i]{codec}[/i]\n"
        
        # Bitrate
        bitrate = video_track.get('BitRate', '')
        if bitrate:
            bitrate_kbps = int(bitrate) // 1000
            bbcode += f"[b][color=#3d85c6]Débit vidéo :[/color][/b] [i]{bitrate_kbps:,} Kbps\n[/i]\n\n"
        else:
            bbcode += "\n"
        
        # Audio tracks
        bbcode += "[b][color=#3d85c6] Audio(s) :[/color][/b]\n"
        for audio in audio_tracks:
            lang = audio.get('Language', 'Unknown')
            flag = get_country_flag(lang)
            lang_name = audio.get('Language_String', lang).capitalize()
            channels = audio.get('Channels', '')
            channel_str = f"[{channels}.1]" if channels else "[Stéréo]"
            format_audio = audio.get('Format', 'Unknown')
            codec_id = audio.get('CodecID', '')
            
            # Determine audio format name
            if 'AC-3' in codec_id or 'AC3' in format_audio.upper():
                format_name = 'Dolby Digital / AC3'
            elif 'AAC' in format_audio.upper():
                format_name = 'AAC'
            elif 'DTS' in format_audio.upper():
                format_name = 'DTS'
            else:
                format_name = format_audio
            
            bitrate_audio = audio.get('BitRate', '')
            if bitrate_audio:
                bitrate_kbps = int(bitrate_audio) // 1000
                bbcode += f" {flag} {lang_name} {channel_str} {format_name} @ {bitrate_kbps} kb/s\n"
            else:
                bbcode += f" {flag} {lang_name} {channel_str} {format_name}\n"
        
        bbcode += "\n"
        
        # Subtitles
        if text_tracks:
            bbcode += "[b][color=#3d85c6]Sous-titres :[/color][/b]\n"
            for sub in text_tracks:
                lang = sub.get('Language', 'Unknown')
                flag = get_country_flag(lang)
                lang_name = sub.get('Language_String', lang).capitalize()
                format_sub = sub.get('Format', 'Unknown')
                bbcode += f" {flag} {lang_name} : {format_sub.upper()} (complets)\n"
            bbcode += "\n"
        
        # ============ RELEASE INFO ============
        bbcode += "[img]https://i.imgur.com/KFsABlN.png[/img]\n"
        bbcode += f"[b][color=#3d85c6]Release :[/color][/b] [i]{release_name or video_file.stem}[/i]\n"
        
        # File size
        file_size = video_file.stat().st_size
        size_gb = file_size / (1024**3)
        bbcode += f"[b][color=#3d85c6]Taille totale :[/color][/b] {size_gb:.1f} GB\n"
        bbcode += f"[b][color=#3d85c6]Nombre de fichier :[/color][/b] 1[/size][/font][/center]\n\n"
        
        # Footer
        bbcode += "[right][sub]Propulsé par [i]FicheGen[/i][/sub][/right]"
        
        return bbcode
        
    except Exception as e:
        logger.error(f"Error generating BBCode: {e}")
        logger.exception(e)
        return None


def save_bbcode_file(bbcode_content, output_path):
    """Save BBCode content to text file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(bbcode_content)
        
        logger.info(f"BBCode file created: {output_path}")
        return {
            'success': True,
            'path': output_path,
            'message': 'BBCode file created successfully'
        }
    except Exception as e:
        logger.error(f"Error saving BBCode file: {e}")
        return {
            'success': False,
            'error': str(e)
        }
