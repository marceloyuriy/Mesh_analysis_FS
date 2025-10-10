# ground_sweep.py (versão aprimorada)
from pathlib import Path
# Importa a função original e a nossa nova função
from ground_generator import generate_ground_p3d_by_count

# --- Parâmetros da Simulação ---
# Use o diretório definido no seu script 'shared.py' para consistência
# Assumindo que a pasta 'ground_mesh' está um nível acima da pasta dos scripts
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = (SCRIPT_DIR.parent / "ground_mesh").resolve()
OUTPUT_DIR.mkdir(exist_ok=True)

# 1. Defina as características físicas do seu estudo
c = 5.625  # Corda média aerodinâmica (m)
altura = 2.8125  # Altura constante do solo (m)

# 2. Defina as dimensões do plano de solo que você quer testar
#    Estes são os comprimentos/larguras TOTAIS do plano.
larguras_totais = [6 * c, 9 * c]  # Exemplo: 4, 8 e 16 cordas

# 3. Defina as discretizações de malha que você quer testar (NI x NJ)
#    Esta é a parte principal: uma lista de tuplas (NI, NJ)
#    Uma boa prática é dobrar a densidade a cada passo.
meshes_to_test = [
    (60, 30),
    (90, 45)
]

# --- Loop de Geração ---

print(f"Iniciando a geração de malhas em: {OUTPUT_DIR}\n")
count = 1

for l_total in larguras_totais:
    # Para este estudo, vamos manter o plano quadrado (Comprimento = Largura)
    w_total = l_total

    for ni, nj in meshes_to_test:
        # --- Nomenclatura Correta e Automática do Arquivo ---
        # O nome agora reflete os parâmetros de forma clara e legível
        filename = f"{count}_plano_solo_L{l_total:.4f}m_malha_{ni}x{nj}_h{altura:.4f}.p3d"
        output_path = OUTPUT_DIR / filename

        # Chama a nossa NOVA função, passando a contagem de painéis
        generate_ground_p3d_by_count(
            L_total=l_total,
            W_total=w_total,
            h=altura,
            NI=ni,
            NJ=nj,
            output_path=output_path
        )
        count += 1

print(f"\n{count - 1} arquivos de malha PLOT3D gerados com sucesso em: {OUTPUT_DIR}")
