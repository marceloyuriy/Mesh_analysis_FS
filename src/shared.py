# shared.py (debug-friendly)
from pathlib import Path
import os
import pyFlightscript as pyfs

# --- CONFIG ---
FS_EXE = os.environ.get(
    "FS_EXE",
    r"C:\marcelo\flightstream\FlightStream_25.1_Windows_x86_64.exe"
)

ROOT      = Path(__file__).resolve().parent  # pasta do script
GEOM_DIR  = (ROOT.parent / "ground_mesh").resolve()
RUNS_DIR  = (ROOT.parent / "runs_pyfs").resolve()

LOGS_DIR  = (RUNS_DIR / "logs").resolve()
SCRIPT_NAME = "script_out.txt"

# Deixe False no debug para VER a janela do FS e qualquer pop-up.
HIDDEN = True

FLOW = dict(velocity=15.0, density=1.225, viscosity=1.7894e-5, aoa=0.0, sideslip=0.0)
SOLVER_ITERS = 500

GEOM_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def _resolve_fsm_path(p: Path) -> Path:
    """Aceita um .fsm direto ou uma pasta contendo .fsm; pega o mais recente."""
    p = p.resolve()
    if p.is_file() and p.suffix.lower() == ".fsm":
        return p
    if p.is_dir():
        candidates = sorted(p.glob("*.fsm"), key=lambda x: x.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
        raise FileNotFoundError(f"Nenhum .fsm encontrado em {p}")
    raise FileNotFoundError(f"Caminho FSM inválido: {p}")

FSM_FILE_PATH =  _resolve_fsm_path((ROOT.parent / "geometria"))

def case_name_from_path(p: Path) -> str:
    return p.stem

def _reset_script():
    # limpa buffer e apaga o arquivo de macro anterior
    if hasattr(pyfs, "script") and hasattr(pyfs.script, "hard_reset"):
        pyfs.script.hard_reset(filename=SCRIPT_NAME, header=False)
    else:
        # fallback para versões antigas
        pyfs.hard_reset(filename=SCRIPT_NAME)

def _new_simulation():
    if hasattr(pyfs, "fsinit") and hasattr(pyfs.fsinit, "new_simulation"):
        pyfs.fsinit.new_simulation()
    else:
        raise RuntimeError("pyFlightscript: não achei fsinit.new_simulation().")

def _set_length_units(units="METER"):
    if hasattr(pyfs, "fsinit") and hasattr(pyfs.fsinit, "set_simulation_length_units"):
        pyfs.fsinit.set_simulation_length_units(units)
    elif hasattr(pyfs, "set_simulation_length_units"):
        pyfs.set_simulation_length_units(units=units)
    else:
        raise RuntimeError("pyFlightscript: não encontrei set_simulation_length_units().")

def _set_iterations(n: int):
    if hasattr(pyfs, "set_solver") and hasattr(pyfs.set_solver, "solver_iterations"):
        pyfs.set_solver.solver_iterations(n)
    else:
        print("[aviso] não achei set_solver.solver_iterations; mantendo default do FS.")

def _write_and_run(script_path: Path):
    # Mostra no console todas as linhas do macro para debug
    try:
        if hasattr(pyfs, "script") and hasattr(pyfs.script, "display_lines"):
            pyfs.script.display_lines()
    except Exception:
        pass

    # Grava o macro
    if hasattr(pyfs, "script") and hasattr(pyfs.script, "write_to_file"):
        pyfs.script.write_to_file(filename=str(script_path))
    else:
        pyfs.write_to_file(filename=str(script_path))

    # Checa o executável
    if not Path(FS_EXE).exists():
        raise FileNotFoundError(f"FlightStream EXE não encontrado: {FS_EXE}")

    # Executa o macro no FlightStream
    # Doc oficial: run_script(fsexe_path, script_path='.\script_out.txt', hidden=False)
    # (Compatível com FS 2025.1+)
    # https://altairengineering.github.io/pyFlightscript/  ← docs
    if hasattr(pyfs, "script") and hasattr(pyfs.script, "run_script"):
        res = pyfs.script.run_script(
            fsexe_path=str(FS_EXE),
            script_path=str(script_path),
            hidden=HIDDEN
        )
    else:
        res = pyfs.run_script(
            fsexe_path=str(FS_EXE),
            script_path=str(script_path),
            hidden=HIDDEN
        )
    return res
