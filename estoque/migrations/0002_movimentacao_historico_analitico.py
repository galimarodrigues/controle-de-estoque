from django.db import migrations, models
import django.db.models.deletion


def preencher_dados_movimentacao(apps, schema_editor):
    Movimentacao = apps.get_model('estoque', 'Movimentacao')

    for movimentacao in Movimentacao.objects.select_related('produto', 'produto__categoria'):
        produto = movimentacao.produto
        if produto is not None:
            movimentacao.produto_nome = produto.nome
            movimentacao.categoria_nome = produto.categoria.nome
            movimentacao.unidade = (produto.unidade or 'un').strip().lower()
            movimentacao.custo_unitario = produto.preco
        else:
            movimentacao.produto_nome = movimentacao.produto_nome or 'Produto removido'
            movimentacao.categoria_nome = movimentacao.categoria_nome or 'Sem categoria'
            movimentacao.unidade = (movimentacao.unidade or 'un').strip().lower()
        movimentacao.save(update_fields=[
            'produto_nome',
            'categoria_nome',
            'unidade',
            'custo_unitario',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimentacao',
            name='categoria_nome',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='custo_unitario',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='fornecedor',
            field=models.CharField(blank=True, default='', max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='motivo',
            field=models.CharField(blank=True, default='', max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='observacao',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='produto_nome',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='unidade',
            field=models.CharField(default='un', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='produto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='estoque.produto'),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='tipo',
            field=models.CharField(choices=[('entrada', 'Entrada'), ('saida', 'Saida')], max_length=10),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user'),
        ),
        migrations.AlterModelOptions(
            name='movimentacao',
            options={'ordering': ['-data', '-id']},
        ),
        migrations.RunPython(preencher_dados_movimentacao, migrations.RunPython.noop),
    ]
