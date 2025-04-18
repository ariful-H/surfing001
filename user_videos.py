import time
from database import users

class UserVideo:
    """
    Class to handle user video preferences, favorites, and history
    """
    
    @staticmethod
    def add_favorite(user_id, video_data):
        """
        Add a video to user's favorites
        
        Args:
            user_id (str): The user ID
            video_data (dict): Video data including id, title, thumbnail
            
        Returns:
            bool: Success status
        """
        if user_id not in users:
            return False
            
        # Initialize favorites list if it doesn't exist
        if 'favorites' not in users[user_id]:
            users[user_id]['favorites'] = []
            
        # Check if video is already in favorites
        for favorite in users[user_id]['favorites']:
            if favorite['id'] == video_data['id']:
                return True
                
        # Add to favorites with timestamp
        users[user_id]['favorites'].append({
            'id': video_data['id'],
            'title': video_data['title'],
            'thumbnail': video_data['thumbnail'],
            'added_at': time.time()
        })
        
        return True
    
    @staticmethod
    def remove_favorite(user_id, video_id):
        """
        Remove a video from user's favorites
        
        Args:
            user_id (str): The user ID
            video_id (str): The video ID to remove
            
        Returns:
            bool: Success status
        """
        if user_id not in users or 'favorites' not in users[user_id]:
            return False
            
        # Find and remove the video
        for i, favorite in enumerate(users[user_id]['favorites']):
            if favorite['id'] == video_id:
                users[user_id]['favorites'].pop(i)
                return True
                
        return False
    
    @staticmethod
    def get_favorites(user_id):
        """
        Get all favorite videos for a user
        
        Args:
            user_id (str): The user ID
            
        Returns:
            list: List of favorite videos
        """
        if user_id not in users or 'favorites' not in users[user_id]:
            return []
            
        return users[user_id]['favorites']
    
    @staticmethod
    def add_to_history(user_id, video_data):
        """
        Add a video to user's watch history
        
        Args:
            user_id (str): The user ID
            video_data (dict): Video data including id, title, thumbnail
            
        Returns:
            bool: Success status
        """
        if user_id not in users:
            return False
            
        # Initialize history list if it doesn't exist
        if 'history' not in users[user_id]:
            users[user_id]['history'] = []
            
        # Remove if already in history (to add it to the top)
        for i, item in enumerate(users[user_id]['history']):
            if item['id'] == video_data['id']:
                users[user_id]['history'].pop(i)
                break
                
        # Add to history with timestamp
        users[user_id]['history'].insert(0, {
            'id': video_data['id'],
            'title': video_data['title'],
            'thumbnail': video_data['thumbnail'],
            'watched_at': time.time()
        })
        
        # Limit history to 50 items
        if len(users[user_id]['history']) > 50:
            users[user_id]['history'] = users[user_id]['history'][:50]
        
        return True
    
    @staticmethod
    def get_history(user_id):
        """
        Get watch history for a user
        
        Args:
            user_id (str): The user ID
            
        Returns:
            list: List of watched videos
        """
        if user_id not in users or 'history' not in users[user_id]:
            return []
            
        return users[user_id]['history']