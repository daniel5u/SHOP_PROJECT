from rest_framework import serializers
from products.models import Product
from carts.models import Cart

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','name','description','price','stock']

class CartSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id','product','quantity']

class AgentChatSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="The message to send to the agent")
    