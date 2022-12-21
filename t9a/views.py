from django.shortcuts import render
from django.views import View

from t9a.models import Deployments


class HomeView(View):
    def get(self, request):
        dep = Deployments.objects.all()
        return render(
            request,
            'home.html',
            context = {
                'dep': dep

            }
        )
