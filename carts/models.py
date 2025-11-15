from django.db import models
from accounts.models import User
from products.models import Product
# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    product_name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product_name} ({self.quantity})"
    
    @property
    def total_price(self):
        if self.product and hasattr(self.product, 'price'):
            return self.product.price * self.quantity
        return 0