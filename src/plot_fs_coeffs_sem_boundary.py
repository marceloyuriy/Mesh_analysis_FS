# -*- coding: utf-8 -*-
"""
pos_processador_simplificado.py

Lê relatórios CSV do FlightStream, exclui as superfícies 'Boundary*'
e plota os coeficientes CL, CDi e CMy em função da dimensão da malha.

Os arquivos CSV de entrada e os gráficos de saída são definidos
nas variáveis de configuração abaixo.
"""

import os
import re
from glob import glob
from typing import Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt

# ===================================================================
# CONFIGURAÇÃO: Altere os caminhos e o eixo X aqui
# ===================================================================

# 1. Coloque aqui o caminho para a pasta onde estão seus arquivos .csv
DIRETORIO_CSVS = r"C:\Users\marce\PycharmProjects\fs_ground_analysis\runs_pyfs\csv_malha_tamanho"  # O "." significa a pasta atual onde o script está

# 2. Coloque aqui o caminho para a pasta onde você quer salvar os gráficos e o CSV agregado
DIRETORIO_SAIDA = r"C:\Users\marce\PycharmProjects\fs_ground_analysis\runs_pyfs\post_process\graphics"

# 3. (NOVO) Escolha a dimensão da malha para usar no eixo X dos gráficos.
#    Use "nx" ou "ny".
EIXO_X_MALHA = "nx"

# ===================================================================
# FIM DA CONFIGURAÇÃO
# ===================================================================


# Expressões Regulares para extrair dados dos nomes dos arquivos
RE_L = re.compile(r"[\\/_]L(?P<L>[-+]?\d+(?:\.\d+)?)m[\\/_]?", re.IGNORECASE)
RE_MALHA = re.compile(r"malha_(?P<nx>\d+)x(?P<ny>\d+)", re.IGNORECASE)


def extrair_dados_do_nome_arquivo(caminho: str) -> Tuple[float, int, int]:
    """Extrai o tamanho L e as dimensões da malha (nx, ny) do nome do arquivo."""
    nome_arquivo = os.path.basename(caminho)
    match_L = RE_L.search(nome_arquivo)
    match_malha = RE_MALHA.search(nome_arquivo)

    if not (match_L and match_malha):
        raise ValueError(f"Não foi possível extrair L e malha de: {nome_arquivo}")

    L = float(match_L.group("L"))
    nx = int(match_malha.group("nx"))
    ny = int(match_malha.group("ny"))
    return L, nx, ny


def ler_tabela_flightstream(caminho: str) -> pd.DataFrame:
    """Lê o arquivo CSV do FlightStream e extrai a tabela 'Aerodynamic Loads'."""
    linhas_tabela = []
    dentro_da_tabela = False

    header_pattern = re.compile(r"^\s*Surface,\s*Cx,\s*Cy,", re.IGNORECASE)
    dash_pattern = re.compile(r"^-{5,}")

    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            linha_limpa = linha.strip()
            if not dentro_da_tabela and header_pattern.match(linha_limpa):
                dentro_da_tabela = True
                continue

            if dentro_da_tabela:
                if dash_pattern.match(linha_limpa):
                    if linhas_tabela:
                        break
                    else:
                        continue

                partes = [p.strip() for p in linha.split(",")]
                if len(partes) >= 10:
                    linhas_tabela.append(partes[:10])

    if not linhas_tabela:
        raise ValueError(f"Tabela de superfícies não encontrada em: {os.path.basename(caminho)}")

    colunas = ["Surface", "Cx", "Cy", "Cz", "CL", "CDi", "CDo", "CMx", "CMy", "CMz"]
    df = pd.DataFrame(linhas_tabela, columns=colunas)

    for col in colunas[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def agregar_coeficientes(df: pd.DataFrame) -> Dict[str, float]:
    """Soma os coeficientes, ignorando as superfícies 'Boundary' e 'Total'."""
    mask_valid = ~df["Surface"].str.contains("boundary", case=False, na=False) & \
                 ~df["Surface"].str.fullmatch(r"(?i)total")

    df_filtrado = df.loc[mask_valid, ["CL", "CDi", "CMy"]]

    return {
        "CL": df_filtrado["CL"].sum(skipna=True),
        "CDi": df_filtrado["CDi"].sum(skipna=True),
        "CMy": df_filtrado["CMy"].sum(skipna=True),
    }


# (ALTERADO) A função agora recebe o rótulo do eixo X como argumento
def gerar_grafico(df: pd.DataFrame, metrica: str, caminho_saida: str, rotulo_eixo_x: str) -> None:
    """Gera e salva um gráfico de uma métrica vs. a dimensão da malha."""
    # (ALTERADO) Usa a coluna 'malha_eixo_x'
    df_plot = df.dropna(subset=["L_m", "malha_eixo_x", metrica]).copy()
    df_plot = df_plot.sort_values(by=["L_m", "malha_eixo_x"])

    plt.figure(figsize=(10, 6))

    for L, grupo in df_plot.groupby("L_m"):
        # (ALTERADO) Plota usando 'malha_eixo_x'
        plt.plot(grupo["malha_eixo_x"], grupo[metrica], marker="o", linestyle="-", label=f"L={L:g} m")

    # (ALTERADO) Usa o rótulo dinâmico
    plt.xlabel(rotulo_eixo_x)
    plt.ylabel(metrica)
    plt.title(f"{metrica} vs. {rotulo_eixo_x}")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)

    if not df_plot.empty:
        plt.legend(title="Tamanho do plano (L)")

    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=150)
    plt.close()
    print(f"✔️ Gráfico salvo em: {caminho_saida}")


def main():
    """Função principal que orquestra todo o processo."""
    print(f"Lendo arquivos CSV de: '{DIRETORIO_CSVS}'")

    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)

    arquivos_csv = sorted(glob(os.path.join(DIRETORIO_CSVS, "*.csv")))
    if not arquivos_csv:
        print(f"⚠️ Nenhum arquivo .csv encontrado em '{DIRETORIO_CSVS}'. Verifique o caminho.")
        return

    resultados = []
    for caminho in arquivos_csv:
        try:
            L, nx, ny = extrair_dados_do_nome_arquivo(caminho)
            df_tabela = ler_tabela_flightstream(caminho)
            coeficientes = agregar_coeficientes(df_tabela)

            # (ALTERADO) Seleciona o valor para o eixo X com base na configuração
            valor_eixo_x = nx if EIXO_X_MALHA == "nx" else ny

            resultados.append({
                "arquivo": os.path.basename(caminho),
                "L_m": L,
                "nx": nx,
                "ny": ny,
                "malha_eixo_x": valor_eixo_x,  # Nova coluna para o eixo X
                **coeficientes,
            })
        except Exception as e:
            print(f"❌ Erro ao processar o arquivo {os.path.basename(caminho)}: {e}")

    if not resultados:
        print("Nenhum dado válido foi processado. Encerrando.")
        return

    df_final = pd.DataFrame(resultados)

    caminho_csv_saida = os.path.join(DIRETORIO_SAIDA, "agregado_sem_boundary.csv")
    df_final.to_csv(caminho_csv_saida, index=False)
    print(f"✔️ Tabela agregada salva em: {caminho_csv_saida}")

    # (ALTERADO) Define o rótulo do eixo X para os gráficos
    rotulo_x = f"Dimensão da Malha ({EIXO_X_MALHA})"

    # (ALTERADO) Passa o rótulo para a função de plotagem
    gerar_grafico(df_final, "CL", os.path.join(DIRETORIO_SAIDA, "plot_CL_vs_malha.png"), rotulo_x)
    gerar_grafico(df_final, "CDi", os.path.join(DIRETORIO_SAIDA, "plot_CDi_vs_malha.png"), rotulo_x)
    gerar_grafico(df_final, "CMy", os.path.join(DIRETORIO_SAIDA, "plot_CMy_vs_malha.png"), rotulo_x)

    print("\nProcesso concluído com sucesso!")


if __name__ == "__main__":
    main()