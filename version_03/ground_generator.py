# ground_generator.py (VERSÃO COM CABEÇALHO CORRIGIDO)
# A única mudança é a remoção da primeira linha que escrevia "1".

import numpy as np
import os


def create_p3d_half_plane_ysymmetry(filename, z_coord, width, length, num_points_width, num_points_length):
    """
    Gera um arquivo .p3d com a formatação final corrigida, incluindo o cabeçalho.
    """
    origin = (0, 0, z_coord)

    print(f"Gerando arquivo '{os.path.basename(filename)}' com formato final...")

    half_length = length / 2.0
    x_start, x_end = origin[0] - half_length, origin[0] + half_length
    y_start, y_end = origin[1], origin[1] + width
    z_plane = origin[2]

    x_coords = np.linspace(x_start, x_end, num_points_length)
    y_coords = np.linspace(y_start, y_end, num_points_width)

    xx, yy = np.meshgrid(x_coords, y_coords, indexing='ij')
    zz = np.full(xx.shape, z_plane)

    x_flat = xx.flatten(order='F')
    y_flat = yy.flatten(order='F')
    z_flat = zz.flatten(order='F')

    try:
        with open(filename, 'w') as f:
            # --- MUDANÇA CRÍTICA ---
            # Removemos a linha "f.write("1\n")".
            # A primeira linha do arquivo será diretamente as dimensões da malha.
            f.write(f"{num_points_length} {num_points_width} 1\n")

            # A lógica de escrever um valor por linha continua, pois é a mais segura.
            for x_val in x_flat:
                f.write(f"{x_val:.8f}\n")

            for y_val in y_flat:
                f.write(f"{y_val:.8f}\n")

            for z_val in z_flat:
                f.write(f"{z_val:.8f}\n")

        print(f"Arquivo '{os.path.basename(filename)}' criado com sucesso.")

    except Exception as e:
        print(f"Ocorreu um erro ao escrever o arquivo: {e}")