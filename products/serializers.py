from rest_framework import serializers
from .models import Product
from accounts.serializers import UserSerializer

class ProductSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

