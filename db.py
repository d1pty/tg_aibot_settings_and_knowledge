# db.py
import aiosqlite

from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                settings TEXT,
                knowledge TEXT,
                admin_thread_id INTEGER,
                last_reset DATETIME,
                bot_enabled INTEGER DEFAULT 1
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def save_user(user_id: int, settings: str = None, knowledge: str = None,
                    admin_thread_id: int = None, last_reset: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        if row:
            if settings is not None:
                if last_reset is not None:
                    await db.execute(
                        "UPDATE users SET settings = ?, last_reset = ? WHERE user_id = ?",
                        (settings, last_reset, user_id)
                    )
                else:
                    await db.execute("UPDATE users SET settings = ? WHERE user_id = ?", (settings, user_id))
            if knowledge is not None:
                await db.execute("UPDATE users SET knowledge = ? WHERE user_id = ?", (knowledge, user_id))
            if admin_thread_id is not None:
                await db.execute("UPDATE users SET admin_thread_id = ? WHERE user_id = ?", (admin_thread_id, user_id))
        else:
            await db.execute(
                "INSERT INTO users (user_id, settings, knowledge, admin_thread_id, last_reset) VALUES (?, ?, ?, ?, ?)",
                (user_id, settings, knowledge, admin_thread_id, last_reset)
            )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT settings, knowledge, admin_thread_id, last_reset, bot_enabled FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "settings": row[0],
                    "knowledge": row[1],
                    "admin_thread_id": row[2],
                    "last_reset": row[3],
                    "bot_enabled": row[4]
                }
            else:
                return None

async def save_history_message(user_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()

async def get_history(user_id: int, last_reset: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if last_reset:
            query = "SELECT role, content FROM history WHERE user_id = ? AND timestamp >= ? ORDER BY id"
            async with db.execute(query, (user_id, last_reset)) as cursor:
                rows = await cursor.fetchall()
        else:
            query = "SELECT role, content FROM history WHERE user_id = ? ORDER BY id"
            async with db.execute(query, (user_id,)) as cursor:
                rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]

async def set_bot_enabled(user_id: int, enabled: bool):
    """Устанавливает для пользователя состояние бота: включён (True) или отключён (False)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET bot_enabled = ? WHERE user_id = ?",
            (1 if enabled else 0, user_id)
        )
        await db.commit()

async def get_user_by_thread(admin_thread_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, settings, knowledge, admin_thread_id, last_reset, bot_enabled FROM users WHERE admin_thread_id = ?",
            (admin_thread_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "settings": row[1],
                    "knowledge": row[2],
                    "admin_thread_id": row[3],
                    "last_reset": row[4],
                    "bot_enabled": row[5]
                }
            else:
                return None
