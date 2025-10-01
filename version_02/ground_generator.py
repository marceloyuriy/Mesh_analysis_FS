
"""
ground_generator.py — Gera um plano em formato PLOT3D ASCII para usar como "ground/boundary" no FlightStream.

Formato gerado (single-zone, ASCII):
    1
    ni nj nk
    X(ni*nj*nk)  Y(ni*nj*nk)  Z(ni*nj*nk)

Obs.:
- O FlightStream aceita PLOT3D ASCII reticulado. Aqui geramos um plano retangular em z=z0.
- Para "meia-malha" (simetria Y=0), defina y_min=0 e posicione a aeronave no plano de simetria do FS.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np


def create_p3d_half_plane_ysymmetry(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    z0: float,
    ni: int, nj: int,
    out_path: str | Path,
    ascii_precision: int = 6
) -> Path:
    """
    Gera um plano PLOT3D ASCII.
    - x_min..x_max, y_min..y_max: domínio do plano
    - z0: cota do plano (altura do solo, ex.: z0=0 e a aeronave a h acima)
    - ni, nj: resolução do reticulado
    - out_path: caminho do arquivo .p3d

    Retorna Path(out_path).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    xs = np.linspace(x_min, x_max, ni)
    ys = np.linspace(y_min, y_max, nj)
    X, Y = np.meshgrid(xs, ys, indexing='xy')
    Z = np.full_like(X, float(z0))

    # Flatten em ordem Fortran (varia mais rápido em i)
    Xf = X.reshape(-1, order='F')
    Yf = Y.reshape(-1, order='F')
    Zf = Z.reshape(-1, order='F')

    with out_path.open('w', encoding='utf-8') as f:
        f.write("1\n")
        f.write(f"{ni} {nj} 1\n")

        # PLOT3D ASCII tipicamente escreve todos X, depois todos Y, depois todos Z
        fmt = f"{{:.{ascii_precision}e}}"
        def dump(arr):
            # escreve 5 valores por linha para legibilidade
            for i in range(0, arr.size, 5):
                chunk = arr[i:i+5]
                f.write(" ".join(fmt.format(v) for v in chunk) + "\n")

        dump(Xf)
        dump(Yf)
        dump(Zf)

    return out_path


if __name__ == "__main__":
    # Exemplo rápido (plano de -30..30 em X, 0..30 em Y, z=0, malha 61x31)
    p = create_p3d_half_plane_ysymmetry(-2, 30, 0, 30, 0.0, 61, 31, "ground_plane_example.p3d")
    print("Gerado:", p.resolve())
