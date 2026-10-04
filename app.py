from fastapi import FastAPI

# Importing the controllers imports all four model modules, which registers every
# table on Base before create_all runs and lets relationship("Category") etc. resolve.
from category.controller import router as category_router
from checklist.controller import router as checklist_router
from database import Base, engine
from file.controller import router as file_router
from item.controller import router as item_router

Base.metadata.create_all(engine)

app = FastAPI(title="Checklist API")
app.include_router(checklist_router)
app.include_router(category_router)
app.include_router(item_router)
app.include_router(file_router)
