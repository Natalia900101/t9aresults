from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.views import View

from .models import Results, Lists


class HomeView(View):
    def get(self, request):
        return render(
            request,
            'home.html',
        )


class ResultView(LoginRequiredMixin, View):
    def get(self, request):
        my_result = Results.objects.filter(player_id=self.request.user.id)
        for r in my_result:
            r.opponent = Results.objects.get(~Q(player_id=self.request.user.id)
                                             & Q(game_id=r.game_id))
        return render(
            request,
            'results.html',
            context={
               'results': my_result

            }
        )


class ListsView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:
            lists = Lists.objects.filter(owner_id=self.request.user.id)
        else:
            lists = Lists.objects.filter(id=pk)

        return render(
            request,
            'lists.html',
            context={
                'lists': lists
            }
        )

