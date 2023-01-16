from django import forms
from django.contrib.auth import get_user_model

from t9a.models import Games, Results, Lists, GamingGroup, HalfResults, UnitsPoints


class UsernameForm(forms.ModelForm):
    username = forms.CharField(label='Username')
    new_username = forms.CharField(label='New username')

    class Meta:
        model = get_user_model()
        fields = ('username',)


class GameForm(forms.ModelForm):
    turns = forms.IntegerField(max_value=6, min_value=1, initial=6)

    class Meta:
        model = Games
        fields = ('date', 'map', 'deploy', 'secondary', 'turns', 'event', 'event_type', 'points_event')


class MyResultForm(forms.ModelForm):
    first = forms.BooleanField(label="starting player", required=False)
    points = forms.IntegerField(label="Small points (VP auto-calculated)", required=True)

    class Meta:
        model = Results
        fields = ('first', 'points', 'secondary', 'list', 'comment')


class OpResultForm(forms.ModelForm):
    points = forms.IntegerField(label="Small points (VP auto-calculated)", required=True)

    class Meta:
        model = Results
        fields = ('player', 'points')


class MyHalfResultForm(forms.ModelForm):
    class Meta:
        model = HalfResults
        fields = ('list', 'comment')


class OpHalfResultForm(forms.ModelForm):
    class Meta:
        model = HalfResults
        fields = ('player',)


class AddListToResultForm(forms.ModelForm):
    class Meta:
        model = HalfResults
        fields = ('list',)


class UnitsPointsForm(forms.ModelForm):
    class Meta:
        model = UnitsPoints
        fields = ('points_percentage', 'points_special', 'unit')


class AddListForm(forms.ModelForm):
    class Meta:
        model = Lists
        fields = ('army', 'name', 'uses_supplement', 'list')


class ApproveResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ('approved', 'list', 'comment')


class AddGamingGroupForm(forms.ModelForm):
    class Meta:
        model = GamingGroup
        fields = ('name', 'comment')
