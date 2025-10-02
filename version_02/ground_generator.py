# ground_generator.py (VERSÃO AJUSTADA)

import numpy as np

def create_p3d_half_plane_ysymmetry(filename, z_coord, width, length, num_points_width, num_points_length):
    """
    Gera um arquivo .p3d representando um MEIO plano retangular no eixo Y positivo.
    Ideal para análises de simetria no FlightStream.

    Args:
        filename (str): Nome do arquivo de saída (ex: 'ground_plane.p3d').
        z_coord (float): Coordenada Z do plano (deve ser 0.0 para efeito solo).
        width (float): Largura do MEIO plano (extensão no eixo Y a partir de y=0).
        length (float): Comprimento total do plano (na direção X).
        num_points_width (int): Número de pontos na largura (j).
        num_points_length (int): Número de pontos no comprimento (i).
    """
    y_origin_simetria = 0.0
    
    # Centraliza o plano no eixo X
    x_start = -length / 2.0
    x_end = length / 2.0

    # O plano começa em y=0 e se estende
    y_start = y_origin_simetria
    y_end = y_origin_simetria + width

    # Cria as grades de coordenadas
    x_coords = np.linspace(x_start, x_end, num_points_length)
    y_coords = np.linspace(y_start, y_end, num_points_width)
    
    xx, yy = np.meshgrid(x_coords, y_coords, indexing='ij')
    zz = np.full(xx.shape, z_coord)

    # Aplana as matrizes na ordem correta para o formato P3D (Fortran 'F')
    x_flat = xx.flatten(order='F')
    y_flat = yy.flatten(order='F')
    z_flat = zz.flatten(order='F')

    try:
        with open(filename, 'w') as f:
            f.write(" 1\n") # 1 bloco de malha
            f.write(f" {num_points_length} {num_points_width} 1\n") # Dimensões i, j, k

            # Escreve as coordenadas em blocos X, depois Y, depois Z
            np.savetxt(f, [x_flat], fmt=' % .8e')
            np.savetxt(f, [y_flat], fmt=' % .8e')
            np.savetxt(f, [z_flat], fmt=' % .8e')

        print(f"Arquivo P3D '{filename}' gerado com sucesso.")

    except Exception as e:
        print(f"ERRO ao escrever o arquivo P3D: {e}")


# --- SEÇÃO DE EXECUÇÃO (PARA TESTE INDIVIDUAL DO SCRIPT) ---
if __name__ == "__main__":
    
    # Parâmetros de exemplo para teste
    output_filename = "chao_simetria_teste.p3d"
    
    create_p3d_half_plane_ysymmetry(
        filename=output_filename,
        z_coord=0.0,
        width=50.0,        # Meia-largura (de y=0 a y=50)
        length=100.0,      # Comprimento total (de x=-50 a x=50)
        num_points_width=21,  # nj
        num_points_length=41  # ni
    )