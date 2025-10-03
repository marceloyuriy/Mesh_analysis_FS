# -*- coding: utf-8 -*-
import subprocess
import textwrap
from pathlib import Path

def bslash(path: str) -> str:
    return str(path).replace('/', '\\')

# --- Caminhos base do projeto (ajuste se seu layout for diferente)
BASE_DIR = Path(r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03")
GROUND_DIR = BASE_DIR / "ground_mesh"   # onde estão os .p3d já gerados
SCRIPT_DIR = BASE_DIR / "FS_script"     # .txt de script do FlightStream
OUTPUT_DIR = BASE_DIR / "output"        # planilhas/saídas
for d in (SCRIPT_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Binário e geometria do veículo
FLIGHTSTREAM_EXE = r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe"
VEICULO_FSM = r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/geometria/AR021D_OGE.fsm"

# --- IDs no FlightStream
IDS_SUPERFICIES_VEICULO = [80, 81, 82, 83, 84, 85, 86]  # ajuste conforme o seu .fsm
ID_SUPERFICIE_SOLO = 139                               # id da superfície do solo importada

# --- Parâmetros de solver (ajuste livre)
REF_VEL = 15.0
REF_LEN = 5.625
REF_AREA = 36.9
AOA = 0.0
NITERS = 500
TOL = 1e-5

# --- Coleta todas as geometrias .p3d no diretório
p3d_files = sorted(GROUND_DIR.glob("*.p3d"))
if not p3d_files:
    raise SystemExit(f"Nenhum .p3d encontrado em {GROUND_DIR}")

print(f"Encontradas {len(p3d_files)} geometrias .p3d em {GROUND_DIR}")

for p3d in p3d_files:
    nome_caso = p3d.stem                                  # ex.: plano_solo_30m_21x11_h2.8125
    script_path = SCRIPT_DIR / f"{nome_caso}.txt"
    result_path = OUTPUT_DIR / f"{nome_caso}_resultados.csv"

    boundaries_veic = ",".join(map(str, IDS_SUPERFICIES_VEICULO))

    # Script do FlightStream: IMPORT FILE (sem FILE_TYPE), solver e export
    script = f"""
    OPEN
    {bslash(VEICULO_FSM)}
    SET_SIMULATION_LENGTH_UNITS METER

    IMPORT
    FILE {bslash(p3d)}

    # Exclui o SOLO do modelo viscoso (mantém o veículo)
    SET_VISCOUS_EXCLUDED_BOUNDARIES 1
    {ID_SUPERFICIE_SOLO}

    SOLVER_SET_REF_VELOCITY {REF_VEL}
    SOLVER_SET_REF_LENGTH {REF_LEN}
    SOLVER_SET_REF_AREA {REF_AREA}
    SOLVER_SET_AOA {AOA}
    SOLVER_SET_VELOCITY {REF_VEL}
    SOLVER_SET_ITERATIONS {NITERS}
    SOLVER_SET_CONVERGENCE {TOL}
    REMOVE_INITIALIZATION
    INITIALIZE_SOLVER
    SOLVER_MODEL INCOMPRESSIBLE

    # Simetria em Y (espelho)
    SYMMETRY MIRROR
    SURFACES -1

    WAKE_TERMINATION_X DEFAULT
    START_SOLVER

    # Considera apenas as superfícies do veículo no somatório total
    SET_SOLVER_ANALYSIS_BOUNDARIES {len(IDS_SUPERFICIES_VEICULO)}
    {boundaries_veic}

    EXPORT_SOLVER_ANALYSIS_SPREADSHEET
    {bslash(result_path)}

    CLOSE_FLIGHTSTREAM
    """
    script_path.write_text(textwrap.dedent(script).strip(), encoding="utf-8")

    print(f"[{nome_caso}] rodando FlightStream…")
    subprocess.run([
        bslash(FLIGHTSTREAM_EXE),
        "-script", bslash(script_path),
        "-hidden"
    ], check=True)
    print(f"[{nome_caso}] OK → {result_path}")
