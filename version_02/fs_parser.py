"""
fs_parser.py — Parser robusto do relatório "Aerodynamic Loads" (TXT) do FlightStream.

Recursos:
- Remove caracteres nulos (\x00) e normaliza linhas.
- Extrai cabeçalho "chave: valor" (Angle of attack, Freestream velocity, etc.).
- Lê a tabela por superfície aceitando tanto CSV quanto colunas com espaços.
  Estratégia: pega os ÚLTIMOS 9 números da linha; o prefixo é o nome da superfície.
- Gera dois CSVs:
  (1) por_superficie.csv — cada superfície com coeficientes
  (2) resumo_por_caso.csv — metadados + totais:
      - reported_*  : se houver linha "Total" no arquivo
      - aircraft_*  : soma excluindo 'Boundary*', 'Ground*' e 'Total'
- Imprime no console resumo “apenas aeronave”.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import re
import csv

_NUM_COLS = ['Cx','Cy','Cz','CL','CDi','CDo','CMx','CMy','CMz']

@dataclass
class FsCaseMeta:
    arquivo: str
    alpha_deg: Optional[float] = None
    beta_deg: Optional[float] = None
    vel_ms: Optional[float] = None
    reynolds: Optional[float] = None
    ref_len_m: Optional[float] = None
    ref_area_m2: Optional[float] = None
    wake_refinement_pct: Optional[float] = None
    iter_solicitadas: Optional[int] = None
    iter_convergidas: Optional[int] = None
    solver_model: Optional[str] = None
    solver_mode: Optional[str] = None
    altura_solo_m: Optional[float] = None

_FLOAT_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?")

def _clean_text(raw: str) -> str:
    raw = raw.replace("\\x00", "").replace("\x00", "")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return raw

def _first_float_in(s: str) -> Optional[float]:
    m = _FLOAT_RE.search(s)
    if m:
        try:
            return float(m.group(0))
        except Exception:
            return None
    return None

def parse_fs_aero_file(path: Path) -> Tuple[FsCaseMeta, Dict[str,str], List[Dict]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = _clean_text(raw)

    # Cabeçalho (linhas "k: v")
    header: Dict[str,str] = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("---"):
            continue
        if ":" in s:
            k, v = s.split(":", 1)
            header[k.strip()] = v.strip()

    # Tabela por superfície
    rows: List[Dict] = []
    # Heurística: linhas que contenham pelo menos 9 floats são candidatas
    for line in raw.splitlines():
        s = line.strip().strip(",")
        if not s or s.lower().startswith(("aerodynamic loads", "force units")):
            continue

        floats = _FLOAT_RE.findall(s)
        if len(floats) < 9:
            continue

        # últimos 9 são as colunas numéricas
        nums = [float(x.replace("D", "E")) for x in floats[-9:]]
        # nome da superfície = texto até o início do primeiro desses 9 números
        tail_first = s.rfind(floats[-9])
        head = s[:tail_first].strip().strip(",")
        # remove separador "Surface" ou cabeçalho
        if head.lower().startswith(("surface", "name")):
            continue
        if not head:
            continue

        row = {"Surface": head}
        row.update({k: v for k, v in zip(_NUM_COLS, nums)})
        rows.append(row)

    # Metadados
    meta = FsCaseMeta(arquivo=str(path))

    def _getf(key: str) -> Optional[float]:
        v = header.get(key)
        if not v:
            return None
        fv = _first_float_in(v)
        return fv

    meta.alpha_deg = _getf("Angle of attack (Deg)")
    meta.beta_deg = _getf("Side-slip angle (Deg)")
    meta.vel_ms = _getf("Freestream velocity (m/s)")
    meta.reynolds = _getf("Reynolds Number")
    meta.ref_len_m = _getf("Reference length (m)")
    meta.ref_area_m2 = _getf("Reference area (m^2)")
    meta.wake_refinement_pct = _getf("Wake refinement size (% average mesh size)")
    it_req = _getf("Requested solver iterations")
    it_cur = _getf("Current solver iteration number")
    meta.iter_solicitadas = int(it_req) if it_req is not None else None
    meta.iter_convergidas = int(it_cur) if it_cur is not None else None
    meta.solver_model = header.get("Solver model")
    meta.solver_mode = header.get("Solver mode")

    # tenta extrair altura 'h' do nome do arquivo (ex.: resultados_h1.00_a0.0_...)
    mname = re.search(r"_h(\d+(?:\.\d+)?)", Path(path).name, flags=re.I)
    if mname:
        try:
            meta.altura_solo_m = float(mname.group(1))
        except Exception:
            pass

    return meta, header, rows

def compute_aircraft_only(rows: List[Dict]) -> Dict[str, float]:
    fil = [
        r for r in rows
        if not r["Surface"].lower().startswith(("boundary", "ground", "total"))
    ]
    tot = {k: 0.0 for k in _NUM_COLS}
    for r in fil:
        for k in _NUM_COLS:
            tot[k] += float(r.get(k, 0.0))
    return tot

def to_csv_por_superficie(rows: List[Dict], meta: FsCaseMeta, out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = ['arquivo','alpha_deg','beta_deg','vel_ms','altura_solo_m','Surface'] + _NUM_COLS
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            rec = {
                'arquivo': meta.arquivo,
                'alpha_deg': meta.alpha_deg,
                'beta_deg': meta.beta_deg,
                'vel_ms': meta.vel_ms,
                'altura_solo_m': meta.altura_solo_m,
                **r
            }
            w.writerow(rec)

def to_csv_resumo(meta: FsCaseMeta, header: Dict[str,str], rows: List[Dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    total_reportado = next((r for r in rows if r['Surface'].lower().startswith('total')), None)
    reported = {k: total_reportado.get(k) for k in _NUM_COLS} if total_reportado else {}

    aircraft = compute_aircraft_only(rows)

    cols = [
        'arquivo','alpha_deg','beta_deg','vel_ms','altura_solo_m',
        'ref_len_m','ref_area_m2','reynolds','wake_refinement_pct',
        'iter_solicitadas','iter_convergidas','solver_model','solver_mode'
    ] + [f"reported_{k}" for k in _NUM_COLS] + [f"aircraft_{k}" for k in _NUM_COLS]

    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        row = {
            'arquivo': meta.arquivo,
            'alpha_deg': meta.alpha_deg,
            'beta_deg': meta.beta_deg,
            'vel_ms': meta.vel_ms,
            'altura_solo_m': meta.altura_solo_m,
            'ref_len_m': meta.ref_len_m,
            'ref_area_m2': meta.ref_area_m2,
            'reynolds': meta.reynolds,
            'wake_refinement_pct': meta.wake_refinement_pct,
            'iter_solicitadas': meta.iter_solicitadas,
            'iter_convergidas': meta.iter_convergidas,
            'solver_model': meta.solver_model,
            'solver_mode': meta.solver_mode,
        }
        for k in _NUM_COLS:
            row[f"reported_{k}"] = reported.get(k)
        for k in _NUM_COLS:
            row[f"aircraft_{k}"] = aircraft.get(k)
        w.writerow(row)

def parse_and_export(in_txt: Path, out_dir: Path) -> None:
    meta, header, rows = parse_fs_aero_file(in_txt)
    if not rows:
        raise ValueError(f"Nenhuma linha de superfície válida encontrada em: {in_txt}")

    to_csv_por_superficie(rows, meta, out_dir / 'por_superficie.csv')
    to_csv_resumo(meta, header, rows, out_dir / 'resumo_por_caso.csv')

    # Resumo amigável
    def fmt(x: float) -> str:
        return f"{x: .5f}"
    print("\n=== RESUMO (apenas aeronave) ===")
    aircraft = compute_aircraft_only(rows)
    for k in _NUM_COLS:
        print(f"{k:>4s}: {fmt(aircraft[k])}")

    print("\n=== SUPERFÍCIES ===")
    header_cols = ['Surface'] + _NUM_COLS
    print(" | ".join([f"{c:>12s}" for c in header_cols]))
    for r in rows:
        vals = [r['Surface']] + [fmt(r[k]) for k in _NUM_COLS]
        print(" | ".join([f"{v:>12s}" for v in vals]))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Arquivo TXT 'Aerodynamic Loads' do FlightStream")
    ap.add_argument("-o","--out", type=Path, default=Path("analise_saida"), help="Pasta de saída para CSVs")
    args = ap.parse_args()
    parse_and_export(args.input, args.out)
