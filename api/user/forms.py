from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Ensure the password is hashed
        user.set_password(self.cleaned_data["password1"])
        
        if commit:
            user.save()
        return user
