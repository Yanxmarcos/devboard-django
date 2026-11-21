from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView

from .forms import ProfileUpdateForm, SignUpForm, UserUpdateForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Tu cuenta fue creada correctamente.")
        return response

    def get_success_url(self):
        return "/dashboard/"


class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "user_form": UserUpdateForm(instance=request.user),
                "profile_form": ProfileUpdateForm(instance=request.user.profile),
            },
        )

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Tu perfil fue actualizado.")
            return redirect("profile")
        return render(
            request,
            self.template_name,
            {"user_form": user_form, "profile_form": profile_form},
        )
