from django.http import JsonResponse

def index(request):
    return JsonResponse({"message": "Library API is working!"})
