# ground_generator.py
import numpy as np
from pathlib import Path
from typing import Iterable, Union

def _write_numbers(fp, arr: Iterable[float], per_line: int = 6) -> None:
    line = []
    for v in arr:
        line.append(f"{v:.8E}")
        if len(line) == per_line:
            fp.write(" ".join(line) + "\n")
            line = []
    if line:
        fp.write(" ".join(line) + "\n")

def _write_plot3d_single_block(filepath: Union[str, Path], X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> None:
    """
    Escreve um PLOT3D ASCII com 1 bloco.
    Arrays devem estar em shape (NI, NJ).
    Ordem Fortran (coluna-major) é usada na saída, como o FS espera.
    """
    filepath = Path(filepath)
    NI, NJ = X.shape
    NK = 1
    with open(filepath, "w") as f:
        f.write("1\n")                    # n_blocks
        f.write(f"{NI} {NJ} {NK}\n")      # dims do bloco
        _write_numbers(f, X.flatten(order="F"))
        _write_numbers(f, Y.flatten(order="F"))
        _write_numbers(f, Z.flatten(order="F"))

def create_p3d_half_plane_ysymmetry(
    filename: Union[str, Path],
    z_coord: float,
    width: float,
    length: float,
    num_points_width: int,
    num_points_length: int,
) -> None:
    # y >= 0 (meio-plano)
    half_L = length / 2.0
    x = np.linspace(-half_L, +half_L, num_points_length)
    y = np.linspace(0.0, width, num_points_width)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    zz = np.full_like(xx, fill_value=z_coord, dtype=float)
    _write_plot3d_single_block(filename, xx, yy, zz)

def create_p3d_plane_centered(
    filename: Union[str, Path],
    z_coord: float,
    L_total: float,
    W_total: float,
    NI: int,
    NJ: int,
) -> None:
    """
    Plano retangular centrado em (0,0,z_coord), cobrindo
      x ∈ [-L_total/2, +L_total/2], y ∈ [-W_total/2, +W_total/2]
    Saída: PLOT3D ASCII (1 bloco).
    """
    x = np.linspace(-L_total/2.0, +L_total/2.0, NI)
    y = np.linspace(-W_total/2.0, +W_total/2.0, NJ)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    zz = np.full_like(xx, fill_value=z_coord, dtype=float)
    _write_plot3d_single_block(filename, xx, yy, zz)

# --- API amigável para o sweep ---
def generate_ground_p3d_by_count(
    L_total: float,
    W_total: float,
    h: float,
    NI: int,
    NJ: int,
    output_path: Union[str, Path],
) -> None:
    """
    Mesma assinatura que você já usava, mas agora grava PLOT3D válido.
    """
    create_p3d_plane_centered(
        filename=output_path,
        z_coord=-abs(h),    # solo “abaixo” da origem
        L_total=L_total,
        W_total=W_total,
        NI=NI,
        NJ=NJ,
    )
    print(f"Malha PLOT3D '{Path(output_path).name}' gerada ({NI}x{NJ} nós).")
