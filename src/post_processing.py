# post_process_v2.py
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Importa a variável RUNS_DIR do seu script 'shared.py'
try:
    from shared import RUNS_DIR
except ImportError:
    print("Aviso: Não foi possível importar 'RUNS_DIR' de 'shared.py'.")
    print("Definindo um caminho padrão. Ajuste se necessário.")
    RUNS_DIR = Path("./runs_pyfs").resolve()  # Fallback

def parse_results(results_dir: Path) -> pd.DataFrame:
    """
    Analisa os arquivos _solver.csv, extrai parâmetros do nome do arquivo
    e calcula a soma dos coeficientes aerodinâmicos, EXCLUINDO a superfície 'Boundary'.
    """
    if not results_dir.is_dir():
        print(f"ERRO: O diretório de resultados não foi encontrado em '{results_dir}'")
        return pd.DataFrame()

    all_data = []
    csv_files = list(results_dir.glob("*/*_solver.csv"))
    print(f"Encontrados {len(csv_files)} arquivos .csv para processar.")

    pattern = re.compile(r"_L(\d+\.?\d*)m_malha_(\dx\d+)_")

    for csv_path in csv_files:
        match = pattern.search(csv_path.name)
        if not match:
            print(f"Aviso: Não foi possível extrair parâmetros do nome: {csv_path.name}")
            continue

        l_val = float(match.group(1))
        mesh_val = match.group(2)

        # --- LÓGICA MODIFICADA AQUI ---
        # Inicializa os somatórios para este arquivo
        total_cl, total_cdi, total_cmy = 0.0, 0.0, 0.0

        try:
            with open(csv_path, 'r') as f:
                in_data_section = False
                for line in f:
                    line_strip = line.strip()

                    # A seção de dados começa após a primeira linha de hífens
                    if '----' in line_strip and not in_data_section:
                        in_data_section = True
                        continue
                    # E termina na segunda linha de hífens
                    if '----' in line_strip and in_data_section:
                        break

                    if in_data_section:
                        # Ignora linhas vazias ou de cabeçalho
                        if not line_strip or "Surface" in line:
                            continue

                        parts = [p.strip() for p in line.split(',')]
                        surface_name = parts[0]

                        # Pula a superfície 'Boundary' e a linha 'Total' original
                        if surface_name.startswith('Boundary') or surface_name == 'Total':
                            continue

                        # Soma os valores das outras superfícies
                        # Índices: CL[4], CDi[5], CMy[8]
                        try:
                            total_cl += float(parts[4])
                            total_cdi += float(parts[5])
                            total_cmy += float(parts[8])
                        except (IndexError, ValueError) as e:
                            print(f"Aviso: Pulando linha malformada em {csv_path.name}: '{line_strip}' ({e})")

            # Adiciona os totais calculados à nossa lista de dados
            all_data.append({
                'L': l_val,
                'malha': mesh_val,
                'CL': total_cl,
                'CDi': total_cdi,
                'CMy': total_cmy
            })

        except Exception as e:
            print(f"Erro ao processar o arquivo {csv_path.name}: {e}")

    if not all_data:
        print("Nenhum dado foi extraído. Verifique os arquivos e caminhos.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    df = df.sort_values(by=['L', 'malha']).reset_index(drop=True)

    return df


def plot_results(df: pd.DataFrame):
    """
    Gera os gráficos dos coeficientes em função do tamanho da malha,
    agrupados pelo comprimento L. (Esta função não foi alterada)
    """
    if df.empty:
        print("O DataFrame está vazio. Nenhum gráfico será gerado.")
        return

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(3, 1, figsize=(12, 18), sharex=True)
    fig.suptitle('Análise de Convergência (Excluindo Superfície "Boundary")', fontsize=20, y=0.95)

    # Gráfico 1: CL vs Malha
    sns.lineplot(data=df, x='malha', y='CL', hue='L', style='L', markers=True, dashes=False, ax=axes[0],
                 palette="viridis", legend='full')
    axes[0].set_title('Coeficiente de Sustentação (CL)')
    axes[0].set_ylabel('CL')
    axes[0].grid(True, which='both', linestyle='--')

    # Gráfico 2: CDi vs Malha
    sns.lineplot(data=df, x='malha', y='CDi', hue='L', style='L', markers=True, dashes=False, ax=axes[1],
                 palette="viridis", legend=False)
    axes[1].set_title('Arrasto Induzido (CDi)')
    axes[1].set_ylabel('CDi')
    axes[1].grid(True, which='both', linestyle='--')

    # Gráfico 3: CMy vs Malha
    sns.lineplot(data=df, x='malha', y='CMy', hue='L', style='L', markers=True, dashes=False, ax=axes[2],
                 palette="viridis", legend=False)
    axes[2].set_title('Momento de Arfagem (CMy)')
    axes[2].set_xlabel('Refinamento da Malha')
    axes[2].set_ylabel('CMy')
    axes[2].grid(True, which='both', linestyle='--')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = RUNS_DIR / "analise_convergencia_sem_boundary.png"
    plt.savefig(output_path, dpi=300)
    print(f"\nGráficos salvos em: {output_path}")
    plt.show()


if __name__ == "__main__":
    df_results = parse_results(RUNS_DIR)

    if not df_results.empty:
        print("\n--- Dados Extraídos (Soma sem 'Boundary') ---")
        print(df_results)
        print("--------------------------------------------\n")

        plot_results(df_results)