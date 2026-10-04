## Stack

- **FastAPI** for the web framework, with `python-multipart` for file uploads.
- **SQLAlchemy** (2.0 declarative style) for the ORM.
- **SQLite** for storage. File contents are stored as blobs in the database.

Why FastAPI over Flask:
- **Uploads:** an `UploadFile` parameter gives `.filename`, `.content_type` and `await file.read()`. The upload is held in a spooled temporary file, which stays in memory up to a threshold and then moves to disk. Flask's `request.files` / Werkzeug `FileStorage` is equivalent, so this is a tie.
- **Validation:** request bodies are declared as Pydantic models (`schema.py`), and FastAPI validates them and returns a `422` with details when they're wrong. Flask needs an extension for this.
- **PATCH:** FastAPI's documented pattern for partial updates is `body.model_dump(exclude_unset=True)`, which returns only the fields the client actually sent.
- **Session per request:** FastAPI's SQL tutorial uses a `yield` dependency (`Depends(get_session)`) to open one session per request and close it afterwards. That's exactly the pattern in the Architecture section below.
- **Docs:** interactive API docs are generated automatically at `/docs`.

SQLite note: the engine is created with `connect_args={"check_same_thread": False}`. FastAPI's docs explain that one request can use more than one thread, and SQLite refuses that by default.

## Architecture

Four files per resource:

- **Model** (`model.py`): SQLAlchemy declarative classes. Holds the row's data plus domain behaviour (`copy`, `add_file`). Model methods never touch the session; they only read their own attributes and build/modify objects.
- **DAO** (`dao.py`): the database operations. Every function takes a `session` as its first argument and **never commits**. It only queries, `add`s, `delete`s, and `flush`es (to get new ids).
- **Schema** (`schema.py`): Pydantic models for request bodies (`ChecklistCreate`, `ChecklistUpdate`) and responses (`ChecklistRead`). FastAPI uses them to validate input and to turn model objects into JSON.
- **Controller** (`controller.py`): FastAPI routes. Parses the request, calls the DAO and model methods, commits **once** per request, and returns results.

One session per request, provided by `get_session` in the root `database.py`. Because only the controller commits, every request is a single transaction: if anything fails, nothing is written.

The root `database.py` holds the shared setup (engine, session factory, `Base`, `get_session`), not DAO functions.

## API

```
GET     /checklists
POST    /checklists
GET     /checklists/{checklist_id}
PATCH   /checklists/{checklist_id}
DELETE  /checklists/{checklist_id}
POST    /checklists/{checklist_id}/copy

GET     /checklists/{checklist_id}/categories
POST    /checklists/{checklist_id}/categories
GET     /checklists/{checklist_id}/categories/{category_id}
PATCH   /checklists/{checklist_id}/categories/{category_id}
DELETE  /checklists/{checklist_id}/categories/{category_id}

GET     /checklists/{checklist_id}/categories/{category_id}/files
POST    /checklists/{checklist_id}/categories/{category_id}/files                  (multipart upload)
GET     /checklists/{checklist_id}/categories/{category_id}/files/{file_id}
PATCH   /checklists/{checklist_id}/categories/{category_id}/files/{file_id}
DELETE  /checklists/{checklist_id}/categories/{category_id}/files/{file_id}

GET     /checklists/{checklist_id}/categories/{category_id}/items
POST    /checklists/{checklist_id}/categories/{category_id}/items
GET     /checklists/{checklist_id}/categories/{category_id}/items/{item_id}
PATCH   /checklists/{checklist_id}/categories/{category_id}/items/{item_id}
DELETE  /checklists/{checklist_id}/categories/{category_id}/items/{item_id}

GET     /checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files
POST    /checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files  (multipart upload)
GET     /checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files/{file_id}
PATCH   /checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files/{file_id}
DELETE  /checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files/{file_id}
```

- **PATCH** updates only the fields sent in the body. Today the only editable field on every resource is `name`, so PATCH means "rename". The body schema has every field optional (`name: str | None = None`), and the controller applies `body.model_dump(exclude_unset=True)` to the object. A field that's left out stays unchanged. File contents can't be changed with PATCH; to replace a file, delete it and upload a new one.
- **Files:** `GET .../files` returns metadata only (id, name, size), never the bytes. `GET .../files/{file_id}` returns the file itself as a download, with `Content-Disposition: attachment; filename="..."`.

- **Copy** is an action sub-resource, `POST /checklists/{id}/copy`, which returns `201 Created` with the new checklist. Only checklists can be copied. `Category.copy`, `Item.copy` and `File.copy` exist only as steps inside the checklist copy and have no endpoints.
- **Uploading a file** is creating a file in a `files` collection, so it's a plain `POST` to `.../files` with `multipart/form-data`. FastAPI (via `python-multipart`) parses the upload into an `UploadFile` with `.filename` and the bytes; the controller passes those to the model.
- **Uploads are limited to 10 MB.** The controller reads at most 10 MB + 1 byte; if it got more than 10 MB, it responds `413 Payload Too Large` and nothing is saved. The limit is a constant `MAX_UPLOAD_BYTES = 10 * 1024 * 1024` in `file/model.py` next to `File`, so both upload controllers share it. This check runs after the upload has been received, so an oversized upload still uses bandwidth and temporary disk before it's rejected. Stopping it earlier would take a limit in the server or a reverse proxy in front of it, which isn't needed at this scale.
- **Nested ids are validated.** A lookup checks that the child really belongs to the parent in the URL, so `/checklists/1/categories/99` is a 404 if category 99 belongs to checklist 5.

## Models

Relationships are one-to-many throughout: each child table has a single foreign key to its parent. No link tables.

```
Checklist 1──* Category 1──* Item
                  │            │
                  1            1
                  *            *
                 File         File
```

Filename: `/checklist/model.py`
```python
class Checklist(Base):
    __tablename__ = "checklists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    categories: Mapped[list["Category"]] = relationship(
        back_populates="checklist", cascade="all, delete-orphan"
    )

    def copy(self) -> "Checklist":
        return Checklist(name=self.name, categories=[c.copy() for c in self.categories])
```

Filename: `/category/model.py`
```python
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"))
    name: Mapped[str]

    checklist: Mapped["Checklist"] = relationship(back_populates="categories")
    items: Mapped[list["Item"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    def copy(self) -> "Category":
        return Category(
            name=self.name,
            items=[i.copy() for i in self.items],
            files=[f.copy() for f in self.files],
        )

    def add_file(self, name: str, content: bytes) -> "File":
        file = File(name=name, content=content)
        self.files.append(file)
        return file
```

Filename: `/item/model.py`
```python
class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str]

    category: Mapped["Category"] = relationship(back_populates="items")
    files: Mapped[list["File"]] = relationship(back_populates="item", cascade="all, delete-orphan")

    def copy(self) -> "Item":
        return Item(name=self.name, files=[f.copy() for f in self.files])

    def add_file(self, name: str, content: bytes) -> "File":
        file = File(name=name, content=content)
        self.files.append(file)
        return file
```

Filename: `/file/model.py`
```python
class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        # a file belongs to exactly one parent: a category or an item
        CheckConstraint("(category_id IS NULL) != (item_id IS NULL)"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    name: Mapped[str]
    size: Mapped[int]
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)

    category: Mapped["Category | None"] = relationship(back_populates="files")
    item: Mapped["Item | None"] = relationship(back_populates="files")

    def __init__(self, name: str, content: bytes):
        super().__init__(name=name, content=content, size=len(content))

    def copy(self) -> "File":
        return File(name=self.name, content=self.content)
```

Notes:
- Relationships use string class names (`"Category"`) so the model files don't import each other. `app.py` imports all four model modules at startup so SQLAlchemy can resolve them.
- `cascade="all, delete-orphan"` means deleting a checklist deletes its categories, their items, and all their files.
- `content` needs no size: SQLite ignores column lengths. Upload size is capped in the controller instead.
- `content` is **deferred**: loading a `File` doesn't load its bytes until `file.content` is read. Listing files and returning a full checklist therefore never load blobs. `size` is stored as its own column so metadata can be shown without reading the bytes. The custom `__init__` sets `size` from the content; SQLAlchemy doesn't call `__init__` when loading rows, so this only runs for new files.

### How `copy` works

`copy()` is a **deep copy** built entirely in memory:

1. The controller loads the original with `get_checklist_contents` (below), so the whole checklist and everything under it is in memory.
2. `original.copy()` recursively builds new, unsaved objects. They have no ids and no foreign keys; they're linked only through the relationship lists.
3. `session.add(new)` adds the new checklist, and the cascade adds every object reachable from it.
4. `session.commit()` inserts parents before children. After each insert, SQLAlchemy copies the new id into the children's foreign keys. A file copied inside `Item.copy` gets `item_id`; one copied inside `Category.copy` gets `category_id`.

Rules for `copy()`:
- Copy data and children only. Never copy `id`, a foreign key, or the parent back-reference.
- Always build new children (`[c.copy() for c in ...]`). Passing the existing list (`categories=self.categories`) would **move** the original categories to the new checklist instead of copying them.

## DAO

All functions take `session` first and never commit. `create_*` functions take the parent id and return the created object.

Filename: `/checklist/dao.py`
```python
def create_checklist(session, name) -> Checklist
def list_checklists(session) -> list[Checklist]
def get_checklist(session, checklist_id) -> Checklist | None
def get_checklist_contents(session, checklist_id, *, include_file_content=False) -> Checklist | None
def delete_checklist(session, checklist: Checklist) -> None
```

`get_checklist_contents` loads the checklist **and everything under it** (categories, items, and files on both) using `selectinload`. That takes 5 queries no matter the size (checklist, categories, items, item files, category files), instead of one lazy-load query per category and per item. Used by copy, and by `GET /checklists/{id}`, which returns a full checklist. Copy passes `include_file_content=True` so the deferred file bytes are loaded in those same queries; the GET leaves them out.

Filename: `/category/dao.py`
```python
def create_category(session, checklist_id, name) -> Category
def list_categories(session, checklist_id) -> list[Category]
def get_category(session, checklist_id, category_id) -> Category | None
def delete_category(session, category: Category) -> None
```

Filename: `/item/dao.py`
```python
def create_item(session, category_id, name) -> Item
def list_items(session, category_id) -> list[Item]
def get_item(session, category_id, item_id) -> Item | None
def delete_item(session, item: Item) -> None
```

Filename: `/file/dao.py`
```python
def list_category_files(session, category_id) -> list[File]
def list_item_files(session, item_id) -> list[File]
def get_category_file(session, category_id, file_id) -> File | None
def get_item_file(session, item_id, file_id) -> File | None
def delete_file(session, file: File) -> None
```

Files are created through `Category.add_file` / `Item.add_file`, not the DAO.

`get_*` functions take the parent id so they can return `None` when the child exists but belongs to a different parent.

## Controllers

Each controller exposes the routes for its resource and has the same operations as its DAO, plus:

Filename: `/checklist/controller.py`
```python
@router.post("/checklists/{checklist_id}/copy", status_code=201)
def copy_checklist(checklist_id: int, session: Session = Depends(get_session)):
    original = dao.get_checklist_contents(session, checklist_id, include_file_content=True)
    if original is None:
        raise HTTPException(404)
    new = original.copy()
    session.add(new)
    session.commit()
    return new
```

Filename: `/file/controller.py`. All `.../files` routes live here, for both category and item files, so the upload routes are here too. The item version is the same with `item.add_file`.
```python
@router.post(CATEGORY_FILES, response_model=FileRead, status_code=201)
def upload_category_file(checklist_id: int, category_id: int, file: UploadFile, session: SessionDep):
    category = _get_category_or_404(session, checklist_id, category_id)
    name, content = _read_upload(file)   # reads at most 10 MB + 1 byte; raises 413 if over
    new_file = category.add_file(name, content)
    session.commit()
    return new_file
```

All routes are plain `def`, not `async def`. The SQLAlchemy session is synchronous, and FastAPI runs `def` routes in a thread pool so a blocking database call doesn't stall other requests. For the same reason, uploads are read with the synchronous `file.file.read(...)` rather than `await file.read(...)`.

PATCH, shown for checklists (the same shape for every resource):
```python
@router.patch("/checklists/{checklist_id}", response_model=ChecklistRead)
def update_checklist(checklist_id: int, body: ChecklistUpdate,
                     session: Session = Depends(get_session)):
    checklist = dao.get_checklist(session, checklist_id)
    if checklist is None:
        raise HTTPException(404)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(checklist, field, value)
    session.commit()
    return checklist
```

PATCH needs no DAO function: changing an attribute on a loaded object is the update, and the commit writes it.

## File Structure
```
check-list-app-planned-not-vibed/
├── app.py            # creates the FastAPI app, imports all models, includes each router
├── database.py       # engine, session factory, Base, get_session
├── requirements.txt  # fastapi, uvicorn, sqlalchemy, python-multipart
├── checklist/
│   ├── __init__.py
│   ├── model.py
│   ├── dao.py
│   ├── schema.py
│   └── controller.py
├── category/
│   ├── __init__.py
│   ├── model.py
│   ├── dao.py
│   ├── schema.py
│   └── controller.py
├── item/
│   ├── __init__.py
│   ├── model.py
│   ├── dao.py
│   ├── schema.py
│   └── controller.py
└── file/
    ├── __init__.py
    ├── model.py
    ├── dao.py
    ├── schema.py
    └── controller.py
```

## Running

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

The API runs at `http://127.0.0.1:8000`, and interactive docs are at `http://127.0.0.1:8000/docs`. The database file `checklist.db` is created on first start and is git-ignored.

## Resolved Questions
1. **What does a model object store, and should getters call the database?** The object holds its row's data, loaded by the DAO's query. Reading `checklist.name` is a plain attribute read with no query. Accessing a relationship such as `checklist.categories` lazy-loads it the first time, unless the DAO already loaded it with `selectinload`. No `get_name()`-style methods are needed. Domain logic like `copy` lives on the model and works on attributes.
2. **Does copy need an endpoint?** Yes, `POST /checklists/{id}/copy`, for checklists only. Copying is a deep copy, done on the models and saved in a single commit.
3. **Framework:** FastAPI, confirmed against its docs (see Stack).
4. **Renaming:** every resource supports `PATCH`.
5. **Item state:** no checked/unchecked state on items for now. If it's added later, `Item.copy` should decide whether to reset it.
6. **Upload size limit:** 10 MB; larger uploads get `413`.
