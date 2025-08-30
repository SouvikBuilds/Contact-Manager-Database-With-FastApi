from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")  # fixed naming (must match .env)
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

class Contact(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str

def contact_helper(contact) -> dict:
    return {
        "id": str(contact["_id"]),
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "address": contact["address"]
    }

@app.get("/")
def hello():
    return {"message": "Hello, Welcome to Contact Manager"}

@app.post("/contacts")
def add_contact(contact: Contact):
    contact_dict = contact.dict()
    result = collection.insert_one(contact_dict)
    new_contact = collection.find_one({"_id": result.inserted_id})
    return contact_helper(new_contact)

@app.get("/contacts")
def get_all_contacts():
    return [contact_helper(contact) for contact in collection.find()]

@app.get("/contacts/{contact_id}")
def get_contact(contact_id: str):
    contact = collection.find_one({"_id": ObjectId(contact_id)})
    if contact:
        return contact_helper(contact)
    return {"error": "Contact not found"}

@app.put("/contacts/{contact_id}")
def update_contact(contact_id: str, contact: Contact):
    contact_dict = contact.dict()
    result = collection.update_one({"_id": ObjectId(contact_id)}, {"$set": contact_dict})
    if result.modified_count:
        updated_contact = collection.find_one({"_id": ObjectId(contact_id)})
        return contact_helper(updated_contact)
    return {"error": "Contact not found or no changes made"}

@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str):
    result = collection.delete_one({"_id": ObjectId(contact_id)})
    if result.deleted_count:
        return {"message": "Contact deleted successfully"}
    return {"error": "Contact not found"}


@app.get("/contacts/search/{query}")
def search_contacts(query: str):
    regex_query = {"$regex": query, "$options": "i"}
    contacts = collection.find({
        "$or": [
            {"name": regex_query},
            {"email": regex_query},
            {"phone": regex_query},
            {"address": regex_query}
        ]
    })
    return [contact_helper(contact) for contact in contacts]