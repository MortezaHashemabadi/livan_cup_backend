from rest_framework import serializers
from .models import ProductReview, Testimonial


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'rating', 'comment', 'user_name', 'user_role', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_user_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or (obj.user.phone[:4] + "***" + obj.user.phone[-2:])

    def get_user_role(self, obj):
        profile = getattr(obj.user, 'business_profile', None)
        if not profile:
            return ''
        position = profile.position
        business_name = profile.business_name
        if position and business_name:
            return f"{position} . {business_name}"
        return position or business_name or ''

    def validate(self, attrs):
        from cart_orders.models import OrderItem
        request = self.context['request']
        product = attrs.get('product')

        has_purchased = OrderItem.objects.filter(
            order__user=request.user, variant__product=product
        ).exclude(order__status='cancelled').exists()
        if not has_purchased:
            raise serializers.ValidationError("فقط خریداران این محصول می‌توانند نظر ثبت کنند")

        if ProductReview.objects.filter(product=product, user=request.user).exists():
            raise serializers.ValidationError("شما قبلاً برای این محصول نظر ثبت کرده‌اید")

        return attrs


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'customer_name', 'customer_title', 'avatar', 'rating', 'comment']