import os, sys
from dotenv import load_dotenv
from client import init_qdrant_collection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from products.models import Product
from accounts.models import User
from agent.rag.retriever import add_documents

init_qdrant_collection()
all_products = Product.objects.all()

docs = []

for p in all_products:
    docs.append(
        {
            "id": p.id,
            "text": f"Product Name: {p.name}\nProduct Description: {p.description}",
            "metadata": {
                "product_id": p.id,
                "price": float(p.price),
                "stock": p.stock,
                "seller": p.seller.username,
            }
        }
    )

add_documents(docs)
print("Documents added successfully")