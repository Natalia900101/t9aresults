from django import forms
from django.contrib.auth import get_user_model

from t9a.models import Games, Results, Lists


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
    first = forms.BooleanField(label="starting player",required=False)
    class Meta:
        model = Results
        fields = ('first', 'points', 'secondary', 'list', 'comment')


class OpResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ('player', 'points')


class AddListForm(forms.ModelForm):
    class Meta:
        model = Lists
        fields = ('army', 'name', 'uses_supplement', 'list')


class ApproveResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ('approved', 'list', 'comment')
