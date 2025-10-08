from pathlib import Path
from itertools import product
from ground_generator import create_p3d_half_plane_ysymmetry

# ----------------- parâmetros do sweep -----------------
c = 5.625
altura = 2.8125
larguras = [2 * c, 4 * c, 8 * c, 10 * c, 20 * c]

# --- CORREÇÃO: Ajustada a segunda definição de malha para não gerar duplicatas após o int() ---
# A segunda fórmula foi alterada de [2*(4*c)/10, 4*c/10] para [2*(6*c)/12, (6*c)/12]
# resultando em malhas únicas: (4, 2), (5, 2) e (6, 3)
mesh_definitions = [
    [2 * (2 * c) / 5, (2 * c) / 5],  # Resultará em NI=4, NJ=2
    [2 * (6 * c) / 12, (6 * c) / 12],  # Resultará em NI=5, NJ=2 (AGORA É ÚNICO)
    [2 * (8 * c) / 15, 8 * c / 15],
    [2 * (10 * c) / 20, 10 * c / 20],
    [2 * (20 * c) / 25, 20 * c / 25]# Resultará em NI=6, NJ=3
]

# -------------------------------------------------------

saida_dir = Path('C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/ground_mesh')
saida_dir.mkdir(parents=True, exist_ok=True)

gerados = []

print("Iniciando geração de 9 planos de solo únicos...")
count = 1
for tamanho, mesh_dims in product(larguras, mesh_definitions):
    NI = int(mesh_dims[0])
    NJ = int(mesh_dims[1])

    largura_y = tamanho
    comprimento_x = tamanho * 2
    z_coord = -altura

    nome = f"{count}_plano_solo_L{largura_y:.2f}m_malha_{NI}x{NJ}_h{altura:.4f}.p3d"
    caminho = saida_dir / nome

    print(f"Gerando: {nome}...")

    create_p3d_half_plane_ysymmetry(
        filename=caminho,
        z_coord=z_coord,
        width=largura_y,
        length=comprimento_x,
        num_points_width=NJ,
        num_points_length=NI,
    )
    gerados.append(caminho)
    count += 1
print(f"\nOperação concluída. Arquivos gerados ({len(gerados)}):")
for g in gerados:
    print(" -", g)