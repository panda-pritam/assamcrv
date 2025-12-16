from django.http import Http404
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

class AdminAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Restrict access to all /administrator routes
        if 'administrator' in path:
            if not request.user.is_authenticated:
                raise Http404()

            # Check role for authenticated users
            role = getattr(getattr(request.user, 'role', None), 'name', None)
            if role == 'Viewer':
                raise Http404()

        # Global unauthenticated check (optional depending on your app flow)
        # elif not request.user.is_authenticated and not path.startswith('/admin/'):
        #     return redirect('login')

        return self.get_response(request)
