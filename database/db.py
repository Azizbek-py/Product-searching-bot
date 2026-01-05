from tinydb import TinyDB, Query
from tinydb.database import Document

db1 = TinyDB("database/users.json", indent=4)
db2 = TinyDB("database/products.json", indent=4)
db3 = TinyDB("database/statistics.json", indent=4)

users = db1.table("users")
products = db2.table("products")
statistics = db3.table("statistics")
User = Query()

def get(table, user_id = None):
    if table == "users":
        if user_id:
            return users.get(doc_id=user_id)
        return users.all()
    elif table == "products":
        if user_id:
            return products.search(User.user_id == user_id)
        return products.all()
    elif table == "statistics":
        return statistics.all()
    
def insert(table, data, user_id = None):
    if table == "users":
        doc = Document(
                value=data,
                doc_id=user_id
            )
        try:
            users.insert(doc)
        except:
            users.update(doc, doc_ids=[user_id])
    elif table == "products":
        doc = {
        "user_id": user_id,
        "items": data
        }

        if products.contains(doc_id=user_id):
            products.update(doc, doc_ids=[user_id])
        else:
            products.insert(Document(doc, doc_id=user_id))

    elif table == "statistics":
        doc = Document(
                value=data,
                doc_id=user_id
            )
        try:
            statistics.insert(doc)
        except:
            statistics.update(doc, doc_ids=[user_id])

def upd(table, data, user_id=None):
    if table == "users":
        doc = Document(
                value=data,
                doc_id=user_id
            )
        users.update(doc, doc_ids=[user_id])
    elif table == "products":
        pass
    elif table == "statistics":
        doc = Document(
                value=data,
                doc_id=user_id
            )
        statistics.update(doc, doc_ids=[user_id])