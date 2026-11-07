from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from login.permissions import admin_required
from .models import Contato
from .forms import ContatoForm

def novo_contato(request):
    if request.method == 'POST':
        form = ContatoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sua mensagem foi enviada.')
            return redirect('novo_contato')
    else:
        form = ContatoForm()
    return render(request, 'novo_contato.html', {'form': form})


@admin_required
def lista_contatos(request):
    contatos = Contato.objects.all().order_by("-id")
    return render(request, "contatos.html", {"contatos": contatos})


@admin_required
@require_POST
def excluir_contato(request, id_contato):
    contato = get_object_or_404(Contato, id=id_contato)
    contato.delete()
    messages.success(request, "Mensagem excluída.")
    return redirect("lista_contatos")
