import requests
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RADARR_URL = os.getenv('RADARR_URL', '').rstrip('/')
RADARR_API_KEY = os.getenv('RADARR_API_KEY', '')

def get_radarr_movie_by_path(video_path):
    """
    Trouve le film Radarr correspondant à un chemin de fichier.
    Retourne le dict du movie Radarr ou None.
    """
    if not RADARR_URL or not RADARR_API_KEY:
        logger.warning("Radarr URL ou API Key non configuré")
        return None
    
    try:
        headers = {'X-Api-Key': RADARR_API_KEY}
        response = requests.get(f"{RADARR_URL}/api/v3/movie", headers=headers, timeout=10)
        response.raise_for_status()
        movies = response.json()
        
        # Normaliser le chemin recherché
        video_path_resolved = str(Path(video_path).resolve())
        
        for movie in movies:
            if not movie.get('hasFile'):
                continue
            
            # Récupérer le movieFile
            movie_file = movie.get('movieFile')
            if not movie_file:
                continue
            
            radarr_file_path = movie_file.get('path', '')
            if not radarr_file_path:
                continue
            
            radarr_file_resolved = str(Path(radarr_file_path).resolve())
            
            if radarr_file_resolved == video_path_resolved:
                return movie
        
        logger.info(f"Aucun film Radarr trouvé pour: {video_path}")
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche Radarr: {e}")
        return None


def get_radarr_source_title(movie_id):
    """
    Récupère le sourceTitle du dernier event d'historique pour un film.
    Retourne le sourceTitle (str) ou None.
    """
    if not RADARR_URL or not RADARR_API_KEY:
        return None
    
    try:
        headers = {'X-Api-Key': RADARR_API_KEY}
        response = requests.get(
            f"{RADARR_URL}/api/v3/history/movie",
            headers=headers,
            params={'movieId': movie_id},
            timeout=10
        )
        response.raise_for_status()
        history = response.json()
        
        if not history:
            logger.info(f"Aucun historique trouvé pour movieId={movie_id}")
            return None
        
        # Filtrer les events pertinents (grabbed, downloadFolderImported)
        relevant_events = [
            event for event in history
            if event.get('eventType') in ['grabbed', 'downloadFolderImported']
        ]
        
        if not relevant_events:
            logger.info(f"Aucun event de download trouvé pour movieId={movie_id}")
            return None
        
        # Trier par date (plus récent en premier)
        relevant_events.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Prendre le sourceTitle du plus récent
        source_title = relevant_events[0].get('sourceTitle', '').strip()
        
        if source_title:
            logger.info(f"Source title trouvé: {source_title}")
            return source_title
        else:
            logger.info(f"sourceTitle vide pour movieId={movie_id}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du sourceTitle: {e}")
        return None


def generate_radarr_name(movie):
    """
    Génère un nom de fichier formaté à partir des métadonnées Radarr.
    Format: Title (Year) [Quality] [Edition]
    """
    title = movie.get('title', 'Unknown')
    year = movie.get('year', '')
    
    # Quality
    quality_str = ''
    movie_file = movie.get('movieFile', {})
    if movie_file:
        quality = movie_file.get('quality', {}).get('quality', {})
        quality_name = quality.get('name', '')
        if quality_name:
            quality_str = f"[{quality_name}]"
    
    # Edition
    edition_str = ''
    if movie_file:
        edition = movie_file.get('edition', '').strip()
        if edition:
            edition_str = f"[{edition}]"
    
    # Assembler
    parts = [f"{title} ({year})" if year else title]
    if quality_str:
        parts.append(quality_str)
    if edition_str:
        parts.append(edition_str)
    
    return ' '.join(parts)


def get_radarr_generated_name(video_path, use_source_title=True):
    """
    Retourne un nom de release pour le fichier vidéo:
    1. Si use_source_title=True: essaie d'abord le sourceTitle de l'historique
    2. Sinon: génère un nom à partir des métadonnées Radarr
    3. Fallback: nom du fichier actuel
    
    Retourne aussi le movie dict pour utilisation ultérieure.
    """
    movie = get_radarr_movie_by_path(video_path)
    
    if not movie:
        # Fallback: nom du fichier sans extension
        return Path(video_path).stem, None
    
    # Essayer le sourceTitle en priorité
    if use_source_title:
        movie_id = movie.get('id')
        if movie_id:
            source_title = get_radarr_source_title(movie_id)
            if source_title:
                # Retourner le sourceTitle tel quel (il ne contient pas d'extension fichier)
                return source_title, movie
    
    # Sinon: générer à partir des métadonnées
    generated = generate_radarr_name(movie)
    return generated, movie

