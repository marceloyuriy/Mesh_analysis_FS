# post_processing.py
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import CategoricalDtype

# Importa a variável RUNS_DIR do seu script 'shared.py'
try:
    from shared import RUNS_DIR
except ImportError:
    print("Aviso: Não foi possível importar 'RUNS_DIR' de 'shared.py'.")
    print("Definindo um caminho padrão. Ajuste se necessário.")
    RUNS_DIR = Path("./runs_pyfs/csv").resolve()  # Fallback


def _parse_mesh(mesh_str: str) -> tuple[int, int]:
    """Converte 'AxB' -> (A, B) como inteiros."""
    m = re.match(r"^\s*(\d+)\s*x\s*(\d+)\s*$", mesh_str, re.IGNORECASE)
    if not m:
        raise ValueError(f"Formato de malha inválido: {mesh_str}")
    return int(m.group(1)), int(m.group(2))


def parse_results(results_dir: Path) -> pd.DataFrame:
    """
    Analisa os arquivos _solver.csv, extrai parâmetros do nome do arquivo
    e calcula a soma dos coeficientes aerodinâmicos, EXCLUINDO a superfície 'Boundary'.
    """
    if not results_dir.is_dir():
        print(f"ERRO: O diretório de resultados não foi encontrado em '{results_dir}'")
        return pd.DataFrame()

    # Procura por todos os arquivos _solver.csv recursivamente dentro da pasta
    csv_files = list(results_dir.glob("*/*_solver.csv"))
    if not csv_files:
        # Se não encontrar em subpastas, procura no diretório principal
        csv_files = list(results_dir.glob("*_solver.csv"))

    print(f"Encontrados {len(csv_files)} arquivos .csv para processar.")

    all_data = []
    # Regex flexível com grupos para L e malha AxB
    pattern = re.compile(r"_L(\d+\.?\d*)m_malha_(\d+x\d+)_", re.IGNORECASE)

    for csv_path in csv_files:
        match = pattern.search(csv_path.name)
        if not match:
            print(f"Aviso: Não foi possível extrair parâmetros do nome: {csv_path.name}")
            continue

        l_val = float(match.group(1))
        mesh_val = match.group(2)

        try:
            NI, NJ = _parse_mesh(mesh_val)
        except ValueError as e:
            print(f"Aviso: {e} ({csv_path.name})")
            continue

        total_cl, total_cdi, total_cmy = 0.0, 0.0, 0.0

        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()

            # Encontra o início da tabela de dados procurando pelo cabeçalho
            start_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('Surface, Cx, Cy'):
                    start_index = i + 2  # pula cabeçalho e linha '----'
                    break

            if start_index == -1:
                print(f"Aviso: Cabeçalho da tabela de dados não encontrado em {csv_path.name}")
                continue

            # Percorre linhas de dados das superfícies
            for i in range(start_index, len(lines)):
                line_strip = lines[i].strip()
                if line_strip.startswith('----') or not line_strip:
                    break

                parts = [p.strip() for p in line_strip.split(',')]
                surface_name = parts[0]

                # Exclui 'Boundary' e a linha 'Total'
                if surface_name.startswith('Boundary') or surface_name == 'Total':
                    continue

                try:
                    # Índices: CL[4], CDi[5], CMy[8]
                    total_cl += float(parts[4])
                    total_cdi += float(parts[5])
                    total_cmy += float(parts[8])
                except (IndexError, ValueError) as e:
                    print(f"Aviso: Pulando linha malformada em {csv_path.name}: '{line_strip}' ({e})")

            all_data.append({
                'L': l_val,
                'malha': mesh_val,  # manter label amigável
                'NI': NI,
                'NJ': NJ,
                'elems': NI * NJ,   # métrica de “tamanho” da malha
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

    # Define ordem crescente de malha: por número de elementos (tie-break por NI e NJ)
    mesh_order = (
        df[['malha', 'NI', 'NJ', 'elems']]
        .drop_duplicates()
        .sort_values(by=['elems', 'NI', 'NJ'], ascending=True)
        ['malha']
        .tolist()
    )

    # Converte 'malha' para categoria ordenada para refletir no eixo X dos gráficos
    dtype_ordered = CategoricalDtype(categories=mesh_order, ordered=True)
    df['malha'] = df['malha'].astype(dtype_ordered)

    # Ordena linhas para impressão/depuração
    df = df.sort_values(by=['L', 'elems', 'NI', 'NJ']).reset_index(drop=True)
    return df


def plot_results(df: pd.DataFrame):
    """
    Gera os gráficos dos coeficientes em função do refinamento da malha
    (ordem crescente por número de elementos).
    """
    if df.empty:
        print("O DataFrame está vazio. Nenhum gráfico será gerado.")
        return

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(3, 1, figsize=(12, 18), sharex=True)
    fig.suptitle('Análise de Convergência (Excluindo Superfície "Boundary")', fontsize=20, y=0.95)

    # CL vs Malha
    sns.lineplot(
        data=df, x='malha', y='CL', hue='L', style='L',
        markers=True, dashes=False, ax=axes[0], palette="viridis", legend='full'
    )
    axes[0].set_title('Coeficiente de Sustentação (CL)')
    axes[0].set_ylabel('CL')
    axes[0].grid(True, which='both', linestyle='--')

    # CDi vs Malha
    sns.lineplot(
        data=df, x='malha', y='CDi', hue='L', style='L',
        markers=True, dashes=False, ax=axes[1], palette="viridis", legend=False
    )
    axes[1].set_title('Arrasto Induzido (CDi)')
    axes[1].set_ylabel('CDi')
    axes[1].grid(True, which='both', linestyle='--')

    # CMy vs Malha
    sns.lineplot(
        data=df, x='malha', y='CMy', hue='L', style='L',
        markers=True, dashes=False, ax=axes[2], palette="viridis", legend=False
    )
    axes[2].set_title('Momento de Arfagem (CMy)')
    axes[2].set_xlabel('Refinamento da Malha (ordem crescente de elementos)')
    axes[2].set_ylabel('CMy')
    axes[2].grid(True, which='both', linestyle='--')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_path = RUNS_DIR / "analise_convergencia_corrigido.png"
    plt.savefig(output_path, dpi=300)
    print(f"\nGráficos salvos em: {output_path}")
    plt.show()


if __name__ == "__main__":
    df_results = parse_results(RUNS_DIR)

    if not df_results.empty:
        print("\n--- Dados Extraídos (Soma sem 'Boundary') ---")
        print(df_results[['L', 'malha', 'NI', 'NJ', 'elems', 'CL', 'CDi', 'CMy']])
        print("--------------------------------------------\n")

        plot_results(df_results)
