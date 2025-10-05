# run_case.py
from pathlib import Path
import os
import pyFlightscript as pyfs

from shared import (
    GEOM_DIR, RUNS_DIR, LOGS_DIR, SCRIPT_NAME,
    FLOW, SOLVER_ITERS,
    case_name_from_path,
    _reset_script, _new_simulation, _set_length_units, _set_iterations, _write_and_run
)

def run_case(p3d: Path):
    case = case_name_from_path(p3d)
    run_dir = (RUNS_DIR / case).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # saídas
    csv_out  = (run_dir / f"{case}_solver.csv").resolve()
    log_out  = (LOGS_DIR / f"{case}.log").resolve()
    script_p = (run_dir / SCRIPT_NAME).resolve()

    cwd0 = Path.cwd()
    try:
        os.chdir(run_dir)

        # 0) macro: reset + mensagem (útil p/ localizar no log do FS)
        _reset_script()
        if hasattr(pyfs, "fsinit") and hasattr(pyfs.fsinit, "print_message"):
            pyfs.fsinit.print_message(message=f"=== Início do case: {case} ===")

        # 1) nova simulação e unidades
        _new_simulation()
        _set_length_units("METER")

        # 2) importar geometria (PLOT3D/P3D)
        # A doc da API expõe import_mesh(geometry_filepath, units, file_type, clear) — padrão 'STL'.
        # Para PLOT3D, use 'P3D' aqui (a camada do pyFlightscript mapeia corretamente para o macro).
        # https docs: pyFlightscript.mesh.import_mesh(...)  (ver seção mesh.import_mesh)
        pyfs.mesh.import_mesh(
            geometry_filepath=str(p3d.resolve()),
            units="METER",
            file_type="P3D",
            clear=True
        )

        # 3) freestream + fluido + condições de solver
        # set_freestream('CONSTANT') e depois velocidade/aoa/beta
        pyfs.freestream.set_freestream(freestream_type="CONSTANT")
        pyfs.freestream.fluid_properties(
            density=FLOW["density"],
            viscosity=FLOW["viscosity"]
        )
        # Coisas básicas de solver (API set_solver.*):
        if hasattr(pyfs, "set_solver"):
            pyfs.set_solver.ref_area(1.0)
            pyfs.set_solver.ref_length(1.0)
            pyfs.set_solver.solver_velocity(FLOW["velocity"])
            pyfs.set_solver.aoa(FLOW["aoa"])
            pyfs.set_solver.sideslip(FLOW["sideslip"])
            # use o máximo de núcleos disponíveis
            if hasattr(pyfs.set_solver, "set_max_parallel_threads"):
                pyfs.set_solver.set_max_parallel_threads(os.cpu_count() or 4)
            # convergência/iter
            if hasattr(pyfs.set_solver, "convergence_threshold"):
                pyfs.set_solver.convergence_threshold(1e-5)
            _set_iterations(SOLVER_ITERS)

        # 4) inicializar e rodar solver
        # initialize_solver(solver_model="INCOMPRESSIBLE", surfaces=-1) está na doc 2025.1
        pyfs.solver.initialize_solver(solver_model="INCOMPRESSIBLE", surfaces=-1)
        pyfs.exec_solver.start_solver()  # linha de macro que dispara o solver

        # 5) exportar resultados e log
        # export_solver_analysis_csv(...): formatos/units conforme doc
        pyfs.export_data.export_solver_analysis_csv(
            file_path=str(csv_out),
            format_value="PRESSURE",
            units="PASCALS",
            frame=1,
            surfaces=-1
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
