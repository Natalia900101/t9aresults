import csv
from datetime import datetime

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from . import forms
from .forms import UsernameForm, GameForm, MyResultForm, OpResultForm, AddListForm, ApproveResultForm, MyHalfResultForm, \
    OpHalfResultForm
from .helpers import Ranking, ListParser
from .models import Results, Lists, Games, Army, UserRenamed, GamingGroup, Units, ListsUnits


class HomeView(View):
    def get(self, request):
        renamed = True
        if self.request.user.id:
            if not UserRenamed.objects.filter(user_id=self.request.user.id).exists() \
                    and SocialAccount.objects.filter(user_id=self.request.user.id).exists():
                renamed = False

        head = '9th age results'
        to_be_approved = Results.objects.filter(Q(approved__isnull=True) & Q(player_id=self.request.user.id))
        my_results = Results.objects.filter(Q(player_id=self.request.user.id)).values('game_id')
        waiting_for_approval = Results.objects.filter(
            Q(approved__isnull=True) & ~Q(player_id=self.request.user.id) & Q(game_id__in=my_results))
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
                'rankings': [
                    {
                        'name': "Players",
                        'id': "table-players",
                        'sortable': True,
                        'ranking': rankingP.get_list(),
                    },
                    {
                        'name': "Armies",
                        'id': "table-armies",
                        'sortable': True,
                        'ranking': rankingA.get_list(),
                    },
                    {
                        'name': "Lists",
                        'id': "table-lists",
                        'sortable': True,
                        'ranking': rankingL.get_list(),
                    }
                ],
                'to_be_approved': to_be_approved,
                'waiting_for_approval': waiting_for_approval,
                'head': head,
                'user_renamed': renamed
            }
        )


class ApproveResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        head = 'Approve result'
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
                'form': form,
                'head': head
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
    def get(self, request, opt="nothing"):
        if opt == "disregard":
            u_r = UserRenamed.objects.create(user_id=self.request.user.id, old_username=self.request.user.username,
                                             new_username=self.request.user.username)
            return redirect('t9a:home')

        head = 'My account'
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
                'form': form,
                'head': head
            }
        )

    def post(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        old_username = self.request.POST.get('username')
        username = self.request.POST.get('new_username')
        user.username = username
        user.save()
        u_r = UserRenamed.objects.create(user_id=self.request.user.id, old_username=old_username, new_username=username)

        return redirect('t9a:home')


class ResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        head = 'My results'
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
                'results': my_result,
                'head': head
            }
        )


class ListsView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:
            head = 'My lists'
        else:
            head = 'List details'
        my_list = Lists.objects.filter(Q(owner_id=self.request.user.id) & Q(id=pk))
        if pk == 0:
            lists = Lists.objects.filter(owner_id=self.request.user.id)
        elif my_list:
            lists = my_list
        elif self.request.user.is_superuser:
            lists = Lists.objects.filter(id=pk)
        else:
            # if pk exists in approved result in game I played
            my_games = Results.objects.filter(Q(player_id=self.request.user.id) & Q(approved=True)).values_list(
                'game_id', flat=True)
            list_games = Results.objects.filter(Q(list_id=pk) & Q(approved=True)).values_list('game_id', flat=True)
            if set(my_games) & set(list_games):
                lists = Lists.objects.filter(id=pk)
            else:
                lists = []

        return render(
            request,
            'lists.html',
            context={
                'lists': lists,
                'head': head
            }
        )


class ParseList(LoginRequiredMixin, View):
    def get(self, request, pk):
        head = 'List parser'
        list = Lists.objects.get(id=pk)
        parser = ListParser()
        parsed_list = parser.parser(list.list)
        if not list.parsed:
            for pl in parsed_list:
                if Units.objects.filter(Q(unit=pl['unit']) & Q(points=pl['points'])).exists():
                    unit = Units.objects.get(Q(unit=pl['unit']) & Q(points=pl['points']))
                else:
                    unit = Units.objects.create(unit=pl['unit'], points=pl['points'], special=pl['special'],
                                                army=list.army)
                ListsUnits.objects.create(unit=unit, list=list, owner=list.owner)
            list.parsed = True
            list.save()
        return render(
            request,
            'parse-list.html',
            context={
                'head': head,
                'parsed_list': parsed_list
            }
        )


class AddListView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:  # if there's no list view add new list
            head = 'Add list'
            form = AddListForm()
        else:
            head = 'Edit list'
            form = AddListForm(instance=Lists.objects.get(
                Q(id=pk) & Q(owner_id=self.request.user.id)))  # if list exist and list.id occurs in results
            if len(Results.objects.filter(list_id=pk)) > 0:  # field 'list' is read only in form
                form.fields['list'].disabled = True
                form.fields['army'].disabled = True

        return render(
            request,
            'add-list.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request, pk=0):
        form = {}
        if pk != 0:  # if list exist return that list
            list = Lists.objects.get(Q(id=pk) & Q(owner_id=self.request.user.id))
            if list:
                if len(Results.objects.filter(list_id=list.id)) > 0:  # if list is connection with results,
                    POST = request.POST.copy()  # it's display and don't send in POST
                    POST['list'] = list.list  # we copy POST and overwrite value field 'list'
                    POST['army'] = list.army
                    form = AddListForm(POST)
        if not form:
            form = AddListForm(request.POST)
        owner = self.request.user.id
        if form.is_valid():
            if pk != 0:
                list = Lists.objects.get(Q(id=pk) & Q(owner_id=self.request.user.id))
                if list:
                    form.instance.id = list.id
                    if len(Results.objects.filter(list_id=list.id)) > 0:
                        form.instance.list = list.list
            form.instance.owner_id = owner
            form.save()
        return ListsView.get(self, request, form.instance.id)


class GameCreateView(LoginRequiredMixin, View):  # view to add games and results
    def get(self, request):
        head = 'Add game'
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
        form_op_result.fields['player'].queryset = get_user_model().objects.filter(
            ~Q(id=self.request.user.id)).order_by('username')
        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result,
                'head': head,
                'save_name': 'add-game'
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

        fpr.auto_approve(fmr.comment)

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


class AddGameHalfView(LoginRequiredMixin, View):
    def get(self, request):
        head = 'Add game'
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
        form_my_result = MyHalfResultForm(initial=init_my_result, prefix='my')  # we used prefix to distinctions form
        form_my_result.fields['list'].queryset = Lists.objects.filter(
            Q(owner_id=self.request.user.id) & Q(parsed=True))  # shows only my lists, modify options on the fly
        form_op_result = OpHalfResultForm(prefix='op')  # there are that same fields
        form_op_result.fields['player'].queryset = get_user_model().objects.filter(
            ~Q(id=self.request.user.id)).order_by('username')

        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result,
                'head': head,
                'save_game': 'add-short-game',
            }
        )
    def post(self, request):
        form_game = forms.GameForm(request.POST)
        form_my_result = forms.MyHalfResultForm(request.POST, prefix='my')
        form_op_result = forms.OpHalfResultForm(request.POST, prefix='op')
        if form_game.is_valid() and form_my_result.is_valid() and form_op_result.is_valid():
            fg = form_game.save(commit=False)  # first we save game form because results have FG to game
            fg.save()
        else:
            raise ValidationError('Something went wrong.')
        player = self.request.user.id
        form_my_result.instance.player_id = player
        form_my_result.instance.game_id = form_game.instance.id
        fmr = form_my_result.save(commit=False)
        fmr.save()

        form_op_result.instance.game_id = form_game.instance.id  # we assign value to opponent result based on our form
        #  form_op_result.instance.result = None

        fpr = form_op_result.save(commit=False)
        fpr.save()


        return redirect('t9a:home')


class AllResultsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('t9a:home')

    def get(self, request, pk=0):
        head = 'All results'

        waiting_for_approval = Results.objects.filter(Q(approved__isnull=True))
        for r in waiting_for_approval:
            r.myself = Results.objects.get(~Q(player_id=r.player_id) & Q(game_id=r.game_id))

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
                'results': all_results,
                'query': query,
                'head': head,
                'waiting_for_approval': waiting_for_approval,
            }
        )


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('t9a:home')


class CSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('t9a:home')

    # Create the HttpResponse object with the appropriate CSV header.
    def get(self, request):
        filename = 'all-results-' + datetime.now().strftime('%Y-%m-%d') + '.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )

        writer = csv.writer(response)
        games = Games.objects.all()
        writer.writerow(Games().csv_array_header() + Results().csv_array_header())
        for g in games:
            results = Results.objects.filter(Q(game_id=g.id) & Q(approved=True))
            game_part = g.csv_array()
            for r in results:
                writer.writerow(game_part + r.csv_array())

        return response


class AddGamingGroup(LoginRequiredMixin, View):
    def get(self, request):
        head = 'Add group'
        form = forms.AddGamingGroupForm
        return render(
            request,
            'add-gaming-group.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request):
        form = forms.AddGamingGroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect('t9a:list-groups')


class GamingGroupListView(LoginRequiredMixin, View):
    def get(self, request):
        head = 'List groups'
        groups = GamingGroup.objects.all()
        for g in groups:
            g.flat_members = list(g.members.values_list('username', flat=True))
            g.iamin = self.request.user.username in g.flat_members

        return render(
            request,
            'list-groups.html',
            context={
                'groups': groups,
                'head': head
            }

        )


class JoinGroupView(LoginRequiredMixin, View):

    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        member = get_user_model().objects.get(id=self.request.user.id)
        group.members.add(member)

        return redirect('t9a:list-groups')

    def post(self, request, pk):
        return self.get(request, pk)


class LeaveGroupView(LoginRequiredMixin, View):

    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        member = get_user_model().objects.get(id=self.request.user.id)
        group.members.remove(member)

        return redirect('t9a:list-groups')

    def post(self, request, pk):
        return self.get(request, pk)


class GroupRankingView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        head = f'Rankings for {group}'
        members = group.members.values_list('id', flat=True)
        results = Results.objects.filter(Q(player_id__in=members) & Q(approved=True))

        rankingI = Ranking(User)
        rankingE = Ranking(User)
        rankingA = Ranking(User)

        for r in results:
            is_opponent_in_group = Results.objects.filter(
                ~Q(player_id=r.player_id) & Q(player_id__in=members) & Q(game_id=r.game_id)
            ).count()
            rankingA.add(r.player_id, r.result, r.score)
            if is_opponent_in_group == 0:
                rankingE.add(r.player_id, r.result, r.score)
            else:
                rankingI.add(r.player_id, r.result, r.score)

        return render(
            request,
            'group-ranking.html',
            context={
                'rankings': [
                    {
                        'name': "Internal",
                        'id': "table-internal",
                        'sortable': True,
                        'ranking': rankingI.get_list(),
                    },
                    {
                        'name': "External",
                        'id': "table-external",
                        'sortable': True,
                        'ranking': rankingE.get_list(),
                    },
                    {
                        'name': "All",
                        'id': "table-all",
                        'sortable': True,
                        'ranking': rankingA.get_list(),
                    },
                ],
                'head': head,
            }
        )
