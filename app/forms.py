from django import forms
from django.core.exceptions import ValidationError

from .models import Servico


class FormServico(forms.ModelForm):
    imagem_upload = forms.ImageField(
        required=False,
        label="Imagem do curso (JPG, PNG ou WEBP; até 2 MB)",
    )
    limpar_imagem = forms.BooleanField(
        required=False,
        label="Remover a imagem atual",
    )

    class Meta:
        model = Servico
        fields = ("nome", "descricao", "preco", "categoria", "ativo")
        labels = {
            "nome": "Nome do curso",
            "descricao": "Descrição",
            "preco": "Preço (R$)",
            "categoria": "Categoria",
            "ativo": "Curso ativo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = True
        self.fields["imagem_upload"].widget.attrs["accept"] = ".jpg,.jpeg,.png,.webp"
        if not self.instance.pk:
            self.fields.pop("limpar_imagem")

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco <= 0:
            raise forms.ValidationError("Informe um preço maior que zero.")
        return preco

    def clean_imagem_upload(self):
        imagem = self.cleaned_data.get("imagem_upload")
        if not imagem:
            return imagem

        if imagem.size > 2 * 1024 * 1024:
            raise forms.ValidationError("A imagem deve ter no máximo 2 MB.")

        formato = getattr(getattr(imagem, "image", None), "format", "")
        if formato not in {"JPEG", "PNG", "WEBP"}:
            raise forms.ValidationError("Envie uma imagem JPG, PNG ou WEBP válida.")

        imagem.seek(0)
        return imagem

    def save(self, commit=True):
        curso = super().save(commit=False)
        imagem_enviada = self.cleaned_data.get("imagem_upload")

        if imagem_enviada:
            from .storage import upload_imagem_curso

            try:
                curso.imagem = upload_imagem_curso(imagem_enviada)
            except Exception as exc:
                raise ValidationError(
                    "Não foi possível enviar a imagem ao Supabase Storage. "
                    "Confira as configurações e tente novamente."
                ) from exc
        elif self.cleaned_data.get("limpar_imagem"):
            curso.imagem = ""

        if commit:
            curso.save()
            self.save_m2m()
        return curso
