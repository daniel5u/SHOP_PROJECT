from django.urls import path
from .views import CartListCreateView,CartDetailView,ClearCartView

urlpatterns = [
    path('cart/',CartListCreateView.as_view(),name='cart-list-create'),
    path('cart/<int:pk>/',CartDetailView.as_view(),name='cart-detail'),
    path('cart/clear/',ClearCartView.as_view(),name='cart-clear'),
]
