from django.urls import path
from . import views

urlpatterns = [
    path('', views.novo_contato, name='novo_contato'),
    path('gerenciar/', views.lista_contatos, name='lista_contatos'),
    path('<int:id_contato>/excluir/', views.excluir_contato, name='excluir_contato'),
]
