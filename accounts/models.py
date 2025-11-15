from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
# Create your models here.
class User(AbstractUser):
    USER_ROLES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('developer', 'Developer'),
    ]
    username = models.CharField(max_length=20, blank=True, null=False, default='', unique=False)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='buyer')
    default_address = models.CharField(max_length=200, blank=True, null=True)
    uuid_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['role','username']
    def save(self, *args, **kwargs):
        if self.role == 'developer':
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"username:{self.username}, phone:{self.phone}, role:{self.role}, default_address:{self.default_address}, uuid_id:{self.uuid_id}"