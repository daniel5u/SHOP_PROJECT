from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name',read_only=True)
    seller_name = serializers.CharField(source='seller.username',read_only=True)
    seller_phone = serializers.CharField(source='seller.phone',read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id','product','product_name','seller','seller_name','seller_phone','quantity','price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.username',read_only=True)
    buyer_phone = serializers.CharField(source='buyer.phone',read_only=True)

    class Meta:
        model = Order
        fields = ['id','buyer','buyer_name','buyer_phone','created_at','status','total_price','items']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(),write_only=True)
    
    class Meta:
        model = Order
        fields = ['items']

    def create(self, validated_data):
        buyer = self.context['request'].user
        
        # 检查用户是否已认证
        if not buyer or buyer.is_anonymous:
            raise serializers.ValidationError("user must be logged in to create an order")
        
        items_data = validated_data.pop('items')

        # 使用数据库事务确保数据一致性
        from django.db import transaction
        
        try:
            with transaction.atomic():
                order = Order.objects.create(buyer=buyer, status='pending')
                total_price = 0
                
                for item in items_data:
                    product = Product.objects.get(id=item['product'])
                    quantity = item.get('quantity', 1)

                    # 检查库存
                    if product.stock < quantity:
                        raise serializers.ValidationError(f"stock not enough: {product.name} (current stock: {product.stock}, need: {quantity})")

                    # 减少库存
                    product.stock -= quantity
                    product.save()

                    # 创建订单项
                    price = product.price * quantity
                    seller = product.seller
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        seller=seller,
                        quantity=quantity,
                        price=price
                    )
                    total_price += price
                
                order.total_price = total_price
                order.save()

                return order
                
        except Exception as e:
            # 如果出现任何异常，事务会自动回滚
            raise serializers.ValidationError(f"create order failed: {str(e)}")

class OrderListSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username',read_only=True)
    buyer_phone = serializers.CharField(source='buyer.phone',read_only=True)
    items = OrderItemSerializer(many=True,read_only=True)

    class Meta:
        model = Order
        fields = ['id','buyer','buyer_name','buyer_phone','created_at','status','total_price','items']

        