import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from analise.services import criar_dataset_demanda


def criar_dataset_produtos_kmeans():
    """
    Cria um dataset com uma linha por produto.

    Cada linha representa o comportamento histórico
    de demanda daquele produto.
    """

    demanda = criar_dataset_demanda()

    if demanda.empty:
        return demanda

    dataset = (
        demanda
        .groupby("produto_nome")
        .agg(
            demanda_total=("quantidade", "sum"),
            demanda_media=("quantidade", "mean"),
            desvio_padrao=("quantidade", "std"),
            demanda_maxima=("quantidade", "max"),
            dias_com_demanda=(
                "quantidade",
                lambda x: (x > 0).sum()
            ),
            percentual_dias_zero=(
                "quantidade",
                lambda x: (x == 0).mean()
            ),
            percentil_75=(
                "quantidade",
                lambda x: x.quantile(0.75)
            ),
        )
        .reset_index()
    )

    dataset["desvio_padrao"] = (
        dataset["desvio_padrao"].fillna(0)
    )

    return dataset


def avaliar_kmeans(
    dataset,
    k_min=2,
    k_max=6,
):
    """
    Testa diferentes quantidades de clusters
    usando o Silhouette Score.
    """

    features = [
        "demanda_media",
        "desvio_padrao",
        "demanda_maxima",
        "dias_com_demanda",
        "percentual_dias_zero",
        "percentil_75",
    ]

    X = dataset[features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    resultados = []

    limite = min(
        k_max,
        len(dataset) - 1
    )

    for k in range(k_min, limite + 1):

        modelo = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=20,
        )

        labels = modelo.fit_predict(X_scaled)

        silhouette = silhouette_score(
            X_scaled,
            labels,
        )

        resultados.append({
            "k": k,
            "silhouette_score": silhouette,
        })

    return pd.DataFrame(resultados)


def treinar_kmeans(
    dataset,
    n_clusters=None,
):
    """
    Treina o K-Means.

    Quando n_clusters não é informado,
    utiliza o K com maior Silhouette Score.
    """

    features = [
        "demanda_media",
        "desvio_padrao",
        "demanda_maxima",
        "dias_com_demanda",
        "percentual_dias_zero",
        "percentil_75",
    ]

    avaliacao = avaliar_kmeans(dataset)

    if n_clusters is None:
        n_clusters = int(
            avaliacao.loc[
                avaliacao["silhouette_score"].idxmax(),
                "k"
            ]
        )

    X = dataset[features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modelo = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=20,
    )

    clusters = modelo.fit_predict(X_scaled)

    resultado = dataset.copy()

    resultado["cluster"] = clusters

    silhouette = silhouette_score(
        X_scaled,
        clusters,
    )

    return {
        "dataset": resultado,
        "features": features,
        "scaler": scaler,
        "modelo": modelo,
        "n_clusters": n_clusters,
        "silhouette_score": silhouette,
        "avaliacao": avaliacao,
    }

def criar_visualizacao_clusters(resultado_kmeans):
    """
    Cria coordenadas em duas dimensões usando PCA
    para visualização dos clusters.
    """

    dataset = resultado_kmeans["dataset"].copy()

    features = resultado_kmeans["features"]
    scaler = resultado_kmeans["scaler"]

    X = dataset[features]

    X_scaled = scaler.transform(X)

    pca = PCA(
        n_components=2,
        random_state=42,
    )

    coordenadas = pca.fit_transform(X_scaled)

    dataset["pca_1"] = coordenadas[:, 0]
    dataset["pca_2"] = coordenadas[:, 1]

    return dataset, pca