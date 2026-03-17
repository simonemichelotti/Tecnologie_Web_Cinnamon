from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    cuisine_specialties = forms.MultipleChoiceField(
        choices=UserProfile.CUISINE_SPECIALTIES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Specialità Culinarie"
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_image', 
            'bio', 
            'experience_level', 
            'cuisine_specialties',
            'culinary_interests',
            'location',
            'birth_date',
            'is_public',
            'show_email'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Raccontaci qualcosa su di te...'}),
            'culinary_interests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'I tuoi interessi gastronomici...'}),
            'location': forms.TextInput(attrs={'placeholder': 'Città, Paese'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.cuisine_specialties:
            self.fields['cuisine_specialties'].initial = self.instance.cuisine_specialties