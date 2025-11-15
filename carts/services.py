from django.shortcuts import get_object_or_404
from .models import Cart
from products.models import Product
from django.db import transaction

def get_user_cart(user):
    """
    获取用户购物车
    """
    return Cart.objects.filter(user=user).select_related('product')

@transaction.atomic
def add_to_cart(user, product_id, quantity):
    """
    添加商品到购物车
    """
    product = get_object_or_404(Product, pk=product_id)

    # 检查库存
    existing_item = Cart.objects.filter(user=user, product=product).first()
    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > product.stock:
            raise ValueError(f"Stock not enough. Only {product.stock} left.")
        existing_item.quantity = new_quantity
        existing_item.save()
        return existing_item

    if quantity > product.stock:
        raise ValueError(f"Stock not enough. Only {product.stock} left.")
    
    return Cart.objects.create(user=user, product=product, quantity=quantity)

def update_cart_item(user, cart_id, quantity):
    """
    更新购物车商品数量
    """
    cart_item = get_object_or_404(Cart, id=cart_id, user=user)
    
    if quantity > cart_item.product.stock:
        raise ValueError(f"Stock not enough. Only {cart_item.product.stock} left.")
    cart_item.quantity = quantity
    cart_item.save()
    
    return cart_item

def delete_cart_item(user, cart_id):
    """
    删除购物车商品
    """
    cart_item = get_object_or_404(Cart, id=cart_id, user=user)
    cart_item.delete()
    return True

def clear_cart(user):
    """
    清空购物车
    """
    Cart.objects.filter(user=user).delete()
    return True