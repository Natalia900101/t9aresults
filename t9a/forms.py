from django import forms
from django.contrib.auth import get_user_model

from t9a.models import Games, Results


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
        fields = '__all__'


class MyResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ('first', 'points', 'secondary', 'list', 'comment')


class OpResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ('player', 'points', 'list')
