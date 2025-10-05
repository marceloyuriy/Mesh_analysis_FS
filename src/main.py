# main.py
from shared import GEOM_DIR  # paths/config
from run_case import run_case


def main():
    p3ds = sorted(GEOM_DIR.glob("*.p3d"))
    if not p3ds:
        print(f"Nenhum .p3d encontrado em {GEOM_DIR}")
        return
    for p3d in p3ds:
        run_case(p3d)


if __name__ == "__main__":
    main()
