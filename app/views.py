import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from login.permissions import admin_required, client_required, is_admin_user
from .models import Categoria, ItemPedido, Pedido, Servico
from .forms import FormServico
from .permissions import ReadOnlyOrAdmin
from .serializers import CategoriaSerializer
from .services import get_equipamentos_parceiros
from .storage import excluir_imagem_curso
from .supabase_client import get_supabase


logger = logging.getLogger(__name__)

def index(request):
    return render(request, "index.html")


def _tentar_excluir_imagem(url):
    if not url:
        return
    try:
        excluir_imagem_curso(url)
    except Exception:
        logger.warning("Não foi possível limpar uma imagem antiga no Supabase Storage.", exc_info=True)


@admin_required
def servicos(request):
    pode_gerenciar = True
    servicos = Servico.objects.all().select_related("categoria")
    busca = request.GET.get('busca')

    if busca:
        servicos = servicos.filter(nome__icontains=busca)

    categorias = Categoria.objects.filter(ativo=True)
    categoria = request.GET.get('categoria')

    if categoria and categoria.isdigit():
        servicos = servicos.filter(categoria_id=categoria)

    preco = request.GET.get('preco')

    if preco == 'baixo':
        servicos = servicos.filter(preco__lte=500)
    elif preco == 'medio':
        servicos = servicos.filter(preco__gt=500, preco__lte=1500)
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=1500)

    ordem = request.GET.get('ordem')

    if ordem == 'menor':
        servicos = servicos.order_by('preco')
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco')
    else:
        servicos = servicos.order_by('nome')

    total_servicos = servicos.count()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = servicos.filter(ativo=False).count()
    tem_servicos = servicos.exists()
    mais_barato = servicos.order_by('preco').first()
    mais_caro = servicos.order_by('-preco').first()

    contexto = {
        'servicos': servicos,
        'total_servicos': total_servicos,
        'servicos_ativos': servicos_ativos,
        'servicos_inativos': servicos_inativos,
        'tem_servicos': tem_servicos,
        'mais_barato': mais_barato,
        'mais_caro': mais_caro,
        'busca': busca,
        'categorias': categorias,
        'categoria': categoria,
        'preco': preco,
        'ordem': ordem,
        'pode_gerenciar': pode_gerenciar,
    }

    return render(request, "servicos.html", contexto)


@admin_required
def addServico(request):
    form = FormServico(request.POST or None, request.FILES)

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
            except ValidationError as exc:
                form.add_error("imagem_upload", exc)
            else:
                messages.success(request, "Curso cadastrado com sucesso.")
                return redirect('servicos')

    return render(request, "add-servico.html", {'form': form})

@admin_required
@require_POST
def delServico(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    imagem_antiga = servico.imagem
    servico.delete()
    _tentar_excluir_imagem(imagem_antiga)
    messages.success(request, "Curso excluído.")
    return redirect('servicos')

@admin_required
def editServico(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    imagem_antiga = servico.imagem
    form = FormServico(request.POST or None, request.FILES, instance=servico)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
            except ValidationError as exc:
                form.add_error("imagem_upload", exc)
            else:
                if imagem_antiga and imagem_antiga != servico.imagem:
                    _tentar_excluir_imagem(imagem_antiga)
                messages.success(request, "Curso atualizado com sucesso.")
                return redirect('servicos')
    return render(request, "edit-servico.html", {"form": form, "servico": servico})

def produtos(request):
    servicos = Servico.objects.filter(ativo=True).select_related("categoria")
    produtos_api, api_erro = get_equipamentos_parceiros()

    return render(request, "produtos.html", {
        "servicos": servicos,
        "produtos_api": produtos_api,
        "api_erro": api_erro,
        "pode_comprar": request.user.is_authenticated and not is_admin_user(request.user),
        "observacao_cotacao": "Valores convertidos de USD para BRL pela cotação do dia.",
    })


@admin_required
def relatorios(request):
    servicos = Servico.objects.all()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = servicos.filter(ativo=False).count()
    categorias = servicos.values("categoria__nome").annotate(
        quantidade=Count("id")
    ).order_by("categoria__nome")

    return render(request, "relatorio.html", {
        "servicos_ativos": servicos_ativos,
        "servicos_inativos": servicos_inativos,
        "total_servicos": servicos_ativos + servicos_inativos,
        "categorias_labels": [
            item["categoria__nome"] or "Sem categoria" for item in categorias
        ],
        "categorias_valores": [item["quantidade"] for item in categorias],
    })


def _integrantes_context(request):
    try:
        resposta = get_supabase().table("integrantes").select("*").order("id").execute()
        return {
            "integrantes": resposta.data or [],
            "pode_gerenciar": is_admin_user(request.user),
            "supabase_erro": False,
        }
    except Exception:
        logger.exception("Falha ao consultar integrantes no Supabase.")
        return {
            "integrantes": [],
            "pode_gerenciar": is_admin_user(request.user),
            "supabase_erro": True,
        }


@admin_required
def integrantes(request):
    return render(request, "integrantes.html", _integrantes_context(request))


def quem_somos(request):
    return render(request, "quem-somos.html", _integrantes_context(request))


@admin_required
def addIntegrante(request):
    if request.method == "POST":
        dados = {
            "nome": request.POST.get("nome", "").strip(),
            "cargo": request.POST.get("cargo", "").strip(),
            "biografia": request.POST.get("biografia", "").strip(),
            "foto_url": request.POST.get("foto", "").strip() or None,
        }
        if not dados["nome"] or not dados["cargo"] or not dados["biografia"]:
            messages.error(request, "Preencha nome, cargo e biografia.")
        else:
            try:
                get_supabase().table("integrantes").insert(dados).execute()
            except Exception:
                logger.exception("Falha ao cadastrar integrante no Supabase.")
                messages.error(request, "Não foi possível salvar agora. Verifique a conexão com a equipe remota.")
            else:
                messages.success(request, "Integrante cadastrado com sucesso.")
                return redirect("integrantes")

    return render(request, "add-integrante.html")


@admin_required
@require_POST
def delIntegrante(request, id_integrante):
    try:
        get_supabase().table("integrantes").delete().eq("id", id_integrante).execute()
    except Exception:
        logger.exception("Falha ao excluir integrante no Supabase.")
        messages.error(request, "Não foi possível excluir agora. Verifique a conexão com a equipe remota.")
    else:
        messages.success(request, "Integrante excluído.")
    return redirect("integrantes")


@admin_required
def editIntegrante(request, id_integrante):
    try:
        supabase = get_supabase()
        registros = (
            supabase.table("integrantes")
            .select("*")
            .eq("id", id_integrante)
            .execute()
            .data
            or []
        )
    except Exception:
        logger.exception("Falha ao consultar integrante no Supabase.")
        messages.error(request, "Não foi possível consultar a equipe remota agora.")
        return redirect("integrantes")
    if not registros:
        raise Http404("Integrante não encontrado.")

    integrante = registros[0]
    if request.method == "POST":
        dados = {
            "nome": request.POST.get("nome", "").strip(),
            "cargo": request.POST.get("cargo", "").strip(),
            "biografia": request.POST.get("biografia", "").strip(),
            "foto_url": request.POST.get("foto", "").strip() or None,
        }
        if not dados["nome"] or not dados["cargo"] or not dados["biografia"]:
            messages.error(request, "Preencha nome, cargo e biografia.")
        else:
            try:
                supabase.table("integrantes").update(dados).eq("id", id_integrante).execute()
            except Exception:
                logger.exception("Falha ao atualizar integrante no Supabase.")
                messages.error(request, "Não foi possível atualizar agora. Verifique a conexão com a equipe remota.")
            else:
                messages.success(request, "Integrante atualizado com sucesso.")
                return redirect("integrantes")
        integrante = {**integrante, **dados}

    return render(request, "edit-integrante.html", {"integrante": integrante})


@client_required
@require_POST
def adicionar_ao_carrinho(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico, ativo=True)
    pedido, _ = Pedido.objects.get_or_create(
        usuario=request.user,
        status=Pedido.Status.CARRINHO,
    )
    item, criado = ItemPedido.objects.get_or_create(
        pedido=pedido,
        servico=servico,
        defaults={
            "quantidade": 1,
            "preco_unitario": servico.preco,
            "nome_servico": servico.nome,
            "imagem_url": servico.imagem,
        },
    )
    if not criado:
        item.quantidade += 1
        item.save(update_fields=["quantidade"])
    messages.success(request, f"{servico.nome} foi adicionado ao seu carrinho.")
    return redirect("produtos")


@client_required
def meus_pedidos(request):
    pedidos = (
        Pedido.objects.filter(usuario=request.user)
        .prefetch_related("itens__servico")
        .order_by("-criado_em")
    )
    return render(request, "meus-pedidos.html", {"pedidos": pedidos})


@client_required
@require_POST
def finalizar_pedido(request):
    pedido = get_object_or_404(
        Pedido,
        usuario=request.user,
        status=Pedido.Status.CARRINHO,
    )
    if not pedido.itens.exists():
        messages.error(request, "Adicione pelo menos um produto antes de finalizar o pedido.")
    else:
        pedido.status = Pedido.Status.REALIZADO
        pedido.save(update_fields=["status", "atualizado_em"])
        messages.success(request, "Pedido realizado com sucesso.")
    return redirect("meus-pedidos")


@client_required
@require_POST
def remover_item_pedido(request, id_item):
    item = get_object_or_404(
        ItemPedido,
        id=id_item,
        pedido__usuario=request.user,
        pedido__status=Pedido.Status.CARRINHO,
    )
    item.delete()
    messages.success(request, "Produto removido do carrinho.")
    return redirect("meus-pedidos")


@api_view(["GET", "POST"])
@permission_classes([ReadOnlyOrAdmin])
def categoriasAPI(request):
    if request.method == "GET":
        serializer = CategoriaSerializer(Categoria.objects.all(), many=True)
        return Response(serializer.data)

    serializer = CategoriaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def categoriasStatusAPI(request):
    categorias = Categoria.objects.annotate(
        quantidade_servicos=Count("servicos"),
        servicos_ativos=Count("servicos", filter=Q(servicos__ativo=True)),
        servicos_inativos=Count("servicos", filter=Q(servicos__ativo=False)),
    ).values(
        "id",
        "nome",
        "ativo",
        "quantidade_servicos",
        "servicos_ativos",
        "servicos_inativos",
    ).order_by("nome")

    return Response(list(categorias))


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([ReadOnlyOrAdmin])
def categoriaAPI(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)

    if request.method == "GET":
        return Response(CategoriaSerializer(categoria).data)
    if request.method == "DELETE":
        categoria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CategoriaSerializer(categoria, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
