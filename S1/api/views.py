# views.py
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from dotenv import load_dotenv
import os

load_dotenv()


@method_decorator(csrf_exempt, name="dispatch")
def user_delete_view(request, id):
    # Check for DELETE method
    if request.method == "DELETE":
        # Verify Authorization Token
        auth_header = request.headers.get("Authorization")
        if auth_header == f"Token {os.getenv("GDPR_KEY")}":
            try:
                user = User.objects.get(id=id)
                user.delete()
                return JsonResponse(
                    {"message": "User deleted successfully"}, status=200
                )
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=404)
        else:
            return JsonResponse({"error": "Unauthorized"}, status=401)
    else:
        return HttpResponse(status=405)  # Method Not Allowed


@method_decorator(csrf_exempt, name="dispatch")
def user_retrieve_view(request, id):
    # Check for GET method
    if request.method == "GET":
        # Verify Authorization Token
        auth_header = request.headers.get("Authorization")
        if auth_header == f"Token {os.getenv("GDPR_KEY")}":
            try:
                user = User.objects.get(id=id)
                user_data = {}
                for field in user._meta.get_fields():
                    if hasattr(user, field.name):
                        user_data[field.name] = getattr(user, field.name)
                return JsonResponse(user_data, status=200)
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=404)
        else:
            return JsonResponse({"error": "Unauthorized"}, status=401)
    else:
        return HttpResponse(status=405)  # Method Not Allowed
