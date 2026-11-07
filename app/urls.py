from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("quem-somos/", views.quem_somos, name="quem_somos"),
    path("servicos", views.servicos, name="servicos"),
    path("add-servico", views.addServico, name="addServico"),
    path("del-servico/<int:id_servico>", views.delServico, name="delServico"),
    path("edit-servico/<int:id_servico>", views.editServico, name="editServico"),
    path('produtos/', views.produtos, name='produtos'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path("carrinho/adicionar/<int:id_servico>/", views.adicionar_ao_carrinho, name="adicionar_ao_carrinho"),
    path("meus-pedidos/", views.meus_pedidos, name="meus-pedidos"),
    path("pedidos/finalizar/", views.finalizar_pedido, name="finalizar_pedido"),
    path("carrinho/item/<int:id_item>/remover/", views.remover_item_pedido, name="remover_item_pedido"),
    path("integrantes/", views.integrantes, name="integrantes"),
    path("integrantes/adicionar/", views.addIntegrante, name="addIntegrante"),
    path("integrantes/<int:id_integrante>/editar/", views.editIntegrante, name="editIntegrante"),
    path("integrantes/<int:id_integrante>/excluir/", views.delIntegrante, name="delIntegrante"),
    path("categoria-api/", views.categoriasAPI, name="categoriasAPI"),
    path("categoria-api/<int:id_categoria>/", views.categoriaAPI, name="categoriaAPI"),
    path("categoria-status/", views.categoriasStatusAPI, name="categoriasStatusAPI"),

]
