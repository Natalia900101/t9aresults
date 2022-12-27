from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View

from .forms import UsernameForm
from .models import Results, Lists


class HomeView(View):
    def get(self, request):
        return render(
            request,
            'home.html',
        )


class ChangeUsernameView(LoginRequiredMixin, View):
    def get(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        username = user.username
        init = {
            'username': username
        }

        form = UsernameForm(initial=init)
        return render(
            request,
            'my-account.html',
            context={
                'form': form

            }
        )

    def post(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        username = self.request.POST.get('new_username')
        user.username = username
        user.save()

        return redirect('t9a:home')



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
