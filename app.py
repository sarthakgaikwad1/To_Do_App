from fastapi import FastAPI, HTTPException
from asyncpg import create_pool, Pool
from models import ToDoItem, ToDoResponse

app = FastAPI()

# PostgreSQL connection details
POSTGRES_URL = "postgresql://postgres:1234@localhost:5432/todo"

# Database connection pool
db_pool: Pool = None


@app.on_event("startup")
async def startup_event():
    """Initialize the database connection and add predefined tasks."""
    global db_pool
    try:
        db_pool = await create_pool(dsn=POSTGRES_URL)
        async with db_pool.acquire() as conn:
            # Create the todos table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)
            # Add predefined tasks if the table is empty
            existing_tasks = await conn.fetch("SELECT * FROM todos")
            if not existing_tasks:
                predefined_tasks = [
                    {"title": "Reading", "description": "Read 'FastAPI Documentation'", "completed": False},
                    {"title": "Workout", "description": "Perform a 30-minute workout session", "completed": False},
                    {"title": "Coding", "description": "Build a FastAPI app for CRUD operations", "completed": False},
                ]
                await conn.executemany("""
                    INSERT INTO todos (title, description, completed)
                    VALUES ($1, $2, $3)
                """, [(task["title"], task["description"], task["completed"]) for task in predefined_tasks])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database startup failed: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close the database connection pool."""
    if db_pool:
        await db_pool.close()


@app.get("/")
async def root():
    """Welcome message for the API."""
    return {"message": "Welcome to the To-Do API!"}


@app.post("/todos/", response_model=ToDoResponse)
async def create_todo(todo: ToDoItem):
    """Create a new To-Do item."""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO todos (title, description, completed)
                VALUES ($1, $2, $3)
                RETURNING id, title, description, completed
            """, todo.title, todo.description, todo.completed)
            if result:
                return ToDoResponse(**dict(result))
            raise HTTPException(status_code=500, detail="Failed to create the To-Do item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/todos/", response_model=list[ToDoResponse])
async def list_todos():
    """List all To-Do items."""
    try:
        async with db_pool.acquire() as conn:
            todos = await conn.fetch("""
                SELECT id, title, description, completed
                FROM todos
            """)
            return [ToDoResponse(**dict(todo)) for todo in todos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/todos/{id}/", response_model=ToDoResponse)
async def get_todo_by_id(id: int):
    """Retrieve a To-Do item by its ID."""
    try:
        async with db_pool.acquire() as conn:
            todo = await conn.fetchrow("""
                SELECT id, title, description, completed
                FROM todos
                WHERE id = $1
            """, id)
            if todo:
                return ToDoResponse(**dict(todo))
            raise HTTPException(status_code=404, detail="To-Do item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.put("/todos/{id}/", response_model=ToDoResponse)
async def update_todo(id: int, todo: ToDoItem):
    """Update a To-Do item."""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                UPDATE todos
                SET title = $1, description = $2, completed = $3
                WHERE id = $4
                RETURNING id, title, description, completed
            """, todo.title, todo.description, todo.completed, id)
            if result:
                return ToDoResponse(**dict(result))
            raise HTTPException(status_code=404, detail="To-Do item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/todos/{id}/")
async def delete_todo(id: int):
    """Delete a To-Do item."""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM todos
                WHERE id = $1
            """, id)
            if result == "DELETE 1":
                return {"message": "To-Do item deleted successfully"}
            raise HTTPException(status_code=404, detail="To-Do item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
