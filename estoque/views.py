from django.shortcuts import render, redirect
from django.db.models import Sum
from .forms import CategoriaForm, ProdutoForm
from .models import Produto, Categoria

# Error handling views
def page_not_found(request, exception):
    return render(request, '404.html', status=404)

def server_error(request):
    return render(request, '500.html', status=500)

def permission_denied(request, exception):
    return render(request, '401.html', status=401)

# Main pages
def index(request):
    produtos = Produto.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'base.html', {'produtos': produtos, 'categorias': categorias})

def charts(request):
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()

    # Prepare data for charts
    category_names = [categoria.nome for categoria in categorias]
    product_quantities = [
        produtos.filter(categoria=categoria).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
        for categoria in categorias
    ]
    stock_values = [
        float(sum(produto.quantidade * produto.preco for produto in produtos.filter(categoria=categoria)))
        for categoria in categorias
    ]

    return render(request, 'charts.html', {
        'categorias': category_names,
        'product_quantities': product_quantities,
        'stock_values': stock_values
    })

def tables(request):
    produtos = Produto.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'tables.html', {'produtos': produtos, 'categorias': categorias})

# Form handling
def add_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tables')
    else:
        form = CategoriaForm()
    return render(request, 'add_categoria.html', {'form': form})

def add_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tables')
    else:
        form = ProdutoForm()
    return render(request, 'add_produto.html', {'form': form})

def remover_produto(request):
    if request.method == 'POST':
        produto_id = request.POST.get('produto')
        remover_tudo = request.POST.get('remover_tudo') == 'on'
        produto = Produto.objects.get(id=produto_id)

        if remover_tudo:
            produto.delete()
        else:
            quantidade = int(request.POST.get('quantidade', 0))
            if produto.quantidade >= quantidade:
                produto.quantidade -= quantidade
                produto.save()
            else:
                error_message = f"A quantidade disponível de {produto.nome} é insuficiente. Reduza a quantidade."
                produtos = Produto.objects.all()
                categorias = Categoria.objects.all()
                return render(request, 'tables.html', {
                    'produtos': produtos,
                    'categorias': categorias,
                    'error_message': error_message
                })

        return redirect('tables')

def remover_categoria(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        Categoria.objects.filter(id=categoria_id).delete()
        return redirect('tables')

def editar_categoria(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        novo_nome = request.POST.get('nome')
        categoria = Categoria.objects.get(id=categoria_id)
        categoria.nome = novo_nome
        categoria.save()
        return redirect('tables')

def editar_produto(request):
    if request.method == 'POST':
        produto_id = request.POST.get('produto')
        produto = Produto.objects.get(id=produto_id)
        produto.nome = request.POST.get('nome')
        produto.categoria_id = request.POST.get('categoria')
        produto.preco = request.POST.get('preco')
        produto.unidade = request.POST.get('unidade')
        produto.save()
        return redirect('tables')