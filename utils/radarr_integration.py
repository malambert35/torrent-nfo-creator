"""
Client Radarr — récupération du nom original via l'historique d'import.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

RADARR_URL    = os.getenv("RADARR_URL", "").rstrip("/")
RADARR_APIKEY = os.getenv("RADARR_APIKEY", "")


def get_radarr_movie_by_path(video_path: str) -> Optional[dict]:
    """
    Trouve le film Radarr correspondant à un chemin de fichier.
    Retourne le dict du movie Radarr ou None.
    """
    if not RADARR_URL or not RADARR_APIKEY:
        logger.warning("Radarr URL ou API Key non configuré")
        return None
    
    try:
        headers = {"X-Api-Key": RADARR_APIKEY}
        response = httpx.get(
            f"{RADARR_URL}/api/v3/movie",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        movies = response.json()
        
        # Normaliser le chemin recherché
        video_path_resolved = str(Path(video_path).resolve())
        
        for movie in movies:
            if not movie.get("hasFile"):
                continue
            
            # Récupérer le movieFile
            movie_file = movie.get("movieFile")
            if not movie_file:
                continue
            
            radarr_file_path = movie_file.get("path", "")
            if not radarr_file_path:
                continue
            
            radarr_file_resolved = str(Path(radarr_file_path).resolve())
            
            # Match exact sur le fichier
            if radarr_file_resolved == video_path_resolved:
                logger.info(f"✅ Film Radarr trouvé: {movie.get('title')} ({movie.get('year')})")
                return movie
            
            # Match sur le dossier parent (cas où source_path est un dossier)
            if Path(video_path_resolved).is_dir():
                if Path(radarr_file_resolved).parent == Path(video_path_resolved):
                    logger.info(f"✅ Film Radarr trouvé (dossier): {movie.get('title')} ({movie.get('year')})")
                    return movie
        
        logger.info(f"Aucun film Radarr trouvé pour: {video_path}")
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche Radarr: {e}")
        return None


def get_radarr_source_title(movie_id: int) -> Optional[str]:
    """
    Récupère le sourceTitle du dernier event d'historique pour un film.
    Retourne le sourceTitle (str) ou None.
    """
    if not RADARR_URL or not RADARR_APIKEY:
        return None
    
    try:
        headers = {"X-Api-Key": RADARR_APIKEY}
        response = httpx.get(
            f"{RADARR_URL}/api/v3/history/movie",
            headers=headers,
            params={"movieId": movie_id},
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
            if event.get("eventType") in ["grabbed", "downloadFolderImported"]
        ]
        
        if not relevant_events:
            logger.info(f"Aucun event de download trouvé pour movieId={movie_id}")
            return None
        
        # Trier par date (plus récent en premier)
        relevant_events.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Prendre le sourceTitle du plus récent
        source_title = relevant_events[0].get("sourceTitle", "").strip()
        
        if source_title:
            logger.info(f"✅ Source title Radarr: {source_title}")
            return source_title
        else:
            logger.info(f"sourceTitle vide pour movieId={movie_id}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du sourceTitle: {e}")
        return None


def generate_radarr_name(movie: dict) -> str:
    """
    Génère un nom de fichier formaté à partir des métadonnées Radarr.
    Format: Title (Year) [Quality] [Edition]
    """
    title = movie.get("title", "Unknown")
    year = movie.get("year", "")
    
    # Quality
    quality_str = ""
    movie_file = movie.get("movieFile", {})
    if movie_file:
        quality = movie_file.get("quality", {}).get("quality", {})
        quality_name = quality.get("name", "")
        if quality_name:
            quality_str = f"[{quality_name}]"
    
    # Edition
    edition_str = ""
    if movie_file:
        edition = movie_file.get("edition", "").strip()
        if edition:
            edition_str = f"[{edition}]"
    
    # Assembler
    parts = [f"{title} ({year})" if year else title]
    if quality_str:
        parts.append(quality_str)
    if edition_str:
        parts.append(edition_str)
    
    return " ".join(parts)


def get_release_name(source_path: str) -> Optional[str]:
    """
    Retourne un nom de release pour le fichier/dossier vidéo:
    1. Essaie d'abord le sourceTitle de l'historique Radarr (nom original)
    2. Sinon: génère un nom à partir des métadonnées Radarr
    3. Fallback: None (le caller utilisera le nom du fichier/dossier)
    
    Args:
        source_path: Chemin du fichier .mkv ou du dossier contenant le film
    
    Returns:
        Nom de release original ou généré, ou None si Radarr non disponible
    """
    movie = get_radarr_movie_by_path(source_path)
    
    if not movie:
        logger.info(f"Film non trouvé dans Radarr pour: {source_path}")
        return None
    
    # Priorité 1: sourceTitle de l'historique (nom original avant renommage)
    movie_id = movie.get("id")
    if movie_id:
        source_title = get_radarr_source_title(movie_id)
        if source_title:
            # Le sourceTitle ne contient généralement pas l'extension
            return source_title
    
    # Priorité 2: Générer à partir des métadonnées Radarr
    logger.info("sourceTitle non trouvé, génération depuis métadonnées Radarr")
    generated = generate_radarr_name(movie)
    return generated
```

---

## Différences clés par rapport à l'ancienne version :

1. **Matching fichier amélioré** : 
   - Compare les chemins résolus (`resolve()`) pour gérer les symlinks
   - Gère le cas où `source_path` est un dossier (match sur le parent du fichier Radarr)

2. **Récupération du sourceTitle** :
   - Filtre les events `grabbed` et `downloadFolderImported` (pas seulement `downloadFolderImported`)
   - Tri par date pour prendre le plus récent

3. **Fallback intelligent** :
   - Si sourceTitle vide → génère depuis métadonnées Radarr (Title, Year, Quality, Edition)
   - Si pas de film Radarr → retourne `None` (le caller utilisera le nom du dossier)

---

## Test avec ton exemple

**Fichier actuel (renommé par Radarr) :**
```
/mnt/source/Basic Instinct (1992)/Basic Instinct (1992) Bluray-2160p.mkv
```

**Historique Radarr (sourceTitle) :**
```
Basic Instinct (1992) Unrated Directors Cut MULTi VFI 2160p 10bit 4KLight DV HDR BluRay DDP 5.1 x265-QTZ
```

**Résultat `get_release_name()` :**
```
Basic Instinct (1992) Unrated Directors Cut MULTi VFI 2160p 10bit 4KLight DV HDR BluRay DDP 5.1 x265-QTZ
```

**Hardlink créé :**
```
/mnt/hardlinks/Basic Instinct (1992) Unrated Directors Cut MULTi VFI 2160p 10bit 4KLight DV HDR BluRay DDP 5.1 x265-QTZ.mkv
