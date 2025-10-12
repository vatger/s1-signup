import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

from .models import RosterEntry

load_dotenv()

@csrf_exempt
def get_roster(request):
    if request.method == "GET":
        auth_header = request.headers.get("Authorization")
        if auth_header == f"Token {os.getenv('ROSTER_KEY')}":
            entries = RosterEntry.objects.all()
            entries_data = []
            for entry in entries:
                entries_data.append(entry.cid)
            return JsonResponse({"entries": entries_data})
        else:
            return JsonResponse({"error": "Unauthorized"})
    else:
        return HttpResponse(status=405)
