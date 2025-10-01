
"""
fs_parser.py — Parser robusto para arquivos "Aerodynamic Loads" do Altair FlightStream
- Limpa caracteres nulos (\x00) e sinais estranhos
- Lê cabeçalho e tabela de superfícies
- Calcula totais:
    (a) "reportado" (linha Total do arquivo)
    (b) "apenas_aeronave" (exclui superfícies que começam com 'Boundary'/'Ground')
- Exporta CSVs "por_superficie" e "resumo_por_caso"
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import csv
from typing import Dict, List, Tuple, Optional


@dataclass
class FsCaseMeta:
    """Metadados úteis do caso (extraídos do header e/ou nome do arquivo)."""
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
    altura_solo_m: Optional[float] = None  # heurística via nome do arquivo, se aplicável


_NUM_COLS = ['Cx','Cy','Cz','CL','CDi','CDo','CMx','CMy','CMz']


def _clean_text(raw: str) -> str:
    # Remove NULs e normaliza separadores
    raw = raw.replace('\\x00', '').replace('\x00', '')
    return raw


def _try_float(x: str) -> Optional[float]:
    try:
        return float(x.strip().replace('+',''))
    except Exception:
        return None


def parse_fs_aero_file(path: Path) -> Tuple[FsCaseMeta, Dict, List[Dict]]:
    """Retorna (meta, header_dict, rows_por_superficie)."""
    raw = path.read_text(encoding='utf-8', errors='replace')
    raw = _clean_text(raw)

    # HEADER: linhas "Chave: valor"
    header: Dict[str, str] = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith('----'):
            continue
        if s.startswith('Aerodynamic Loads'):
            continue
        if ':' in s:
            k, v = s.split(':', 1)
            header[k.strip()] = v.strip()

    # TABELA
    m = re.search(r"Surface,\\s*Cx.*?-+\\s*(.*?)\\s*-{5,}\\s*Force Units", raw, flags=re.S)
    rows: List[Dict] = []
    if m:
        body = m.group(1)
        for line in body.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 10:
                # Formatação inesperada — tenta separar pelo primeiro token (nome) + números
                # Ex.: "Wing, +0.01, ..." é o caso mais comum. Se quebrar, pula.
                continue
            nome = parts[0]
            nums = [_try_float(p) for p in parts[1:]]
            if any(v is None for v in nums):
                # linha problemática; ignora
                continue
            row = {'Surface': nome}
            row.update({k: v for k, v in zip(_NUM_COLS, nums)})
            rows.append(row)

    # META
    meta = FsCaseMeta(arquivo=str(path))
    def _getf(key: str) -> Optional[float]:
        v = header.get(key)
        if v is None:
            return None
        # pega o primeiro "token" numérico da direita
        m2 = re.search(r"([-+]?\\d+(?:\\.\\d+)?(?:E[-+]?\\d+)?)", v, flags=re.I)
        return float(m2.group(1)) if m2 else None

    meta.alpha_deg = _getf('Angle of attack (Deg)')
    meta.beta_deg = _getf('Side-slip angle (Deg)')
    meta.vel_ms = _getf('Freestream velocity (m/s)')
    meta.reynolds = _getf('Reynolds Number')
    meta.ref_len_m = _getf('Reference length (m)')
    meta.ref_area_m2 = _getf('Reference area (m^2)')
    meta.wake_refinement_pct = _getf('Wake refinement size (% average mesh size)')
    meta.iter_solicitadas = int(_getf('Requested solver iterations') or 0)
    meta.iter_convergidas = int(_getf('Current solver iteration number') or 0)
    meta.solver_model = header.get('Solver model')
    meta.solver_mode = header.get('Solver mode')

    # tenta "altura" via nome (ex.: resultados_h1.0_s30.txt -> h=1.0)
    mname = re.search(r"_h([0-9]+(?:\\.[0-9]+)?)", path.name, flags=re.I)
    if mname:
        try:
            meta.altura_solo_m = float(mname.group(1))
        except Exception:
            pass

    return meta, header, rows


def compute_totals(rows: List[Dict]) -> Dict[str, float]:
    """Soma geral (inclui tudo, inclusive Boundary e Total se estiver na lista)."""
    tot = {k: 0.0 for k in _NUM_COLS}
    for r in rows:
        for k in _NUM_COLS:
            tot[k] += r.get(k, 0.0)
    return tot


def compute_aircraft_only(rows: List[Dict]) -> Dict[str, float]:
    """Soma excluindo superfícies do tipo 'Boundary*' e a linha 'Total' por segurança."""
    fil = [
        r for r in rows
        if not r['Surface'].lower().startswith(('boundary', 'ground', 'total'))
    ]
    tot = {k: 0.0 for k in _NUM_COLS}
    for r in fil:
        for k in _NUM_COLS:
            tot[k] += r.get(k, 0.0)
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


def to_csv_resumo(meta: FsCaseMeta, header: Dict, rows: List[Dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    # "Total" do arquivo (se existir)
    total_reportado = next((r for r in rows if r['Surface'].lower().startswith('total')), None)
    total_reportado_vals = {k: total_reportado[k] for k in _NUM_COLS} if total_reportado else {}

    aircraft_only = compute_aircraft_only(rows)

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
        # reported
        for k in _NUM_COLS:
            row[f"reported_{k}"] = total_reportado_vals.get(k)
        # aircraft-only
        for k in _NUM_COLS:
            row[f"aircraft_{k}"] = aircraft_only.get(k)
        w.writerow(row)


def parse_and_export(in_txt: Path, out_dir: Path) -> None:
    meta, header, rows = parse_fs_aero_file(in_txt)
    # CSVs
    to_csv_por_superficie(rows, meta, out_dir / 'por_superficie.csv')
    to_csv_resumo(meta, header, rows, out_dir / 'resumo_por_caso.csv')

    # Impressão amigável (sem \x00, colunas alinhadas)
    # Útil para logs
    def fmt(x: float) -> str:
        return f"{x: .5f}"

    print("\n=== RESUMO (apenas aeronave) ===")
    aircraft = compute_aircraft_only(rows)
    for k in _NUM_COLS:
        print(f"{k:>4s}: {fmt(aircraft[k])}")
    print("\n=== SUPERFÍCIES ===")
    header_cols = ['Surface'] + _NUM_COLS
    print(" | ".join([f"{c:>10s}" for c in header_cols]))
    for r in rows:
        vals = [r['Surface']] + [fmt(r[k]) for k in _NUM_COLS]
        print(" | ".join([f"{v:>10s}" for v in vals]))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Arquivo TXT 'Aerodynamic Loads' do FlightStream")
    ap.add_argument("-o","--out", type=Path, default=Path("analise_saida"), help="Pasta de saída para CSVs")
    args = ap.parse_args()
    parse_and_export(args.input, args.out)
