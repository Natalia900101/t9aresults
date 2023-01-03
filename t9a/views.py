from datetime import datetime

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View

from . import forms
from .forms import UsernameForm, GameForm, MyResultForm, OpResultForm, AddListForm, ApproveResultForm
from .helpers import Ranking
from .models import Results, Lists, Games, Army


class HomeView(View):
    def get(self, request):
        to_be_approved = Results.objects.filter(Q(approved__isnull=True) & Q(player_id=self.request.user.id))
        my_results = Results.objects.filter(Q(player_id=self.request.user.id)).values('game_id')
        waiting_for_approval = Results.objects.filter(Q(approved__isnull=True) & ~Q(player_id=self.request.user.id) & Q(game_id__in=my_results))
        for r in to_be_approved:
            r.opponent = Results.objects.get(~Q(player_id=r.player_id)
                                             & Q(game_id=r.game_id))
        for r in waiting_for_approval:
            r.myself = Results.objects.get(~Q(player_id=r.player_id)
                                             & Q(game_id=r.game_id))


        rankingL = Ranking(Lists)
        rankingA = Ranking(Army)
        rankingP = Ranking(User)
        results = Results.objects.filter(approved__isnull=False)

        for r in results:
            rankingL.add(r.list_id, r.result, r.score)
            rankingA.add(r.list.army_id, r.result, r.score)
            rankingP.add(r.player_id, r.result, r.score)
        return render(
            request,
            'home.html',
            context={
                'rankings': [rankingP.get_list(), rankingA.get_list(), rankingL.get_list()],
                'to_be_approved': to_be_approved,
                'waiting_for_approval': waiting_for_approval
            }
        )


class ApproveResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:  # in form is displayed last  introduced value
            list = result[0].list
        else:
            list = 0
        result = Results.objects.get(id=pk)
        initial = {
            'list': list,
            'approved': True
        }
        form = ApproveResultForm(initial=initial)
        form.fields['list'].queryset = Lists.objects.filter(
            owner_id=self.request.user.id)  # shows only my lists, modify options on the fly

        return render(
            request,
            'approve-result.html',
            context={
                'form': form
            }
        )

    def post(self, request, pk=0):
        form = forms.ApproveResultForm(request.POST)
        if form.is_valid():

            check_list = Lists.objects.filter(Q(id=form.instance.list_id) & Q(owner_id=self.request.user.id)).count()
            result = Results.objects.get(id=pk)
            print(check_list)
            if check_list == 1 and result.player_id == self.request.user.id:
                result.approved = form.instance.approved
                result.list_id = form.instance.list_id
                result.comment = form.instance.comment
                result.save()
            return redirect('t9a:home')


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
    def get(self, request, pk=0):
        if pk == 0:
            my_result = Results.objects.filter(player_id=self.request.user.id)
        else:
            my_result = Results.objects.filter(Q(player_id=self.request.user.id) & Q(game_id=pk))
        for r in my_result:
            r.opponent = Results.objects.get(~Q(player_id=r.player_id)
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


class AddListView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:  # if there's no list view add new list
            form = AddListForm()
        else:
            form = AddListForm(instance=Lists.objects.get(id=pk))  # if list exist and list.id occurs in results
            if len(Results.objects.filter(list_id=pk)) > 0:  # field 'list' is read only in form
                form.fields['list'].disabled = True

        return render(
            request,
            'add-list.html',
            context={
                'form': form
            }
        )

    def post(self, request, pk=0):
        form = {}
        if pk != 0:  # if list exist return that list
            list = Lists.objects.get(id=pk)
            if list:
                if len(Results.objects.filter(list_id=list.id)) > 0:  # if list is connection with results,
                    POST = request.POST.copy()  # it's display and don't send in POST
                    POST['list'] = list.list  # we copy POST and overwrite value field 'list'
                    form = AddListForm(POST)
        if not form:
            form = AddListForm(request.POST)
        owner = self.request.user.id
        if form.is_valid():
            if pk != 0:
                list = Lists.objects.get(id=pk)
                if list:
                    form.instance.id = list.id
                    if len(Results.objects.filter(list_id=list.id)) > 0:
                        form.instance.list = list.list
            form.instance.owner_id = owner
            form.save()
        return ListsView.get(self, request, form.instance.id)


class GameCreateView(LoginRequiredMixin, View):  # view to add games and results
    def get(self, request):
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:  # in form is displayed last  introduced value
            event = Games.objects.get(id=result[0].game_id).event
            points_event = Games.objects.get(id=result[0].game_id).points_event
            event_type = Games.objects.get(id=result[0].game_id).event_type
            list = result[0].list
        else:
            event = ''
            points_event = 4500
            list = 0
            event_type = 'test'

        init_game = {  # init value to game form
            'event': event,
            'points_event': points_event,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'event_type': event_type
        }
        form_game = GameForm(initial=init_game)
        init_my_result = {  # init value to my result form
            'list': list
        }
        init_op_result = {
        }
        form_my_result = MyResultForm(initial=init_my_result, prefix='my')  # we used prefix to distinctions form
        form_my_result.fields['list'].queryset = Lists.objects.filter(
            owner_id=self.request.user.id)  # shows only my lists, modify options on the fly
        form_op_result = OpResultForm(initial=init_op_result, prefix='op')  # there are that same fields
        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result
            }
        )

    def post(self, request):
        form_game = forms.GameForm(request.POST)
        form_my_result = forms.MyResultForm(request.POST, prefix='my')
        form_op_result = forms.OpResultForm(request.POST, prefix='op')
        if form_game.is_valid() and form_my_result.is_valid() and form_op_result.is_valid():
            fg = form_game.save(commit=False)  # first we save game form because results have FG to game
            fg.save()
        else:
            raise ValidationError('Something went wrong.')
        player = self.request.user.id
        form_my_result.instance.player_id = player
        form_my_result.instance.score = self.count_score \
            (form_game.instance.points_event, form_my_result.instance.points, form_op_result.instance.points,
             form_my_result.instance.secondary)
        score = form_my_result.instance.score
        form_my_result.instance.result = 1 if score > 10 else -1 if score < 10 else 0
        form_my_result.instance.game_id = form_game.instance.id
        form_my_result.instance.approved = True
        fmr = form_my_result.save(commit=False)
        fmr.save()

        form_op_result.instance.game_id = form_game.instance.id  # we assign value to opponent result based on our form
        form_op_result.instance.score = 20 - score
        form_op_result.instance.secondary = form_my_result.instance.secondary * -1
        form_op_result.instance.result = form_my_result.instance.result * -1
        form_op_result.instance.first = not form_my_result.instance.first
        #  form_op_result.instance.result = None

        fpr = form_op_result.save(commit=False)
        fpr.save()

        return redirect('t9a:home')

    def count_score(self, points, my, op, scenario):  # function to count score used in Result
        difference = my - op
        fraction = abs(difference / points)
        score = 0
        if fraction <= 0.05:
            score += 10
        elif fraction <= 0.10:
            score += 11
        elif fraction <= 0.20:
            score += 12
        elif fraction <= 0.30:
            score += 13
        elif fraction <= 0.40:
            score += 14
        elif fraction <= 0.50:
            score += 15
        elif fraction <= 0.70:
            score += 16
        else:
            score += 17

        if difference < 0:
            score = 20 - score
        score += 3 * scenario
        return score


class AllResultsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('t9a:home')

    def get(self, request, pk=0):
        if self.request.GET.get("q") is None:
            all_results = Results.objects.all()
            query = ''
        else:
            query = self.request.GET.get("q")
            player = User.objects.filter(Q(username__icontains=query)).values("id")
            list = Lists.objects.filter(Q(name__icontains=query)).values("id")
            army = Army.objects.filter(Q(name__icontains=query)).values("id")
            all_results = Results.objects.filter(
                Q(player_id__in=player) | Q(list_id__in=list)  # | Q(army_id__in=army)
            )
        duplicates = []
        for r in all_results:
            if r.game_id in duplicates:
                r = None
            else:
                r.opponent = Results.objects.get(~Q(player_id=r.player_id)
                                                 & Q(game_id=r.game_id))
                duplicates.append(r.game_id)
        return render(
            request,
            'all-results.html',
            context={
                'all_results': all_results,
                'query': query
            }
        )


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('t9a:home')
