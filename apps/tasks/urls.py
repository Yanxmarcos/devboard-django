from django.urls import path

from .views import (
    CommentCreateView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskStatusView,
    TaskUpdateView,
)

urlpatterns = [
    path("project/<slug:slug>/new/", TaskCreateView.as_view(), name="task_create"),
    path("<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="task_update"),
    path("<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("<int:pk>/status/", TaskStatusView.as_view(), name="task_status"),
    path("<int:pk>/comments/", CommentCreateView.as_view(), name="comment_create"),
]
