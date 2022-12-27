from django import forms
from django.contrib.auth import get_user_model


class UsernameForm(forms.ModelForm):
    username = forms.CharField(label='Username')
    new_username = forms.CharField(label='New username')

    class Meta:
        model = get_user_model()
        fields = ('username',)


