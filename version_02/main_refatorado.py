# main.py

import os
import subprocess
import textwrap
import csv
from ground_generator import create_p3d_half_plane_ysymmetry

# --- CONFIGURAÇÕES DA SIMULAÇÃO ---
# Use os.path.join para compatibilidade entre sistemas operacionais
project_base_path = 'C:/Users/marce/PycharmProjects/Analise_malha_solo_FS'

flightstream_exe = r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe"
veiculo_geometria = os.path.join(project_base_path, 'geometria', 'AR021D_OGE.fsm')
geo_dir = os.path.join(project_base_path, 'geometria')
output_dir = os.path.join(project_base_path, 'output')
config_output_dir = os.path.join(project_base_path, 'FS_script')

os.makedirs(output_dir, exist_ok=True)
os.makedirs(config_output_dir, exist_ok=True)

# --- PARÂMETROS PARA A VARREDURA ---
altura = 2.8125
tamanhos_solo = [30]
mesh_base = [21, 11]
mesh_configs = {'fina': [2 * mesh_base[0], mesh_base[0]], 'grossa': [2 * mesh_base[1], mesh_base[1]]}
# --- IDs DAS SUPERFÍCIES NO FLIGHTSTREAM ---
IDS_SUPERFICIES_VEICULO = [80, 81, 82, 83, 84, 85, 86]
ID_SUPERFICIE_SOLO = 137

# --- PREPARAÇÃO PARA O CSV ---
resultados_finais = []
csv_header = ['altura_m', 'tamanho_solo_m', 'mesh_ni', 'mesh_nj', 'CL', 'CDi', 'CDo', 'CD_Total', 'L_D', 'CMz']

# --- LOOP DE EXECUÇÃO ---
for nome_mesh, mesh_dims in mesh_configs.items():
    for tamanho in tamanhos_solo:
        ni, nj = mesh_dims
        print(f"--- Iniciando: Altura={altura}m, Solo={tamanho}m, Malha Solo='{nome_mesh}' ({ni}x{nj}) ---")

        nome_arquivo_solo = f"plano_solo_{tamanho}_m_mesh_{nome_mesh}.p3d"
        caminho_arquivo_solo = os.path.join(geo_dir, nome_arquivo_solo)

        print(f"Gerando malha do solo: {nome_arquivo_solo}")
        create_p3d_half_plane_ysymmetry(
            filename=caminho_arquivo_solo, z_coord=-altura, width=tamanho,
            length=tamanho * 2, num_points_width=nj, num_points_length=ni
        )

        run_id = f"h{altura}_s{tamanho}_m{nome_mesh}"
        nome_script_fs = f"script_{run_id}.txt"
        caminho_script_fs = os.path.join(config_output_dir, nome_script_fs)
        nome_arquivo_resultados_txt = f"resultados_{run_id}.txt"
        caminho_arquivo_resultados_txt = os.path.join(output_dir, nome_arquivo_resultados_txt)
        caminho_arquivo_resultados_txt_fs = os.path.join(config_output_dir, f"resultados_{run_id}_FS_CONFIG.txt")

        script_content_raw = f"""
        OPEN
        {veiculo_geometria}
        IMPORT
        UNITS METER
        FILE {caminho_arquivo_solo}
        CLEAR
        SET_VISCOUS_EXCLUDED_BOUNDARIES 1
        {ID_SUPERFICIE_SOLO}
        SOLVER_SET_REF_VELOCITY 15.0
        SOLVER_SET_REF_LENGTH 5.625
        SOLVER_SET_REF_AREA 36.9
        SOLVER_SET_AOA 0.0
        SOLVER_SET_VELOCITY 15.0
        SOLVER_SET_ITERATIONS 1000
        SOLVER_SET_CONVERGENCE 1E-5
        REMOVE_INITIALIZATION
        INITIALIZE_SOLVER
        SOLVER_MODEL INCOMPRESSIBLE
        SYMMETRY MIRROR
        SURFACES -1
        WAKE_TERMINATION_X DEFAULT
        START_SOLVER
        EXPORT_SOLVER_ANALYSIS_SPREADSHEET
        {caminho_arquivo_resultados_txt_fs}
        CLOSE_FLIGHTSTREAM
        """
        script_content_final = textwrap.dedent(script_content_raw).strip()
        with open(caminho_script_fs, 'w') as f:
            f.write(script_content_final)

        print(f"Script FlightStream gerado: {nome_script_fs}")

        print("Iniciando FlightStream em modo batch...")
        try:
            log_file = os.path.join(project_base_path, "FlightStreamLog.txt")
            if os.path.exists(log_file):
                os.remove(log_file)

            # Executa o FlightStream a partir do diretório do projeto para garantir que o log seja gerado lá
            subprocess.run([flightstream_exe, "-script", caminho_script_fs, "-hidden"], check=True,
                           cwd=project_base_path, capture_output=True, text=True)

            print(f"Lendo resultados de: {nome_arquivo_resultados_txt}")
            # ... (código de leitura de resultados permanece o mesmo) ...

        except subprocess.CalledProcessError as e:
            print(f"ERRO: O FlightStream encerrou com um erro.")
            print("--- Conteúdo do Log do FlightStream ---")
            if os.path.exists(log_file):
                with open(log_file, 'r') as log:
                    print(log.read())
            else:
                print("Arquivo de log não encontrado. O erro pode ter ocorrido antes da inicialização do log.")
                print(f"Output do Subprocess (stdout):\n{e.stdout}")
                print(f"Output de Erro do Subprocess (stderr):\n{e.stderr}")

        except (IOError, IndexError, ValueError) as e:
            print(f"ERRO ao processar o arquivo de resultados: {e}")
            print("Verifique se o FlightStream executou corretamente e gerou o arquivo de saída.")

# --- FINALIZAÇÃO ---
# (código de finalização permanece o mesmo)