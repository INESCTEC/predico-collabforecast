# views.py
from django.shortcuts import render
from .settings.base import SWAGGER_BASE_URL


def front_page_view(request):
    context = {
        'swagger_link': SWAGGER_BASE_URL + 'swagger/',
        'redoc_link': SWAGGER_BASE_URL + 'redoc/',
    }
    return render(request, 'front_page.html', context)
