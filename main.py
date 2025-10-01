# gerenciador_analises.py (VERSÃO FINAL COM ID DO SOLO CORRIGIDO)

import os
import subprocess

# --- CONFIGURAÇÕES DA SIMULAÇÃO ---
# Caminho para o executável do FlightStream
FLIGHTSTREAM_EXEC = r"C:\Altair\2025.1\flightstream\FlightStream_25.1_Windows_x86_64.exe"

# Caminho para o seu arquivo .fsm base do veículo
VEHICULO_FSM_PATH = r"C:\Users\marce\PycharmProjects\Analise_malha_solo_FS\geometria\AR021D_OGE.fsm"

# Caminho para o seu script que gera o plano do solo
GERADOR_SOLO_SCRIPT = r"C:\Users\marce\PycharmProjects\Analise_malha_solo_FS\criar_plano.py"

# Diretório para salvar os resultados
OUTPUT_DIR = r"C:\Users\marce\PycharmProjects\Analise_malha_solo_FS\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- PARÂMETROS PARA A VARREDURA ---
alturas_teste = [1.0]  # em metros
tamanhos_solo = [30, 100]  # dimensão característica do plano do solo em metros

# --- IDs DAS SUPERFÍCIES NO FLIGHTSTREAM ---
# IDs dos componentes do veículo, conforme fornecido
IDS_SUPERFICIES_VEICULO = [80, 81, 82, 83, 84, 85, 86]

# ID da superfície do solo, CONFIRMADO MANUALMENTE PELO USUÁRIO.
ID_SUPERFICIE_SOLO = 137

# --- LOOP DE EXECUÇÃO ---
for altura in alturas_teste:
    for tamanho in tamanhos_solo:
        print(f"--- Iniciando análise para Altura = {altura}m, Tamanho do Solo = {tamanho}m ---")

        # 1. Gerar o arquivo de malha para o plano do solo
        nome_arquivo_solo = f"plano_solo_{tamanho}m.stl"
        caminho_arquivo_solo = os.path.join(OUTPUT_DIR, nome_arquivo_solo)

        print(f"Gerando malha do solo: {nome_arquivo_solo}")
        subprocess.run([
            "python", GERADOR_SOLO_SCRIPT,
            "--tamanho", str(tamanho),
            "--output", caminho_arquivo_solo
        ], check=True)

        # 2. Gerar o script do FlightStream para esta configuração
        nome_script_fs = f"script_h{altura}_s{tamanho}.txt"
        caminho_script_fs = os.path.join(OUTPUT_DIR, nome_script_fs)

        nome_arquivo_resultados = f"resultados_h{altura}_s{tamanho}.txt"
        caminho_arquivo_resultados = os.path.join(OUTPUT_DIR, nome_arquivo_resultados)

        # Gera a seção de comandos de translação para cada componente do veículo
        comandos_translacao = ""
        for comp_id in IDS_SUPERFICIES_VEICULO:
            comandos_translacao += f"TRANSLATE_SURFACE_IN_FRAME {comp_id} 1 0.0 0.0 {altura} METER ENABLE\n"

        # Conteúdo do script do FlightStream
        script_content = f"""
# Script de Análise de Efeito Solo para FlightStream
# Configuração: Altura={altura}m, Tamanho do Solo={tamanho}m

# Abre o arquivo .fsm base que já contém o veículo
OPEN
{VEHICULO_FSM_PATH}

# Importa a malha do plano do solo gerada
IMPORT
UNITS METER
FILE_TYPE STL
FILE {caminho_arquivo_solo}

# Translada CADA COMPONENTE do VEÍCULO para a altura de voo desejada (eixo Z)
{comandos_translacao}

# --- CONFIGURAÇÕES DA FÍSICA E SOLVER ---

# Exclui o plano do solo (ID {ID_SUPERFICIE_SOLO}) dos cálculos de camada limite viscosa.
SET_VISCOUS_EXCLUDED_BOUNDARIES 1
{ID_SUPERFICIE_SOLO}

# Define os parâmetros de simulação

SOLVER_SET_AOA 0.0
SOLVER_SET_VELOCITY 25.0 # m/s
SOLVER_SET_ITERATIONS 1000
SOLVER_SET_CONVERGENCE 1E-5

# Inicializa o solver com TODAS as superfícies
INITIALIZE_SOLVER
SOLVER_MODEL SUBSONIC_PRANDTL_GLAUERT
SURFACES -1

# Inicia a execução do solver
START_SOLVER

# --- EXPORTAÇÃO DE RESULTADOS ---

# Exporta a planilha de análise
EXPORT_SOLVER_ANALYSIS_SPREADSHEET
{caminho_arquivo_resultados}

# Fecha o FlightStream
CLOSE_FLIGHTSTREAM
"""
        # Salva o script gerado
        with open(caminho_script_fs, 'w') as f:
            f.write(script_content)

        print(f"Script FlightStream gerado: {nome_script_fs}")

        # 3. Executar o FlightStream com o script gerado
        print("Iniciando FlightStream em modo batch...")
        subprocess.run([
            FLIGHTSTREAM_EXEC,
            "-script", caminho_script_fs,
            "-hidden"
        ], check=True)

        print(f"Análise concluída. Resultados salvos em: {nome_arquivo_resultados}")

print("--- Todas as análises foram concluídas. ---")