from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0002_movimentacao_historico_analitico'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='categoria',
            options={'ordering': ['nome']},
        ),
        migrations.AlterField(
            model_name='categoria',
            name='nome',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='produto',
            name='categoria',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='produtos',
                to='estoque.categoria',
            ),
        ),
        migrations.AlterField(
            model_name='produto',
            name='unidade',
            field=models.CharField(
                choices=[
                    ('un', 'Unidade'),
                    ('cx', 'Caixa'),
                    ('pct', 'Pacote'),
                    ('g', 'Grama'),
                    ('kg', 'Quilograma'),
                    ('ml', 'Mililitro'),
                    ('l', 'Litro'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='produto',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimentacoes',
                to='estoque.produto',
            ),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='produto_nome',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='categoria_nome',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='unidade',
            field=models.CharField(
                choices=[
                    ('un', 'Unidade'),
                    ('cx', 'Caixa'),
                    ('pct', 'Pacote'),
                    ('g', 'Grama'),
                    ('kg', 'Quilograma'),
                    ('ml', 'Mililitro'),
                    ('l', 'Litro'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='tipo',
            field=models.CharField(
                choices=[('entrada', 'Entrada'), ('saida', 'Saida')],
                db_index=True,
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='data',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AddConstraint(
            model_name='produto',
            constraint=models.UniqueConstraint(
                fields=('nome', 'categoria'),
                name='estoque_produto_unico_por_categoria',
            ),
        ),
        migrations.AddIndex(
            model_name='movimentacao',
            index=models.Index(fields=['data', 'tipo'], name='estoque_mov_data_tipo'),
        ),
        migrations.AddIndex(
            model_name='movimentacao',
            index=models.Index(fields=['produto', 'data'], name='estoque_mov_produto_data'),
        ),
        migrations.AddIndex(
            model_name='movimentacao',
            index=models.Index(fields=['categoria_nome', 'data'], name='estoque_mov_categ_data'),
        ),
    ]
