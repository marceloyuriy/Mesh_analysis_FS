
# main_refatorado.py — Pipeline robusto para análise de efeito solo no FlightStream
# - Gera plano PLOT3D (ground)
# - Monta script do FlightStream por caso
# - Executa em modo batch
# - Faz parsing do "Aerodynamic Loads" com fs_parser.py (exclui Boundary do total)
#
# Pré-requisitos:
#   - FlightStream instalado e acessível
#   - Geometria .fsm do veículo
#
# Dicas de modelagem (condensado do manual e prática):
#   * Use plano de solo grande o suficiente (>= 10–15 cordas na direção X e largura Y similar ao span),
#     para reduzir efeitos de bordo do boundary.
#   * Evite que o "Total" inclua o ground — sempre compute métricas "apenas aeronave".
#   * Ajuste "Wake refinement size" para ~100–200% (1000% costuma estourar o tamanho médio e degrada
#     a fidelidade ao redor da asa/esteira).
#   * Garanta consistência da área/corda de referência entre casos OGE/IGE.
#
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List

from ground_generator import create_p3d_half_plane_ysymmetry
from fs_parser import parse_and_export


# -------- CONFIG --------

FLIGHTSTREAM_EXE = r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe"
FSM_GEOM = r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/geometria/AR021D_OGE.fsm"

WORKDIR = Path(r"/")
OUT_DIR = WORKDIR / "output"
CFG_DIR = WORKDIR / "FS_config"

# Domínio do plano de solo (ajuste conforme a sua escala/corda/span)
PLANE_X = (-60.0, 60.0)
PLANE_Y = (0.0, 60.0)     # meia-malha no Y=0; mude para (-60, 60) se for malha completa
PLANE_RES = (121, 61)     # resolução (ni, nj)

# Casos a rodar (ex.: alturas IGE e OGE, mesmo V e alpha)
CASES = [
    # altura_solo_m, alpha_deg, beta_deg, vel_ms
    (1.0, 0.0, 0.0, 25.0),
    # adicione outros casos aqui
]

MAX_ITERS = 1000
CONV_LIMIT = 1e-5
WAKE_REFINEMENT_PCT = 150.0


@dataclass
class Case:
    h: float
    alpha: float
    beta: float
    V: float


def build_fs_script_text(fsm_path: Path, ground_p3d: Path, case: Case, out_txt: Path) -> str:
    """
    Gera texto de script do FlightStream (comandos simples).
    Ajuste os comandos conforme a sintaxe da sua versão, se necessário.
    """
    lines = [
        # Abre geometria
        f'Load File "{fsm_path.as_posix()}"',
        # Importa plano PLOT3D como boundary
        f'Import Block File "{ground_p3d.as_posix()}"',
        # Define condições
        f'Set AngleOfAttack {case.alpha:.3f}',
        f'Set SideSlip {case.beta:.3f}',
        f'Set FreestreamVelocity {case.V:.3f}',
        # Ajustes de solver
        f'Set MaxIterations {MAX_ITERS}',
        f'Set ConvergenceLimit {CONV_LIMIT:.1e}',
        f'Set WakeRefinementPercent {WAKE_REFINEMENT_PCT:.1f}',
        # Executa solver
        'Run Solver',
        # Exporta "Aerodynamic Loads" (tabela)
        f'Export AerodynamicLoads "{out_txt.as_posix()}"',
        # Salva sessão/estado opcionalmente
        # f'Save Project "{(out_txt.with_suffix(".fsprj")).as_posix()}"',
        'Exit'
    ]
    return "\n".join(lines)


def run_case(case: Case) -> Path:
    h = case.h
    # 1) Gera ground PLOT3D na altura z=0; posicione a geometria a z=h (ou vice-versa)
    ground_file = OUT_DIR / f"ground_h{h:.2f}.p3d"
    create_p3d_half_plane_ysymmetry(
        PLANE_X[0], PLANE_X[1],
        PLANE_Y[0], PLANE_Y[1],
        z0=0.0,
        ni=PLANE_RES[0], nj=PLANE_RES[1],
        out_path=ground_file
    )

    # 2) Script do FlightStream para o caso
    out_txt = OUT_DIR / f"resultados_h{h:.2f}_a{case.alpha:.1f}_b{case.beta:.1f}_V{case.V:.1f}.txt"
    script_txt = build_fs_script_text(Path(FSM_GEOM), ground_file, case, out_txt)
    script_file = CFG_DIR / f"script_h{h:.2f}_a{case.alpha:.1f}.fs.txt"
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_text(script_txt, encoding='utf-8')

    # 3) Roda FlightStream em modo batch/hidden
    print(f"[FS] Rodando caso h={h:.2f} m, alpha={case.alpha:.1f}°, V={case.V:.1f} m/s ...")
    subprocess.run([
        FLIGHTSTREAM_EXE,
        "-script", script_file.as_posix(),
        "-hidden"
    ], check=True)

    # 4) Faz parsing e gera CSVs limpos
    out_parsed = OUT_DIR / f"parsed_h{h:.2f}_a{case.alpha:.1f}"
    parse_and_export(out_txt, out_parsed)

    return out_txt


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    for h, a, b, V in CASES:
        run_case(Case(h, a, b, V))

    print("--- Todas as análises foram concluídas. ---")


if __name__ == "__main__":
    main()
