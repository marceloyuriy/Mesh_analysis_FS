import numpy as np
from typing import Iterable, Union
from pathlib import Path # Importar Path

# A função _write_numbers está perfeita, sem alterações.
def _write_numbers(fp, arr: Iterable[float], per_line: int = 6) -> None:
    """Escreve valores em notação científica, per_line por linha (estilo Fortran)."""
    line = []
    for v in arr:
        line.append(f"{v:.8E}")
        if len(line) == per_line:
            fp.write(" ".join(line) + "\n")
            line = []
    if line:
        fp.write(" ".join(line) + "\n")

def create_p3d_half_plane_ysymmetry(
    # << MELHORIA: Aceitar string ou objeto Path, mais moderno.
    filename: Union[str, Path],
    z_coord: float,
    width: float,
    length: float,
    num_points_width: int,
    num_points_length: int,
) -> None: # << MELHORIA: Adicionar o tipo de retorno -> None
    """
    Gera um arquivo PLOT3D ASCII (1 bloco) para um MEIO PLANO:
      - eixo x: comprimento (NI = num_points_length)
      - eixo y: largura (NJ = num_points_width), apenas y >= 0
      - eixo z: constante = z_coord (NK = 1)
    Formatação robusta: 6 valores por linha, notação científica.
    """
    half_L = length / 2.0
    x = np.linspace(-half_L, +half_L, num_points_length)
    y = np.linspace(0.0, width, num_points_width)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    zz = np.full_like(xx, fill_value=z_coord, dtype=float)

    x_flat = xx.flatten(order="F")
    y_flat = yy.flatten(order="F")
    z_flat = zz.flatten(order="F")

    NI, NJ, NK = num_points_length, num_points_width, 1

    with open(filename, "w") as f:
        f.write("1\n")
        f.write(f"{NI} {NJ} {NK}\n")
        _write_numbers(f, x_flat, per_line=6)
        _write_numbers(f, y_flat, per_line=6)
        _write_numbers(f, z_flat, per_line=6)