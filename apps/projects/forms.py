from django import forms
from django.contrib.auth.models import User

from .models import Project, ProjectMembership


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "color")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "color": forms.TextInput(attrs={"type": "color"}),
        }


class MemberForm(forms.Form):
    identifier = forms.CharField(
        max_length=150,
        label="Usuario o correo",
        help_text="Escribe el nombre de usuario o correo de una cuenta existente.",
    )
    role = forms.ChoiceField(
        choices=[
            (ProjectMembership.Role.COLLABORATOR, "Colaborador"),
            (ProjectMembership.Role.VIEWER, "Observador"),
        ]
    )

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            raise forms.ValidationError("No encontramos una cuenta con esos datos.")
        self.user = user
        return identifier


class MemberRoleForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ("role",)
        widgets = {"role": forms.Select(attrs={"aria-label": "Rol del miembro"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (ProjectMembership.Role.COLLABORATOR, "Colaborador"),
            (ProjectMembership.Role.VIEWER, "Observador"),
        ]
