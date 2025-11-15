from .models import Product
from django.shortcuts import get_object_or_404

def search_products(keyword):
    return Product.objects.filter(name__icontains=keyword)

def upload_product(user, product_data):
    product = Product.objects.create(**product_data, seller=user)
    return product

def update_product(user, product_id, product_data):
    product = get_object_or_404(Product, id=product_id)
    if product.seller != user:
        raise ValueError("You are not the seller of this product.")
    product.update(**product_data)
    return product

def delete_product(user, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.seller != user:
        raise ValueError("You are not the seller of this product.")
    product.delete()
    return True