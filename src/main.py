# main.py
from pathlib import Path
from shared import GEOM_DIR  # paths/config
from run_case import run_case
from post_processing import parse_results, plot_results

def main():
    p3ds = sorted(GEOM_DIR.glob("*.p3d"))
    if not p3ds:
        print(f"Nenhum .p3d encontrado em {GEOM_DIR}")
        return
    for p3d in p3ds:
        run_case(p3d)

    #Post-processing
    # Importa a variável runs_dir do seu script 'shared.py'
    try:
        from shared import runs_dir
    except ImportError:
        print("Aviso: Não foi possível importar 'runs_dir' de 'shared.py'.")
        print("Definindo um caminho padrão. Ajuste se necessário.")
        runs_dir = Path("./runs_pyfs").resolve()  # Fallback

    df_results = parse_results(runs_dir)

    if not df_results.empty:
        print("\n--- Dados Extraídos (Soma sem 'Boundary') ---")
        print(df_results)
        print("--------------------------------------------\n")

        plot_results(df_results)

if __name__ == "__main__":
    main()
