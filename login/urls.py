from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.AcademiaLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("perfil/", views.perfil, name="perfil"),
    path("alterar-senha/", auth_views.PasswordChangeView.as_view(
        template_name="alterar_senha.html",
        success_url=reverse_lazy("perfil"),
    ), name="alterar-senha"),

    path("senha/esqueceu/", auth_views.PasswordResetView.as_view(
        template_name="password_reset_form.html",
        email_template_name="password_reset_email.txt",
        subject_template_name="password_reset_subject.txt",
        success_url=reverse_lazy("password_reset_done"),
    ), name="password_reset"),
    path("senha/enviada/", auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_done.html",
    ), name="password_reset_done"),
    path("senha/redefinir/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ), name="password_reset_confirm"),
    path("senha/concluida/", auth_views.PasswordResetCompleteView.as_view(
        template_name="password_reset_complete.html",
    ), name="password_reset_complete"),

    path("cadastro/", views.cadastro, name="cadastro"),




]
