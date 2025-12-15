import json
import os
import logging
from typing import Set, List

from config import Config

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages user authentication and persistence of authorized users."""
    
    def __init__(self):
        self.file_path = Config.ALLOWED_USERS_FILE
        self.password = Config.BOT_ACCESS_PASSWORD
        self.allowed_users: Set[int] = set()
        self._load_users()
        
    def _load_users(self):
        """Load authorized users from file."""
        if not os.path.exists(self.file_path):
            return
            
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.allowed_users = set(data.get('users', []))
            logger.info(f"Loaded {len(self.allowed_users)} authorized users.")
        except Exception as e:
            logger.error(f"Error loading authorized users: {e}")
            
    def _save_users(self):
        """Save authorized users to file."""
        try:
            data = {'users': list(self.allowed_users)}
            with open(self.file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving authorized users: {e}")

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled (password is set)."""
        return bool(self.password)

    def is_authorized(self, user_id: int) -> bool:
        """Check if a user is authorized."""
        if not self.is_auth_enabled():
            return True
        return user_id in self.allowed_users

    def authorize(self, user_id: int, password: str) -> bool:
        """Attempt to authorize a user with a password."""
        if not self.is_auth_enabled():
            return True
            
        if password == self.password:
            self.allowed_users.add(user_id)
            self._save_users()
            logger.info(f"User {user_id} authorized successfully.")
            return True
        
        logger.warning(f"Failed authorization attempt for user {user_id}.")
        return False
