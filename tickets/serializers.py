from rest_framework import serializers
from .models import Ticket, TicketReply


class TicketReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketReply
        fields = ['id', 'message', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'fullname', 'phone', 'ticket_type', 'subject',
            'message', 'status', 'is_read', 'created_at', 'replies',
        ]
        read_only_fields = ['id', 'status', 'is_read', 'created_at', 'replies']

    def validate(self, attrs):
        request = self.context['request']
        if request.user.is_authenticated:
            if not attrs.get('fullname'):
                name = f"{request.user.first_name} {request.user.last_name}".strip()
                attrs['fullname'] = name or request.user.phone
            if not attrs.get('phone'):
                attrs['phone'] = request.user.phone
        else:
            # مهمان: fullname و phone اجباریه
            if not attrs.get('fullname'):
                raise serializers.ValidationError({"fullname": "این فیلد الزامی است"})
            if not attrs.get('phone'):
                raise serializers.ValidationError({"phone": "این فیلد الزامی است"})
        return attrs