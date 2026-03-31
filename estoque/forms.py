from django import forms

from .models import Categoria, Produto, UNIDADES_VALIDAS, normalizar_nome_categoria, normalizar_unidade


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

    def clean_nome(self):
        nome = normalizar_nome_categoria(self.cleaned_data['nome'])
        queryset = Categoria.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ja existe uma categoria com este nome.')
        return nome


class ProdutoForm(forms.ModelForm):
    quantidade_inicial = forms.IntegerField(min_value=0, required=False, initial=0)
    motivo = forms.CharField(max_length=120, required=False, initial='Estoque inicial')
    fornecedor = forms.CharField(max_length=120, required=False)
    observacao = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'preco', 'unidade']

    def clean_unidade(self):
        unidade = normalizar_unidade(self.cleaned_data['unidade'])
        unidades_validas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if unidade not in unidades_validas:
            raise forms.ValidationError('Selecione uma unidade padronizada valida.')
        return unidade


class EditCategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

    def clean_nome(self):
        nome = normalizar_nome_categoria(self.cleaned_data['nome'])
        queryset = Categoria.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ja existe uma categoria com este nome.')
        return nome


class EditProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'preco', 'unidade']

    def clean_unidade(self):
        unidade = normalizar_unidade(self.cleaned_data['unidade'])
        unidades_validas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if unidade not in unidades_validas:
            raise forms.ValidationError('Selecione uma unidade padronizada valida.')
        return unidade


class MovimentacaoForm(forms.Form):
    produto = forms.ModelChoiceField(queryset=Produto.objects.none())
    quantidade = forms.IntegerField(min_value=1)
    custo_unitario = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    motivo = forms.CharField(max_length=120, required=False)
    fornecedor = forms.CharField(max_length=120, required=False)
    observacao = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.select_related('categoria').order_by('nome')
