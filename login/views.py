from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import CadastroForm, PerfilForm
from .models import Perfil
from .permissions import is_admin_user


class AcademiaLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        if is_admin_user(self.request.user):
            return reverse("admin:index")
        return super().get_success_url()


@login_required
def dashboard(request):
    if is_admin_user(request.user):
        return redirect("admin:index")

    return render(request, "dashboard.html")

@login_required
@login_required
def perfil(request):
    form = PerfilForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Seus dados foram atualizados.")
            return redirect("perfil")

    return render(request, "perfil.html", {"form": form})

def cadastro(request):
    if request.method == "POST":
        form = CadastroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            Perfil.objects.create(usuario=usuario, tipo_usuario='cliente')
            messages.success(request, "Conta criada. Agora você já pode entrar.")
            return redirect('login')
    else:
        form = CadastroForm()

    return render(request, "cadastro.html", {'form': form})
