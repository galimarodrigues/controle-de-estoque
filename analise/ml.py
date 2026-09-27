import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
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

def treinar_modelo_dois_estagios(df_ml):
    """
    Modelo em duas etapas:

    1. Classifica se haverá demanda (0 ou 1).
    2. Para os casos com demanda, estima a quantidade.

    A previsão final é zero quando o classificador
    identifica ausência de demanda.
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

    # -------------------------------------------------
    # ETAPA 1 - CLASSIFICAÇÃO
    # -------------------------------------------------

    y_treino_classe = (y_treino > 0).astype(int)

    preprocessor_clf, _ = criar_modelo()

    classificador = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
        class_weight="balanced",
    )

    X_treino_clf = preprocessor_clf.fit_transform(X_treino)
    X_teste_clf = preprocessor_clf.transform(X_teste)

    classificador.fit(
        X_treino_clf,
        y_treino_classe,
    )

    previsao_classe = classificador.predict(
        X_teste_clf
    )

    # -------------------------------------------------
    # ETAPA 2 - REGRESSÃO
    # -------------------------------------------------

    # O regressor aprende somente com os dias
    # em que realmente houve demanda.
    filtro_positivos = y_treino > 0

    X_treino_pos = X_treino.loc[filtro_positivos]
    y_treino_pos = y_treino.loc[filtro_positivos]

    preprocessor_reg, regressor = criar_modelo()

    X_treino_reg = preprocessor_reg.fit_transform(
        X_treino_pos
    )

    X_teste_reg = preprocessor_reg.transform(
        X_teste
    )

    regressor.fit(
        X_treino_reg,
        y_treino_pos,
    )

    previsao_quantidade = regressor.predict(
        X_teste_reg
    )

    # -------------------------------------------------
    # PREVISÃO FINAL
    # -------------------------------------------------

    # Quando o classificador prevê ausência de demanda,
    # a previsão final passa a ser exatamente zero.
    previsoes = np.where(
        previsao_classe == 1,
        previsao_quantidade,
        0,
    )

    # Evita eventual previsão negativa.
    previsoes = np.maximum(previsoes, 0)

    # -------------------------------------------------
    # MÉTRICAS
    # -------------------------------------------------

    mae = mean_absolute_error(
        y_teste,
        previsoes,
    )

    rmse = mean_squared_error(
        y_teste,
        previsoes,
    ) ** 0.5

    r2 = r2_score(
        y_teste,
        previsoes,
    )

    acuracia_classificacao = accuracy_score(
        (y_teste > 0).astype(int),
        previsao_classe,
    )

    resultados = teste[
        [
            "data_dia",
            "produto_nome",
            "quantidade",
        ]
    ].copy()

    resultados["previsao"] = previsoes
    resultados["previsao_demanda"] = previsao_classe

    return {
        "preprocessor_clf": preprocessor_clf,
        "classificador": classificador,
        "preprocessor_reg": preprocessor_reg,
        "regressor": regressor,
        "treino": treino,
        "teste": teste,
        "resultados": resultados,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "acuracia_classificacao": acuracia_classificacao,
        "data_corte": data_corte,
    }