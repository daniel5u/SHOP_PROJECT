from rest_framework import serializers, generics
from .models import Cart
from products.models import Product

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','name','price','image','seller']

class CartSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id','product','quantity','total_price']

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

class CartCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    quantity = serializers.IntegerField(default=1)

    class Meta:
        model = Cart
        fields = ['product_id', 'quantity']

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        product_id = attrs['product_id']
        quantity = attrs['quantity']

        product = Product.objects.filter(pk=product_id).first()
        if not product:
            raise serializers.ValidationError("Product not found.")
        
        existing_cart_item = Cart.objects.filter(user=user,product=product).first()
        total_quantity = (existing_cart_item.quantity if existing_cart_item else 0) + quantity

        if product.stock < total_quantity:
            raise serializers.ValidationError(f"Stock not enough. Only {product.stock} left.")

        attrs['product'] = product
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data['quantity']

        cart_item, created = Cart.objects.get_or_create(
            user = user,
            product = product,
            defaults = {'quantity': quantity, 'product_name': product.name}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        return cart_item
