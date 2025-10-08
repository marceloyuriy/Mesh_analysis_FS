# run_case.py
from pathlib import Path
import os
import pyFlightscript as pyfs

from shared import (
    FSM_FILE_PATH, # Importa o novo caminho
    RUNS_DIR, LOGS_DIR, SCRIPT_NAME,
    FLOW, SOLVER_ITERS,
    case_name_from_path,
    _reset_script, _write_and_run
)

def run_case(p3d: Path):
    case = case_name_from_path(p3d)
    run_dir = (RUNS_DIR / case).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # saídas
    csv_out  = (run_dir / f"{case}_solver.csv").resolve()
    log_out  = (LOGS_DIR / f"{case}.log").resolve()
    script_p = (run_dir / SCRIPT_NAME).resolve()

    if not FSM_FILE_PATH.exists():
        raise FileNotFoundError(f"Arquivo FSM base não encontrado em: {FSM_FILE_PATH}")

    cwd0 = Path.cwd()
    try:
        os.chdir(run_dir)

        # 1) CARREGAR O PROJETO .FSM EXISTENTE
        # Este é o passo mais importante. Substitui o _new_simulation().
        pyfs.fsinit.open_fsm(str(FSM_FILE_PATH))

        pyfs.mesh.import_mesh(
            geometry_filepath=str(p3d.resolve()),
            units="METER",
            file_type="P3D",
            clear=False  # MUITO IMPORTANTE!
        )

        # inicializar e rodar solver
        # initialize_solver(solver_model="INCOMPRESSIBLE", surfaces=-1) está na doc 2025.1
        pyfs.solver.initialize_solver(solver_model="INCOMPRESSIBLE", surfaces=-1)
        pyfs.exec_solver.start_solver()  # linha de macro que dispara o solver

        # exportar resultados e log
        # export_solver_analysis_csv(...): formatos/units conforme doc
        pyfs.export_data.export_solver_analysis_spreadsheet(
            str(csv_out)
        )
        # log de execução (muito útil p/ ver se travou em algo)
        if hasattr(pyfs, "log") and hasattr(pyfs.log, "export_log"):
            pyfs.log.export_log(str(log_out))

        # 6) fechar FS ao final
        pyfs.exec_solver.close_flightstream()

        # 7) gravar e executar macro
        res = _write_and_run(script_p)
        print(f"[OK] {case}  -> returncode={getattr(res,'returncode',None)}")

    finally:
        os.chdir(cwd0)
        # limpa buffer do macro p/ próximo case
        try:
            if hasattr(pyfs, "script") and hasattr(pyfs.script, "clear_lines"):
                pyfs.script.clear_lines()
        except Exception:
            pass
