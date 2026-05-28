class TenantMiddleware:
    """Attaches the tenant to the request based on the authenticated user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.tenant = getattr(request.user, 'tenant', None)
        return self.get_response(request)
