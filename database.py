from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import jwt

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'quantumgaze'

# Initialize MongoDB client with error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Verify connection
    client.server_info()
    db = client[DB_NAME]
    print(f"Successfully connected to MongoDB at {MONGO_URI}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    print("Using fallback in-memory storage")
    # Fallback to in-memory storage
    class MockDB:
        def __init__(self):
            self.users = {}
            self.favorites = {}
            self.history = {}
        
        def __getitem__(self, key):
            if key not in self.__dict__:
                self.__dict__[key] = {}
            return self.__dict__[key]
    
    db = MockDB()
    client = None

class User:
    def __init__(self, email):
        self.email = email
        self.collection = db.users

    @staticmethod
    def create_user(email, password):
        try:
            # Check if user already exists
            if db.users.find_one({"email": email}):
                raise Exception("User already exists")

            # Create new user
            user_data = {
                "email": email,
                "password": generate_password_hash(password),
                "created_at": datetime.utcnow()
            }
            
            result = db.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")

    @staticmethod
    def verify_user(email, password):
        try:
            user = db.users.find_one({"email": email})
            if user and check_password_hash(user['password'], password):
                return str(user['_id'])
            return None
        except Exception as e:
            raise Exception(f"Error verifying user: {str(e)}")

    @staticmethod
    def get_by_id(user_id):
        try:
            from bson.objectid import ObjectId
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                return user
            return None
        except Exception as e:
            return None

    @staticmethod
    def get_by_email(email):
        try:
            user = db.users.find_one({"email": email})
            if user:
                return user
            return None
        except Exception as e:
            return None

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_EXPIRATION = timedelta(days=1)

def create_token(user_id):
    try:
        payload = {
            'exp': datetime.utcnow() + JWT_EXPIRATION,
            'iat': datetime.utcnow(),
            'sub': str(user_id)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    except Exception as e:
        raise Exception(f"Error creating token: {str(e)}")

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')