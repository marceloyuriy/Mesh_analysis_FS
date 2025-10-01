# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# SCRIPT ADAPTADO PARA GERAÇÃO DE MEIO PLANO .p3d (SIMETRIA EM Y)
# Engenheiro Aeronáutico: Gemini
# Data: 01/10/2025
# Análise baseada no arquivo 'Voadeiro.p3d'
# -----------------------------------------------------------------------------

import numpy as np


def create_p3d_half_plane_ysymmetry(filename, origin=(0, 0, 0), width=50.0, length=50.0,
                                    num_points_width=21, num_points_length=41):
    """
    Gera um arquivo .p3d representando um MEIO plano retangular que se estende
    apenas no eixo Y positivo, ideal para análises de simetria.

    Argumentos:
        filename (str): O nome do arquivo de saída (ex: 'ground_plane_sym.p3d').
        origin (tuple): As coordenadas (x, y, z) do ponto inicial do plano.
                          O 'y' deste 'origin' será o plano de simetria (geralmente y=0).
        width (float): A largura do MEIO plano (extensão total no eixo Y a partir da origem).
        length (float): O comprimento do plano (na direção X).
        num_points_width (int): Número de pontos na direção da largura (j).
        num_points_length (int): Número de pontos na direção do comprimento (i).
    """
    print(f"Gerando arquivo de MEIO PLANO '{filename}' para análise de simetria:")
    print(f"  - Plano de Simetria em: Y = {origin[1]}")
    print(f"  - Extensão em Y: de {origin[1]} até {origin[1] + width}")
    print(f"  - Dimensões: {length}m (comprimento) x {width}m (largura do meio plano)")
    print(f"  - Grade de Pontos: {num_points_length} (i) x {num_points_width} (j)")

    # --- LÓGICA MODIFICADA ---
    # Calcula os limites do plano em X, centrado na origem X.
    half_length = length / 2.0
    x_start, x_end = origin[0] - half_length, origin[0] + half_length

    # Calcula os limites do plano em Y, começando na origem Y e se estendendo positivamente.
    y_start = origin[1]
    y_end = origin[1] + width

    z_plane = origin[2]

    # Cria vetores de coordenadas para X e Y
    x_coords = np.linspace(x_start, x_end, num_points_length)
    y_coords = np.linspace(y_start, y_end, num_points_width)  # <<-- A MUDANÇA ESTÁ AQUI

    # O restante da lógica para escrever o arquivo permanece idêntico.
    xx, yy = np.meshgrid(x_coords, y_coords, indexing='ij')
    zz = np.full(xx.shape, z_plane)

    x_flat = xx.flatten(order='F')
    y_flat = yy.flatten(order='F')
    z_flat = zz.flatten(order='F')

    try:
        with open(filename, 'w') as f:
            f.write(" 1\n")
            f.write(f" {num_points_length} {num_points_width} 1\n")

            # Bloco de Coordenadas X
            for x_val in x_flat:
                f.write(f"  {x_val:e}")
            f.write("\n")

            # Bloco de Coordenadas Y
            for y_val in y_flat:
                f.write(f"  {y_val:e}")
            f.write("\n")

            # Bloco de Coordenadas Z
            for z_val in z_flat:
                f.write(f"  {z_val:e}")
            f.write("\n")

        print(f"\nArquivo '{filename}' criado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro ao escrever o arquivo: {e}")


# --- SEÇÃO DE EXECUÇÃO ---
if __name__ == "__main__":
    # Nome do arquivo de saída
    output_filename = "C:/Users/marce/PycharmProjects/Analise_malha_solo_FS/geometria/chao_simetria.p3d"

    # Dimensões (largura e comprimento) em metros
    # O 'width' agora é a largura do meio modelo (ex: a semi-envergadura do plano)
    plane_width = 50.0  # O plano irá de y=0 até y=50
    plane_length = 50.0  # O plano irá de x=-25 até x=25

    # Densidade da malha (número de pontos)
    points_in_length = 41  # ni
    points_in_width = 21  # nj (Pode usar menos pontos na direção da envergadura)

    # Posição da origem do plano. O y=0 será o plano de simetria.
    plane_origin_xyz = (0, 0, -3)

    # Chama a função para criar o arquivo
    create_p3d_half_plane_ysymmetry(filename=output_filename,
                                    origin=plane_origin_xyz,
                                    width=plane_width,
                                    length=plane_length,
                                    num_points_length=points_in_length,
                                    num_points_width=points_in_width)