import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder


FEATURES_NUMERICAS = [
    "dia_semana",
    "fim_de_semana",
    "mes",
    "dia_mes",
    "demanda_lag_1",
    "demanda_lag_7",
    "media_7",
    "media_14",
    "media_30",
]

FEATURES_CATEGORICAS = [
    "produto_nome",
]

FEATURES = FEATURES_CATEGORICAS + FEATURES_NUMERICAS

ALVO = "quantidade"


def preparar_dados_treinamento(df_ml):
    """
    Separa o dataset em treinamento e teste respeitando
    a ordem cronológica dos dados.
    """

    df = df_ml.copy()

    df["data_dia"] = pd.to_datetime(df["data_dia"])

    # Ordenação cronológica.
    df = df.sort_values("data_dia").reset_index(drop=True)

    # 80% das datas para treinamento e 20% para teste.
    datas = sorted(df["data_dia"].unique())

    ponto_corte = int(len(datas) * 0.80)

    data_corte = datas[ponto_corte]

    treino = df[df["data_dia"] < data_corte].copy()
    teste = df[df["data_dia"] >= data_corte].copy()

    X_treino = treino[FEATURES]
    y_treino = treino[ALVO]

    X_teste = teste[FEATURES]
    y_teste = teste[ALVO]

    return (
        X_treino,
        X_teste,
        y_treino,
        y_teste,
        treino,
        teste,
        data_corte,
    )


def criar_modelo():
    """
    Cria o pipeline de preparação das variáveis
    e o modelo Random Forest.
    """

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "produto",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                FEATURES_CATEGORICAS,
            ),
        ],
        remainder="passthrough",
    )

    modelo = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    return preprocessor, modelo


def treinar_modelo(df_ml):
    """
    Prepara os dados, treina o Random Forest
    e retorna o modelo e os resultados.
    """

    (
        X_treino,
        X_teste,
        y_treino,
        y_teste,
        treino,
        teste,
        data_corte,
    ) = preparar_dados_treinamento(df_ml)

    preprocessor, modelo = criar_modelo()

    X_treino_transformado = preprocessor.fit_transform(X_treino)
    X_teste_transformado = preprocessor.transform(X_teste)

    modelo.fit(
        X_treino_transformado,
        y_treino,
    )

    previsoes = modelo.predict(X_teste_transformado)

    mae = mean_absolute_error(y_teste, previsoes)

    rmse = mean_squared_error(
        y_teste,
        previsoes,
    ) ** 0.5

    r2 = r2_score(
        y_teste,
        previsoes,
    )

    resultados = teste[
        ["data_dia", "produto_nome", "quantidade"]
    ].copy()

    resultados["previsao"] = previsoes

    return {
        "preprocessor": preprocessor,
        "modelo": modelo,
        "treino": treino,
        "teste": teste,
        "resultados": resultados,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "data_corte": data_corte,
    }