from django.shortcuts import render
from .models import Cart
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from .serializers import CartSerializer
from products.models import Product
from rest_framework import generics
from accounts.models import User
from rest_framework import permissions
from .serializers import CartCreateSerializer
from . import services
from rest_framework import serializers

class CartListCreateView(generics.ListCreateAPIView):
    """
    GET: 查看用户购物车
    POST: 添加商品到购物车
    """
    permission_classes = permissions.IsAuthenticated

    def get_queryset(self):
        return services.get_user_cart(self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CartCreateSerializer
        return CartSerializer
    
    def perfrom_create(self, serializer):
        """
        当调用POST (/cart/) 时，调用此方法
        """
        user = self.request.user
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        try:
            cart_item = services.add_to_cart(user, product_id, quantity)
            serializer.instance = cart_item
        except ValueError as e:
            raise serializers.ValidationError(str(e))

class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: 查看购物车商品
    PUT: 更新购物车商品数量
    DELETE: 删除购物车商品
    """
    permission_classes = permissions.IsAuthenticated

    def get_queryset(self):
        return services.get_user_cart(self.request.user)
    
    def perform_update(self, serializer):
        user = self.request.user
        cart_id = self.kwargs.get('pk')
        quantity = serializer.validated_data['quantity']
        
        try:
            updated = services.update_cart_item(user, cart_id, quantity)
            serializer.instance = updated
        except ValueError as e:
            raise serializers.ValidationError(str(e))

class ClearCartView(APIView):
    """
    DELETE: 清空购物车
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        services.clear_cart(request.user)
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)