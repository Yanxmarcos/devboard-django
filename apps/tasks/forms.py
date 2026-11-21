from django import forms

from .models import Comment, Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "status", "priority", "assignee", "due_date")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project:
            from django.contrib.auth.models import User

            self.fields["assignee"].queryset = User.objects.filter(
                project_memberships__project=project
            ).distinct()
            self.fields["assignee"].empty_label = "Sin asignar"

    def clean_assignee(self):
        assignee = self.cleaned_data.get("assignee")
        if assignee and self.project and not self.project.memberships.filter(user=assignee).exists():
            raise forms.ValidationError("La persona asignada debe pertenecer al proyecto.")
        return assignee


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        labels = {"body": "Comentario"}
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Escribe una actualización…"})}
