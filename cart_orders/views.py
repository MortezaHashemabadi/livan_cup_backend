import pprint

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from accounts.models import Address
from pricing.models import Discount
from .services import create_order_from_cart
from pricing.services import get_unit_price, validate_discount, calculate_discount_amount
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 👈 این خط به جنگو میگه دیتای از نوع فایل (FormData) رو هم قبول کن
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        cart = get_or_create_cart(self.request.user)
        return cart.items.all()

    # 👈 متد create رو اورراید می‌کنیم تا ارورهای اعتبارسنجی رو دقیق ببینیم
    def create(self, request, *args, **kwargs):
        print("\n" + "🔍" * 15)
        print("📥 Raw Data:", request.data)
        print("📁 Files:", request.FILES)
        print("🔍" * 15 + "\n")

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            # این همون اروری هست که باعث 400 میشه! الان میتونی تو ترمینال بخونیش
            print("❌ Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        cart = get_or_create_cart(self.request.user)
        variant = serializer.validated_data['variant']
        design = serializer.validated_data.get('design')
        print_file = self.request.FILES.get('print_file')

        existing = cart.items.filter(variant=variant, design=design).first()
        if existing:
            existing.quantity += serializer.validated_data.get('quantity', 1)
            if print_file:
                existing.print_file = print_file
            existing.save()
            serializer.instance = existing
        else:
            instance = serializer.save(cart=cart)
            if print_file:
                instance.print_file = print_file
                instance.save(update_fields=['print_file'])


class ApplyDiscountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        cart = get_or_create_cart(request.user)
        discount = Discount.objects.filter(code=code).first()
        if not discount:
            return Response({"detail": "کد تخفیف یافت نشد"}, status=404)

        subtotal = CartSerializer().get_subtotal(cart)
        try:
            validate_discount(discount, subtotal)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        cart.discount = discount
        cart.save(update_fields=['discount'])
        return Response(CartSerializer(cart).data)


class RemoveDiscountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = get_or_create_cart(request.user)
        cart.discount = None
        cart.save(update_fields=['discount'])
        return Response(CartSerializer(cart).data)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        print("\n" + "=" * 30)
        print("📥 Data Received from Frontend:")
        pprint.pprint(request.data)
        print("=" * 30 + "\n")

        cart = get_or_create_cart(request.user)
        address = get_object_or_404(Address, id=request.data.get('address_id'), user=request.user)
        try:
            order = create_order_from_cart(cart, address, notes=request.data.get('notes', ''))
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')