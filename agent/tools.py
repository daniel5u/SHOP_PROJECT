from pydantic import BaseModel, Field
from typing import List
from carts import services as cart_services
from products import services as product_services
from accounts import services as account_services
from .rag.retriever import retrieve

#------定义function calling 的 schema
class AddToCartInput(BaseModel):
    product_id: int = Field(..., description="The ID of the product to add to the cart")
    quantity: int = Field(..., description="The quantity of the product to add to the cart")

class ClearCartInput(BaseModel):
    pass

class UploadProductInput(BaseModel):
    name: str = Field(..., description="The name of the product")
    description: str = Field(..., description="The description of the product")
    price: float = Field(..., description="The price of the product")
    stock: int = Field(..., description="The stock of the product")

class UpdateProductInput(BaseModel):
    name: str = Field(..., description="The name of the product")
    description: str = Field(..., description="The description of the product")
    price: float = Field(..., description="The price of the product")
    stock: int = Field(..., description="The stock of the product")

class DeleteProductInput(BaseModel):
    product_id: int = Field(..., description="The ID of the product to delete")

class SearchProductsInput(BaseModel):
    keyword: str = Field(..., description="The keyword to search for products")

class ChangeUserNameInput(BaseModel):
    name: str = Field(..., description="The name to change to")

class ChangeUserAddressInput(BaseModel):
    address: str = Field(..., description="The address to change to")

class RAGRetrieveInput(BaseModel):
    query: str = Field(..., description="The query to retrieve from the RAG")
#------定义工具函数   
def add_to_cart_tool(user, args:AddToCartInput):
    item = cart_services.add_to_cart(user, args.product_id, args.quantity)
    return f"Added {item.product.name}, quantity: {item.quantity} to cart."

def clear_cart_tool(user):
    cart_services.clear_cart(user)
    return "Cleared the cart."

def list_cart_tool(user):
    cart_items = cart_services.get_user_cart(user)
    if not cart_items.exists():
        return "Your cart is empty."
    result = []
    for item in cart_items:
        result.append(f"{item.product.name} - {item.quantity} units")
    return "The cart contains: " + ", ".join(result)

def search_products_tool(keyword):
    products = product_services.search_products(keyword)
    if not products.exists():
        return "No products found."
    result = []
    for product in products:
        result.append(f"{product.name} - {product.price}")
    return "The products are: " + ", ".join(result)

def upload_product_tool(user, args:UploadProductInput):
    product = product_services.upload_product(user, args.model_dump())
    return f"Uploaded product: {product.name}"

def update_product_tool(user, product_id, args:UpdateProductInput):
    product = product_services.update_product(user, product_id, args.model_dump())
    return f"Updated product: {product.name}"

def delete_product_tool(user, product_id):
    product_services.delete_product(user, product_id)
    return f"Deleted product: {product_id}"

def change_user_name_tool(user, args:ChangeUserNameInput):
    user = account_services.change_user_name(user, args.name)
    return f"Changed user name to: {user.username}"

def change_user_address_tool(user, args:ChangeUserAddressInput):
    user = account_services.change_user_address(user, args.address)
    return f"Changed user address to: {user.default_address}"

def rag_retrieve_tool(args:RAGRetrieveInput):
    try:
        retieve_result = retrieve(args.query)
        if not retieve_result:
            return "No relevant information found in the knowledge base."
        context = "\n".join(
            [f"[{i+1}] {r['text']} (score={r['score']:.3f})" for i, r in enumerate(retieve_result)]
            
        )
        return f"Here is the retrieved knowledge:\n{context}"
    except Exception as e:
        return f"RAG retrieval error {str(e)}"
