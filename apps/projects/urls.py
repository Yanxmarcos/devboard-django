from django.urls import path

from .views import (
    MemberAddView,
    MemberRemoveView,
    MemberRoleUpdateView,
    ProjectCreateView,
    ProjectDeleteView,
    ProjectDetailView,
    ProjectListView,
    ProjectUpdateView,
)

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("new/", ProjectCreateView.as_view(), name="project_create"),
    path("<slug:slug>/", ProjectDetailView.as_view(), name="project_detail"),
    path("<slug:slug>/edit/", ProjectUpdateView.as_view(), name="project_update"),
    path("<slug:slug>/delete/", ProjectDeleteView.as_view(), name="project_delete"),
    path("<slug:slug>/members/add/", MemberAddView.as_view(), name="member_add"),
    path("<slug:slug>/members/<int:pk>/role/", MemberRoleUpdateView.as_view(), name="member_role_update"),
    path("<slug:slug>/members/<int:pk>/remove/", MemberRemoveView.as_view(), name="member_remove"),
]
