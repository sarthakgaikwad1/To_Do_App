from pydantic import BaseModel, Field
from typing import Optional


class ToDoItem(BaseModel):
    """Model for creating and updating To-Do items."""
    title: str = Field(..., example="Read Books")
    description: Optional[str] = Field(None, example="Read FastAPI docs")
    completed: bool = Field(default=False, example=False)


class ToDoResponse(ToDoItem):
    """Response model for returning To-Do items with an ID."""
    id: int = Field(..., example=1)

