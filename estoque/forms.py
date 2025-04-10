from django import forms
from .models import Produto, Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'preco', 'quantidade', 'unidade']

class EditCategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

class EditProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'preco', 'unidade']