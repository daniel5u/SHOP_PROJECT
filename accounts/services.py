from .models import User

def change_user_address(user, address):
    user.default_address = address
    user.save()
    return user

def change_user_name(user, name):
    user.username = name
    user.save()
    return user