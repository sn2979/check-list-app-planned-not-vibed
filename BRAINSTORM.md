## API
```
/checklists
/checklists/{id}/categories/{id}
/checklist/{id}/categories/{id}/items/{id}
/checklist/{id}/categories/{id}/items/{id}/files/{id}
/checklist/{id}/categories/{id}/files/{id}
```

## Controller Classes
```python
class Checklist:
    def __init__(self):
        self._id = generate_uuid() #find a library for this
        self._name = name
        self._categories = {}

    def copy(self) -> Checklist:
        copy = Checklist(self._name)

        for category in self._categories:
            copy._categories[generate_uuid()] = category.copy()

        return copy
```

```python
class Category:
    def __init__(self, name):
        self._id = generate_uuid()
        self._name = name
        self._items = {}
        self._files = {}
    
    def get_id(self) -> str:
        return self._id

    def get_name(self) -> str:
        return self._name
    
    def list_files(self) -> List[Files]:
        return self._files
    
    def list_items(self) -> List[Items]:
        return self._items
    
    def get_file(self, id) -> File:
        return self._files[id]
    
    def get_item(self, id) -> Item:
        return self._items[id]

    def copy(self) -> Category:
        copy = Category(self._name)

        for item in self._items:
            copy._items[generate_uuid()] = item.copy()
        
        for file in self._files:
            copy._files[generate_uuid()] = file.copy()

        return copy
    
    def upload_file(self, name):
        # I am not sure what library we can use here but the idea is that a user supplies the file when they upload. We should parse it for the file name and the content. Maybe there is a library to do that? You should explain to me how it does this to, but do not do that in a code comment. Just explain to me
        self._files[generate_uuid()] = File(name, content)
```
```python
class Item:
    def __init__(self, name):
        self._id = generate_uuid()
        self._name = name
        self._files = {}

    def get_id(self) -> str:
        return self._id

    def get_name(self) -> str:
        return self._name
    
    def list_files(self) -> List[Files]:
        return self._files
    
    def get_file(self, id) -> File:
        return self._files[id]

    def copy(self) -> Item:
        copy = Item(self._name)
        
        for file in self._files:
            copy._files.append(file.copy())

        return copy
    
    def upload_file(self, name):
        # I am not sure what library we can use here but the idea is that a user supplies the file when they upload. We should parse it for the file name and the content. Maybe there is a library to do that? You should explain to me how it does this to, but do not do that in a code comment. Just explain to me
        self._files[generate_uuid()] = File(name, content)
```
```python
class File:
    def __init__(self, name, content):
        self._id = generate_uuid()
        self._name = name
        self._content = content
    
    def get_id(self) -> str:
        return self._id
    
    def get_name(self) -> str:
        return self._name
    
    def get_content(self) -> str:
        return self._content
    
    def copy(self) -> File:
        return File(self._name, self._content)
```

I defined all of the above in Python object syntax, but you should be able to translate this into models for the various `model.py` files used by SQLAlchemy (we will use a SQLite databse for storing things persistently)

## File Structure
```
├──check-list-app-planned-not-vibed
│   ├── app.py
│   ├── database.py
│   ├── checklist
        |-- model.py
        |-- database.py
        |-- controller.py
    |-- category
        |-- model.py
        |-- database.py
        |-- controller.py
    |-- item
        |-- model.py
        |-- database.py
        |-- controller.py
    |-- file
        |-- model.py
        |-- database.py
        |-- controller.py
```

The `database.py` files will do the crud operations on the database itself. The controller will take in the API call to the endpoints and route to the appropriate function call

## Open Questions/Thoughts
1. Would like to discuss GOOD software engineering principles on integrating some of this. For example, on `get_name` for the `Checklist` for example, should we be loading in the checklist fields from the table and populating and object at runtime? Not sure how. Actually, the pattern I think that makes the most sense is for `get_name` to call the corresponding crud operation we've defined in database.py. Other methods, like `copy` for all of them should load in the corresponding required info from the database via the getter functions and then return the appropriate response. But if that is the case, then what are we actually storing in the "object"? Nothing? How are we going to resolve that?
2. Copy is not an item, so do we need to create an endpoint for it?