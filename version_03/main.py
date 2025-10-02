# gerenciador_analises.py (VERSÃO COM CORREÇÃO DE FORMATAÇÃO)

import os
import subprocess
import textwrap
from ground_generator import create_p3d_half_plane_ysymmetry

# --- CONFIGURAÇÕES DA SIMULAÇÃO ---

def bslash(path: str) -> str:
    return path.replace('/', '\\')

flightstream_exe = bslash(r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe")
veiculo_geometria = bslash(r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/geometria/AR021D_OGE.fsm")
gerador_solo_script = bslash(r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/ground_generator.py")
config_output_dir = bslash(r'/version_03/FS_script')
output_dir = bslash(r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/output")
ground_mesh = bslash(r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/ground_mesh")

os.makedirs(output_dir, exist_ok=True)
os.makedirs(config_output_dir, exist_ok=True)
os.makedirs(ground_mesh, exist_ok=True)

# --- PARÂMETROS PARA A VARREDURA ---
altura = 2.8125
tamanhos_solo = [30, 50, 70]
mesh_base = [[11, 21], [21, 41], [31, 61]]
mesh_configs = {'11_elem': [2 * mesh_base[0][0], mesh_base[0][1]], '21_elem': [2 * mesh_base[1][0], mesh_base[1][1]],
                '31_elem': [2 * mesh_base[2][0], mesh_base[2][1]]}

# --- IDs DAS SUPERFÍCIES NO FLIGHTSTREAM ---
IDS_SUPERFICIES_VEICULO = [80, 81, 82, 83, 84, 85, 86]
ID_SUPERFICIE_SOLO = 137

print(mesh_configs.items())

# --- LOOP DE EXECUÇÃO ---
for nome_mesh, mesh_dims in mesh_configs.items():
    for tamanho in tamanhos_solo:
        ni, nj = mesh_dims
        print(f"--- Iniciando análise para Altura = {altura}m, Tamanho do Solo = {tamanho}m ---")

        # 1. Gerar o arquivo de malha para o plano do solo
        nome_arquivo_solo = f"plano_solo_{tamanho}m.p3d"
        caminho_arquivo_solo = bslash(f'C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/ground_mesh/{nome_arquivo_solo}')

        print(f"Gerando malha do solo: {nome_arquivo_solo}")
        create_p3d_half_plane_ysymmetry(caminho_arquivo_solo,-altura,tamanho, tamanho * 2, nj, ni)

        # 2. Gerar o script do FlightStream para esta configuração
        nome_script_fs = f"script_h{altura}_s{tamanho}.txt"
        caminho_script_fs = bslash(f'/version_03/FS_script/{nome_script_fs}')

        nome_arquivo_resultados = f"resultados_h{altura}_s{tamanho}.txt"
        caminho_arquivo_resultados = bslash(f'C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/output/{nome_arquivo_resultados}')

        # Formata os IDs do veículo para o script - > tem como objetivo limitar a analise para apenas as superficies do veiculo
        num_boundaries_veiculo = len(IDS_SUPERFICIES_VEICULO)
        boundaries_veiculo_str = ",".join(map(str, IDS_SUPERFICIES_VEICULO))

        # Conteúdo do script do FlightStream (sem alterações aqui)
        script_content_raw = f"""
        OPEN
        {veiculo_geometria}
        SET_SIMULATION_LENGTH_UNITS METER
        
        IMPORT
        FILE {caminho_arquivo_solo}
        
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
        #Define que apenas as superficies do veiculo entram no calculo TOTAL ---
        SET_SOLVER_ANALYSIS_BOUNDARIES {num_boundaries_veiculo}
        {boundaries_veiculo_str}
        EXPORT_SOLVER_ANALYSIS_SPREADSHEET
        {caminho_arquivo_resultados}
        CLOSE_FLIGHTSTREAM
        """

        script_content_final = textwrap.dedent(script_content_raw).strip()
        with open(caminho_script_fs, 'w') as f:
            f.write(script_content_final)

        print(f"Script FlightStream gerado: {nome_script_fs}")
        # 3. Executar o FlightStream com o script gerado
        print("Iniciando FlightStream em modo batch...")
        subprocess.run([
            flightstream_exe,
            "-script", caminho_script_fs,
            "-hidden"
        ], check=True)

        print(f"Análise concluída. Resultados salvos em: {nome_arquivo_resultados}")

print("--- Todas as análises foram concluídas. ---")