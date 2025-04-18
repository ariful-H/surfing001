import time
from database import db

# In-memory storage for movie favorites and history
movie_favorites = {}
movie_history = {}

class MovieFavorite:
    @staticmethod
    def add_favorite(user_id, video_id, video_data):
        """
        Add a movie to user's favorites
        
        Args:
            user_id (str): The user ID
            video_id (str): The YouTube video ID
            video_data (dict): Video metadata including title, thumbnail, etc.
            
        Returns:
            bool: True if successful
        """
        if user_id not in movie_favorites:
            movie_favorites[user_id] = {}
            
        # Store the favorite with timestamp
        movie_favorites[user_id][video_id] = {
            'video_id': video_id,
            'data': video_data,
            'added_at': time.time()
        }
        
        return True
    
    @staticmethod
    def remove_favorite(user_id, video_id):
        """
        Remove a movie from user's favorites
        
        Args:
            user_id (str): The user ID
            video_id (str): The YouTube video ID
            
        Returns:
            bool: True if successful, False if not found
        """
        if user_id in movie_favorites and video_id in movie_favorites[user_id]:
            del movie_favorites[user_id][video_id]
            return True
        return False
    
    @staticmethod
    def get_user_favorites(user_id):
        """
        Get all favorites for a user
        
        Args:
            user_id (str): The user ID
            
        Returns:
            list: List of favorite videos
        """
        if user_id not in movie_favorites:
            return []
            
        # Convert to list and sort by most recently added
        favorites = list(movie_favorites[user_id].values())
        favorites.sort(key=lambda x: x['added_at'], reverse=True)
        
        return favorites
    
    @staticmethod
    def is_favorite(user_id, video_id):
        """
        Check if a video is in user's favorites
        
        Args:
            user_id (str): The user ID
            video_id (str): The YouTube video ID
            
        Returns:
            bool: True if video is a favorite
        """
        return user_id in movie_favorites and video_id in movie_favorites[user_id]

class MovieHistory:
    @staticmethod
    def add_to_history(user_id, video_id, video_data):
        """
        Add a movie to user's watch history
        
        Args:
            user_id (str): The user ID
            video_id (str): The YouTube video ID
            video_data (dict): Video metadata
            
        Returns:
            bool: True if successful
        """
        if user_id not in movie_history:
            movie_history[user_id] = {}
            
        # Store or update the history entry with new timestamp
        movie_history[user_id][video_id] = {
            'video_id': video_id,
            'data': video_data,
            'last_watched': time.time()
        }
        
        return True
    
    @staticmethod
    def get_user_history(user_id, limit=20):
        """
        Get user's watch history
        
        Args:
            user_id (str): The user ID
            limit (int): Maximum number of history items to return
            
        Returns:
            list: List of watched videos, sorted by most recent
        """
        if user_id not in movie_history:
            return []
            
        # Convert to list and sort by most recently watched
        history = list(movie_history[user_id].values())
        history.sort(key=lambda x: x['last_watched'], reverse=True)
        
        # Return only the requested number of items
        return history[:limit]