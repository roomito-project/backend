from django.http import HttpResponse

def home(request):
    return HttpResponse("خوش آمدید به صفحه اصلی Roomito!")
