# main.py
from pathlib import Path
import os
import pyFlightscript as pyfs

# >>>>>>>>>>>> AJUSTE AQUI <<<<<<<<<<<<
FS_EXE   = r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe"
GEOM_DIR = Path(__file__).parent / "ground_mesh"
RUNS_DIR = Path(__file__).parent / "runs_pyfs"
SCRIPT_NAME = "script_out.txt"

FLOW = dict(velocity=15.0, density=1.225, viscosity=1.7894e-5, aoa=0.0, sideslip=0.0)
SOLVER_ITERS = 500
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

GEOM_DIR.mkdir(exist_ok=True, parents=True)
RUNS_DIR.mkdir(exist_ok=True, parents=True)

def case_name_from_path(p3d_path: Path) -> str:
    return p3d_path.stem  # ex.: plano_solo_30m_41x21_h2.8125

# ---------- Utilitários de compatibilidade com versões do pyFlightscript ----------

def _reset_script(script_path: Path):
    """Reset robusto: usa hard_reset se existir; senão limpa linhas e apaga o arquivo."""
    try:
        if hasattr(pyfs, "script") and hasattr(pyfs.script, "hard_reset"):
            pyfs.script.hard_reset(str(script_path))
            return
    except Exception:
        pass
    try:
        if hasattr(pyfs, "script") and hasattr(pyfs.script, "clear_lines"):
            pyfs.script.clear_lines()
    except Exception:
        pass
    try:
        script_path.unlink(missing_ok=True)
    except Exception:
        pass

def _write_and_run(script_path: Path):
    """Escreve a macro e executa o FlightStream, cobrindo diferenças de API."""
    # escrever
    if hasattr(pyfs, "script") and hasattr(pyfs.script, "write_to_file"):
        pyfs.script.write_to_file(str(script_path))
    elif hasattr(pyfs, "write_to_file"):
        pyfs.write_to_file(str(script_path))
    else:
        raise RuntimeError("pyFlightscript: não encontrei write_to_file.")
    # executar
    if hasattr(pyfs, "script") and hasattr(pyfs.script, "run_script"):
        pyfs.script.run_script(fsexe_path=FS_EXE, script_path=str(script_path), hidden=True)
    elif hasattr(pyfs, "execute_fsm_script"):
        # versões antigas executam o último script gravado no CWD
        pyfs.execute_fsm_script(fsexe_path=FS_EXE, hidden=True)
    else:
        raise RuntimeError("pyFlightscript: não encontrei run_script/execute_fsm_script.")

def _new_simulation():
    """new_simulation compatível (mudou de lugar em versões)."""
    if hasattr(pyfs, "fsinit") and hasattr(pyfs.fsinit, "new_simulation"):
        pyfs.fsinit.new_simulation()
    elif hasattr(pyfs, "new_simulation"):
        pyfs.new_simulation()
    else:
        raise RuntimeError("pyFlightscript: não encontrei new_simulation().")

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
        # se a função não existir nesta versão, só avisa e segue
        print(f"[aviso] não achei set_solver.solver_iterations; mantendo default do FS.")

# -------------------------------------------------------------------------------

def run_case(p3d_path: Path):
    case = case_name_from_path(p3d_path)
    work = RUNS_DIR / case
    work.mkdir(parents=True, exist_ok=True)

    # Isola cada caso no seu diretório (script + outputs ficam dentro)
    cwd0 = Path.cwd()
    os.chdir(work)
    try:
        _reset_script(Path(SCRIPT_NAME))

        # --- Macro: começa a simulação e define unidades
        _new_simulation()
        _set_length_units("METER")

        # --- Importa a malha (PLOT3D)
        ext = Path(p3d_path).suffix.lower()
        ftype = {".p3d": "P3D", ".stl": "STL"}.get(ext, "P3D")
        pyfs.mesh.import_mesh(str(p3d_path), units="METER", file_type = ftype, clear=True)

        # --- Freestream + fluido  (substituir o bloco antigo por este)
        # 1) tipo de escoamento (constante no tempo/espacialmente uniforme)
        pyfs.freestream.set_freestream(freestream_type="CONSTANT")  # só define o tipo

        # 2) propriedades do fluido (densidade/viscosidade etc.)
        pyfs.freestream.fluid_properties(
            density=FLOW["density"],
            viscosity=FLOW["viscosity"],
            # pressure=101325.0, temperature=288.15, sonic_velocity=340.0  # (opcionais)
        )

        # 3) condições do solver: velocidade/ângulos (dimensional)
        pyfs.set_solver.solver_velocity(FLOW["velocity"])
        pyfs.set_solver.aoa(FLOW["aoa"])
        pyfs.set_solver.sideslip(FLOW["sideslip"])

        # --- Solver
        pyfs.solver.initialize_solver(solver_model="INCOMPRESSIBLE", surfaces=-1)
        _set_iterations(SOLVER_ITERS)

        # --- Rodar
        pyfs.exec_solver.start_solver()

        # --- Exportar resultados
        pyfs.export_data.export_solver_analysis_csv("C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/versao_04/runs_pyfs/analysis.csv")

        # --- Fechar FS (na macro)
        pyfs.exec_solver.close_flightstream()

        # --- Gravar e executar macro
        _write_and_run(Path(SCRIPT_NAME))

        print(f"[OK] {case}")

    finally:
        os.chdir(cwd0)
        # limpa buffer para o próximo caso (não falha se não existir)
        try:
            if hasattr(pyfs, "script") and hasattr(pyfs.script, "clear_lines"):
                pyfs.script.clear_lines()
        except Exception:
            pass

def main():
    p3ds = sorted(GEOM_DIR.glob("*.p3d"))
    if not p3ds:
        print(f"Nenhum .p3d encontrado em {GEOM_DIR}")
        return
    for p3d in p3ds:
        run_case(p3d)

if __name__ == "__main__":
    main()
