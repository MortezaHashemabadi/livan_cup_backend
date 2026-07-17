from rest_framework.throttling import SimpleRateThrottle


class OTPRateThrottle(SimpleRateThrottle):
    scope = "otp"

    def get_cache_key(self, request, view):
        phone = request.data.get("phone")
        if not phone:
            return None
        return self.cache_format % {"scope": self.scope, "ident": phone}