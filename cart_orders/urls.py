from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartView, CartItemViewSet, ApplyDiscountView, RemoveDiscountView, CheckoutView, OrderViewSet

item_router = DefaultRouter()
item_router.register('', CartItemViewSet, basename='cart-item')

order_router = DefaultRouter()
order_router.register('', OrderViewSet, basename='order')

urlpatterns = [
    path('cart/', CartView.as_view()),
    path('cart/items/', include(item_router.urls)),
    path('cart/apply-discount/', ApplyDiscountView.as_view()),
    path('cart/remove-discount/', RemoveDiscountView.as_view()),
    path('cart/checkout/', CheckoutView.as_view()),
    path('orders/', include(order_router.urls)),
]