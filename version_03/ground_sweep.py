from pathlib import Path
from itertools import product

from ground_generator import create_p3d_half_plane_ysymmetry  # mesma função já usada

# ----------------- parâmetros do sweep -----------------
altura = 2.8125                             # altura do ponto de referência (m)
largura_m = [15, 30, 40]                # largura (y) do meio-plano; comprimento (x) = 2*largura
mesh_base = [[21, 11], [41, 21], [61, 31]]  # [NI, NJ] = [pts em x, pts em y]
# -------------------------------------------------------

saida_dir = Path('C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/version_03/ground_mesh')
saida_dir.mkdir(parents=True, exist_ok=True)

gerados = []

for tamanho, (NI, NJ) in product(largura_m, mesh_base):
    largura_y = tamanho
    comprimento_x = tamanho * 2
    z_coord = -altura                         # plano no nível -altura (ajuste se quiser z=+altura)

    nome = f"plano_solo_{tamanho}m_{NI}x{NJ}_h{altura:.4f}.p3d"
    caminho = (saida_dir / nome).as_posix()

    # Atenção à assinatura: (filename, z, width=Y, length=X, num_points_width=NJ, num_points_length=NI)
    create_p3d_half_plane_ysymmetry(
        filename=caminho,
        z_coord=z_coord,
        width=largura_y,
        length=comprimento_x,
        num_points_width=NJ,
        num_points_length=NI,
    )
    gerados.append(caminho)

print(f"Arquivos gerados ({len(gerados)}):")
for g in gerados:
    print(" -", g)
