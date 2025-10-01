# gerenciador_analises.py (VERSÃO COM CORREÇÃO DE FORMATAÇÃO)

import os
import subprocess
import textwrap
from ground_generator import create_p3d_half_plane_ysymmetry

# --- CONFIGURAÇÕES DA SIMULAÇÃO ---

flightstream_exe = r"C:/Altair/2025.1/flightstream/FlightStream_25.1_Windows_x86_64.exe"
veiculo_geometria = r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/geometria/AR021D_OGE.fsm"
gerador_solo_script = r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/ground_generator.py"
config_output_dir = r'C:\Users\marce\PycharmProjects\Analise_malha_solo_FS\FS_config'
output_dir = r"C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/output"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(config_output_dir, exist_ok=True)

# --- PARÂMETROS PARA A VARREDURA ---
alturas_teste = [1.0, 2.0, 3.0]
tamanhos_solo = [30]
mesh = [[21,41],[11,22]]
# --- IDs DAS SUPERFÍCIES NO FLIGHTSTREAM ---
IDS_SUPERFICIES_VEICULO = [80, 81, 82, 83, 84, 85, 86]
ID_SUPERFICIE_SOLO = 137

# --- LOOP DE EXECUÇÃO ---
for altura in alturas_teste:
    for tamanho in tamanhos_solo:
        print(f"--- Iniciando análise para Altura = {altura}m, Tamanho do Solo = {tamanho}m ---")

        # 1. Gerar o arquivo de malha para o plano do solo
        nome_arquivo_solo = f"plano_solo_{tamanho}m.stl"
        caminho_arquivo_solo = os.path.join(output_dir, nome_arquivo_solo)

        print(f"Gerando malha do solo: {nome_arquivo_solo}")
        #def create_p3d_half_plane_ysymmetry(filename, z_coord , width, length, num_points_width, num_points_length):
        create_p3d_half_plane_ysymmetry(gerador_solo_script, altura, tamanho, tamanho, mesh[0][0], mesh[0][1])

        # 2. Gerar o script do FlightStream para esta configuração
        nome_script_fs = f"script_h{altura}_s{tamanho}.txt"
        caminho_script_fs = os.path.join(config_output_dir, nome_script_fs)

        nome_arquivo_resultados = f"resultados_h{altura}_s{tamanho}.txt"
        caminho_arquivo_resultados = os.path.join(output_dir, nome_arquivo_resultados)

        # Conteúdo do script do FlightStream (sem alterações aqui)
        script_content_raw = f"""
# Script de Análise de Efeito Solo para FlightStream
# Configuração: Altura={altura}m, Tamanho do Solo={tamanho}m

OPEN
{veiculo_geometria}

IMPORT
UNITS METER
FILE_TYPE STL
FILE {caminho_arquivo_solo}

# Exclui o plano do solo (ID {ID_SUPERFICIE_SOLO}) dos cálculos de camada limite viscosa.
SET_VISCOUS_EXCLUDED_BOUNDARIES 1
{ID_SUPERFICIE_SOLO}

# Define os parâmetros de simulação
SOLVER_SET_AOA 0.0
SOLVER_SET_VELOCITY 25.0
SOLVER_SET_ITERATIONS 1000
SOLVER_SET_CONVERGENCE 1E-5

# Inicializa o solver com TODAS as superfícies
INITIALIZE_SOLVER
SOLVER_MODEL SUBSONIC_PRANDTL_GLAUERT
SURFACES -1

# Inicia a execução do solver
START_SOLVER

# Exporta a planilha de análise
EXPORT_SOLVER_ANALYSIS_SPREADSHEET
{caminho_arquivo_resultados}

# Fecha o FlightStream
CLOSE_FLIGHTSTREAM
"""

        # <-- AJUSTE APLICADO AQUI -->
        # Remove a indentação comum do bloco de texto para que cada linha comece no caractere 0
        script_content_final = textwrap.dedent(script_content_raw).strip()

        # Salva o script corrigido
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