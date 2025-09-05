"""
Database module for storing conversation history and user data.
Uses SQLite for local storage with async support.
"""
import asyncio
import logging
import sqlite3
import aiosqlite
import time
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from config.settings import DATABASE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ConversationRecord:
    """Database record for conversation messages."""
    id: Optional[int] = None
    timestamp: float = 0.0
    user_message: str = ""
    assistant_response: str = ""
    screen_context: str = ""
    metadata: str = "{}"  # JSON string
    session_id: Optional[str] = None


@dataclass
class ScreenContextRecord:
    """Database record for screen context snapshots."""
    id: Optional[int] = None
    timestamp: float = 0.0
    content: str = ""
    confidence: float = 0.0
    image_hash: str = ""
    metadata: str = "{}"  # JSON string


class DatabaseManager:
    """
    Manages SQLite database operations for the SAGE assistant.
    """
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG["path"]
        self.max_history = DATABASE_CONFIG["max_history"]
        self.cleanup_interval = DATABASE_CONFIG["cleanup_interval"]
        self.last_cleanup = time.time()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self):
        """Initialize database tables if they don't exist."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Conversations table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        user_message TEXT NOT NULL,
                        assistant_response TEXT NOT NULL,
                        screen_context TEXT DEFAULT '',
                        metadata TEXT DEFAULT '{}',
                        session_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Screen context table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS screen_contexts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        content TEXT NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        image_hash TEXT DEFAULT '',
                        metadata TEXT DEFAULT '{}',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # User preferences table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                    ON conversations(timestamp)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_screen_contexts_timestamp 
                    ON screen_contexts(timestamp)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_session 
                    ON conversations(session_id)
                """)
                
                await db.commit()
                
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def save_conversation(
        self,
        user_message: str,
        assistant_response: str,
        screen_context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Save conversation to database.
        
        Args:
            user_message: User's input message
            assistant_response: Assistant's response
            screen_context: Current screen context
            metadata: Additional metadata as dict
            session_id: Session identifier
            
        Returns:
            ID of the inserted record
        """
        try:
            metadata_json = json.dumps(metadata or {})
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO conversations 
                    (timestamp, user_message, assistant_response, screen_context, metadata, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    user_message,
                    assistant_response,
                    screen_context,
                    metadata_json,
                    session_id
                ))
                
                await db.commit()
                record_id = cursor.lastrowid
                
            logger.debug(f"Saved conversation record with ID: {record_id}")
            
            # Perform cleanup if needed
            await self._cleanup_if_needed()
            
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            raise
    
    async def save_screen_context(
        self,
        content: str,
        confidence: float = 0.0,
        image_hash: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save screen context to database.
        
        Args:
            content: Screen text content
            confidence: OCR confidence score
            image_hash: Hash of the screen image
            metadata: Additional metadata
            
        Returns:
            ID of the inserted record
        """
        try:
            metadata_json = json.dumps(metadata or {})
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO screen_contexts 
                    (timestamp, content, confidence, image_hash, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    content,
                    confidence,
                    image_hash,
                    metadata_json
                ))
                
                await db.commit()
                record_id = cursor.lastrowid
                
            logger.debug(f"Saved screen context record with ID: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to save screen context: {e}")
            raise
    
    async def get_recent_conversations(
        self,
        limit: int = 50,
        session_id: Optional[str] = None
    ) -> List[ConversationRecord]:
        """
        Get recent conversation records.
        
        Args:
            limit: Maximum number of records to return
            session_id: Filter by session ID if provided
            
        Returns:
            List of ConversationRecord objects
        """
        try:
            query = """
                SELECT id, timestamp, user_message, assistant_response, 
                       screen_context, metadata, session_id
                FROM conversations
            """
            params = []
            
            if session_id:
                query += " WHERE session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
            
            records = []
            for row in rows:
                record = ConversationRecord(
                    id=row[0],
                    timestamp=row[1],
                    user_message=row[2],
                    assistant_response=row[3],
                    screen_context=row[4],
                    metadata=row[5],
                    session_id=row[6]
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    async def get_recent_screen_contexts(self, limit: int = 10) -> List[ScreenContextRecord]:
        """
        Get recent screen context records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of ScreenContextRecord objects
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT id, timestamp, content, confidence, image_hash, metadata
                    FROM screen_contexts
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()
            
            records = []
            for row in rows:
                record = ScreenContextRecord(
                    id=row[0],
                    timestamp=row[1],
                    content=row[2],
                    confidence=row[3],
                    image_hash=row[4],
                    metadata=row[5]
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get recent screen contexts: {e}")
            return []
    
    async def search_conversations(
        self,
        query: str,
        limit: int = 20
    ) -> List[ConversationRecord]:
        """
        Search conversations by text content.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching ConversationRecord objects
        """
        try:
            search_query = f"%{query}%"
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT id, timestamp, user_message, assistant_response, 
                           screen_context, metadata, session_id
                    FROM conversations
                    WHERE user_message LIKE ? OR assistant_response LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (search_query, search_query, limit)) as cursor:
                    rows = await cursor.fetchall()
            
            records = []
            for row in rows:
                record = ConversationRecord(
                    id=row[0],
                    timestamp=row[1],
                    user_message=row[2],
                    assistant_response=row[3],
                    screen_context=row[4],
                    metadata=row[5],
                    session_id=row[6]
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    async def set_user_preference(self, key: str, value: Any):
        """Set a user preference."""
        try:
            value_str = json.dumps(value) if not isinstance(value, str) else value
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value_str))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to set user preference: {e}")
    
    async def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT value FROM user_preferences WHERE key = ?
                """, (key,)) as cursor:
                    row = await cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return row[0]  # Return as string if not JSON
            
            return default
            
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
            return default
    
    async def _cleanup_if_needed(self):
        """Perform database cleanup if needed."""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Clean up old conversations
                await db.execute("""
                    DELETE FROM conversations 
                    WHERE id NOT IN (
                        SELECT id FROM conversations 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    )
                """, (self.max_history,))
                
                # Clean up old screen contexts (keep more for analysis)
                await db.execute("""
                    DELETE FROM screen_contexts 
                    WHERE id NOT IN (
                        SELECT id FROM screen_contexts 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    )
                """, (self.max_history * 2,))
                
                await db.commit()
                
            self.last_cleanup = current_time
            logger.debug("Database cleanup completed")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Count conversations
                async with db.execute("SELECT COUNT(*) FROM conversations") as cursor:
                    conversation_count = (await cursor.fetchone())[0]
                
                # Count screen contexts
                async with db.execute("SELECT COUNT(*) FROM screen_contexts") as cursor:
                    context_count = (await cursor.fetchone())[0]
                
                # Get database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "conversation_count": conversation_count,
                    "screen_context_count": context_count,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "last_cleanup": self.last_cleanup
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# Singleton instance
_database_manager_instance: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _database_manager_instance
    if _database_manager_instance is None:
        _database_manager_instance = DatabaseManager()
    return _database_manager_instance
