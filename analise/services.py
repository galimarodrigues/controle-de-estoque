import pandas as pd

from estoque.models import Movimentacao


def carregar_movimentacoes_dataframe():
    """
    Carrega as movimentações do banco de dados
    e retorna um DataFrame do Pandas.
    """

    registros = Movimentacao.objects.values(
        "id",
        "produto_id",
        "produto_nome",
        "categoria_nome",
        "unidade",
        "quantidade",
        "tipo",
        "data",
        "custo_unitario",
        "motivo",
        "fornecedor",
    )

    df = pd.DataFrame.from_records(registros)

    if df.empty:
        return df

    df["data"] = pd.to_datetime(df["data"])

    # Mantém a data como Timestamp do Pandas.
    # Isso facilita os cálculos de série temporal.
    df["data_dia"] = df["data"].dt.normalize()

    df["custo_unitario"] = pd.to_numeric(
        df["custo_unitario"],
        errors="coerce"
    )

    df["quantidade"] = pd.to_numeric(
        df["quantidade"],
        errors="coerce"
    )

    return df


def criar_dataset_demanda():
    """
    Constrói o dataset diário de demanda por produto.

    O processo:
    1. Carrega as movimentações.
    2. Considera apenas saídas.
    3. Agrega a quantidade por dia e produto.
    4. Cria todas as combinações de dia e produto.
    5. Preenche com zero os dias sem saída.
    6. Cria variáveis temporais.
    """

    df = carregar_movimentacoes_dataframe()

    if df.empty:
        return df

    # Consideramos saída como consumo/demanda.
    saidas = df[df["tipo"] == "saida"].copy()

    # Demanda observada por dia e produto.
    demanda_diaria = (
        saidas
        .groupby(
            ["data_dia", "produto_nome"],
            as_index=False
        )["quantidade"]
        .sum()
    )

    # Todas as datas existentes no período.
    data_inicio = demanda_diaria["data_dia"].min()
    data_fim = demanda_diaria["data_dia"].max()

    datas = pd.date_range(
        start=data_inicio,
        end=data_fim,
        freq="D"
    )

    # Todos os produtos.
    produtos = (
        demanda_diaria["produto_nome"]
        .dropna()
        .unique()
    )

    # Todas as combinações possíveis:
    # dia × produto.
    grade = pd.MultiIndex.from_product(
        [datas, produtos],
        names=["data_dia", "produto_nome"]
    ).to_frame(index=False)

    # Junta a demanda observada.
    demanda_completa = grade.merge(
        demanda_diaria,
        on=["data_dia", "produto_nome"],
        how="left"
    )

    # Ausência de saída = demanda zero.
    demanda_completa["quantidade"] = (
        demanda_completa["quantidade"]
        .fillna(0)
    )

    # Variáveis de calendário.
    demanda_completa["dia_semana"] = (
        demanda_completa["data_dia"].dt.dayofweek
    )

    demanda_completa["fim_de_semana"] = (
        demanda_completa["dia_semana"] >= 5
    ).astype(int)

    demanda_completa["mes"] = (
        demanda_completa["data_dia"].dt.month
    )

    demanda_completa["dia_mes"] = (
        demanda_completa["data_dia"].dt.day
    )

    # Ordenação temporal por produto.
    demanda_completa = (
        demanda_completa
        .sort_values(
            ["produto_nome", "data_dia"]
        )
        .reset_index(drop=True)
    )

    # Demanda do dia anterior.
    demanda_completa["demanda_lag_1"] = (
        demanda_completa
        .groupby("produto_nome")["quantidade"]
        .shift(1)
    )

    # Demanda de sete dias atrás.
    demanda_completa["demanda_lag_7"] = (
        demanda_completa
        .groupby("produto_nome")["quantidade"]
        .shift(7)
    )

    # Médias móveis baseadas apenas no passado.
    demanda_completa["media_7"] = (
        demanda_completa
        .groupby("produto_nome")["quantidade"]
        .transform(
            lambda x: x.shift(1).rolling(7).mean()
        )
    )

    demanda_completa["media_14"] = (
        demanda_completa
        .groupby("produto_nome")["quantidade"]
        .transform(
            lambda x: x.shift(1).rolling(14).mean()
        )
    )

    demanda_completa["media_30"] = (
        demanda_completa
        .groupby("produto_nome")["quantidade"]
        .transform(
            lambda x: x.shift(1).rolling(30).mean()
        )
    )

    return demanda_completa


def criar_dataset_ml():
    """
    Retorna somente os registros com histórico suficiente
    para treinamento do modelo.
    """

    demanda_completa = criar_dataset_demanda()

    if demanda_completa.empty:
        return demanda_completa

    df_ml = demanda_completa[
        [
            "data_dia",
            "produto_nome",
            "quantidade",
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
    ].copy()

    # Removemos registros sem histórico suficiente.
    df_ml = df_ml.dropna()

    return df_ml