from django.shortcuts import render

from analise.clustering import (
    criar_dataset_produtos_kmeans,
    treinar_kmeans,
    criar_visualizacao_clusters,
)


def dashboard_analise(request):
    """
    Dashboard de análise de comportamento dos produtos
    utilizando K-Means.
    """

    # -------------------------------------------------
    # 1. Criar dataset dos produtos
    # -------------------------------------------------

    dataset_produtos = criar_dataset_produtos_kmeans()

    features = [
        "demanda_media", "desvio_padrao", "demanda_maxima",
        "dias_com_demanda", "percentual_dias_zero", "percentil_75",
    ]
    if dataset_produtos.empty:
        return render(request, "analise.html", {
            "mensagem_analise": "Ainda não há movimentações de saída para analisar."
        })
    if len(dataset_produtos) < 3 or len(dataset_produtos[features].drop_duplicates()) < 2:
        return render(request, "analise.html", {
            "mensagem_analise": "São necessários pelo menos três produtos com demanda e dois perfis diferentes para gerar a análise."
        })

    # -------------------------------------------------
    # 2. Treinar K-Means
    # -------------------------------------------------

    resultado_kmeans = treinar_kmeans(
        dataset_produtos,
        n_clusters=2,
    )

    # -------------------------------------------------
    # 3. Preparar coordenadas para o gráfico
    # -------------------------------------------------

    dataset_pca, pca = criar_visualizacao_clusters(
        resultado_kmeans
    )

    # -------------------------------------------------
    # 4. Identificar qual cluster representa
    #    maior e menor frequência de demanda
    # -------------------------------------------------

    media_por_cluster = (
        dataset_pca
        .groupby("cluster")["demanda_media"]
        .mean()
        .sort_values(ascending=False)
    )

    cluster_frequente = int(
        media_por_cluster.index[0]
    )

    cluster_intermitente = int(
        media_por_cluster.index[-1]
    )

    nomes_clusters = {
        cluster_frequente: "Demanda frequente",
        cluster_intermitente: "Demanda intermitente",
    }

    # -------------------------------------------------
    # 5. Preparar pontos do gráfico
    # -------------------------------------------------

    pontos_clusters = []

    for cluster in sorted(
        dataset_pca["cluster"].unique()
    ):
        dados_cluster = dataset_pca[
            dataset_pca["cluster"] == cluster
        ]

        pontos = []

        for _, produto in dados_cluster.iterrows():
            pontos.append({
                "x": round(float(produto["pca_1"]), 3),
                "y": round(float(produto["pca_2"]), 3),
                "produto": produto["produto_nome"],
            })

        pontos_clusters.append({
            "cluster": int(cluster),
            "nome": nomes_clusters[int(cluster)],
            "pontos": pontos,
        })

    # -------------------------------------------------
    # 6. Preparar tabela de produtos
    # -------------------------------------------------

    produtos = []

    for _, produto in (
        dataset_pca
        .sort_values(
            ["cluster", "demanda_media"],
            ascending=[True, False],
        )
        .iterrows()
    ):
        produtos.append({
            "nome": produto["produto_nome"],
            "cluster": int(produto["cluster"]),
            "cluster_nome": nomes_clusters[
                int(produto["cluster"])
            ],
            "demanda_media": round(
                float(produto["demanda_media"]),
                2,
            ),
            "demanda_total": round(
                float(produto["demanda_total"]),
                0,
            ),
            "dias_com_demanda": int(
                produto["dias_com_demanda"]
            ),
            "percentual_dias_zero": round(
                float(
                    produto["percentual_dias_zero"]
                ) * 100,
                1,
            ),
        })

    # -------------------------------------------------
    # 7. Contexto do dashboard
    # -------------------------------------------------

    contexto = {
        "cluster_nome_0": nomes_clusters.get(0, ""),
        "cluster_nome_1": nomes_clusters.get(1, ""),
        "total_produtos": len(dataset_pca),
        "n_clusters": resultado_kmeans["n_clusters"],
        "silhouette_score": round(
            float(
                resultado_kmeans[
                    "silhouette_score"
                ]
            ),
            4,
        ),
        "variancia_pca": round(
            float(
                pca.explained_variance_ratio_.sum()
            ) * 100,
            2,
        ),
        "pca_1_percentual": round(
            float(
                pca.explained_variance_ratio_[0]
            ) * 100,
            2,
        ),
        "pca_2_percentual": round(
            float(
                pca.explained_variance_ratio_[1]
            ) * 100,
            2,
        ),
        "pontos_clusters": pontos_clusters,
        "produtos": produtos,
    }

    return render(
        request,
        "analise.html",
        contexto,
    )