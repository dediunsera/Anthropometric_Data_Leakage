"""
Perhitungan Height-for-Age Z-score (HAZ) menurut WHO Child Growth Standards 2006.

DUA MODE:
1. RESMI (dipakai untuk hasil final): bila file WHO `lenanthro.txt` (paket WHO Anthro /
   igrowup; kolom: sex, age[hari], l, m, s, loh) tersedia, HAZ dihitung dengan metode LMS
   harian: z = ((y/M)^L - 1) / (L*S); untuk panjang/tinggi L = 1.
2. PROVISIONAL (dipakai hanya bila file resmi tidak ada): median dan batas -2SD WHO pada
   usia jangkar (0-60 bulan) yang DITRANSKRIPSI DARI TABEL SD WHO, lalu diinterpolasi
   linier per hari. SD = (median - (-2SD))/2. Hasil mode ini WAJIB diverifikasi ulang
   dengan lenanthro.txt sebelum naskah dikirim.

Koreksi posisi ukur (WHO): usia < 731 hari diukur berdiri -> +0.7 cm;
usia >= 731 hari diukur telentang -> -0.7 cm.
"""
import os
import numpy as np
import pandas as pd

# (usia_bulan, median, minus2SD) -- ASUMSI PROVISIONAL, verifikasi dengan lenanthro.txt
_ANCHORS = {
    # Laki-laki: panjang badan (0-24 bln)
    ("M", "L"): [(0, 49.9, 46.1), (3, 61.4, 57.3), (6, 67.6, 63.3), (9, 72.0, 67.5),
                 (12, 75.7, 71.0), (18, 82.3, 76.9), (24, 87.8, 81.7)],
    # Laki-laki: tinggi badan (24-60 bln)
    ("M", "H"): [(24, 87.1, 81.0), (30, 91.9, 85.1), (36, 96.1, 88.7), (42, 99.9, 91.9),
                 (48, 103.3, 94.9), (54, 106.7, 97.8), (60, 110.0, 100.7)],
    # Perempuan: panjang badan
    ("F", "L"): [(0, 49.1, 45.4), (3, 59.8, 55.6), (6, 65.7, 61.2), (9, 70.1, 65.3),
                 (12, 74.0, 68.9), (18, 80.7, 74.9), (24, 86.4, 80.0)],
    # Perempuan: tinggi badan
    ("F", "H"): [(24, 85.7, 79.3), (30, 90.7, 83.6), (36, 95.1, 87.4), (42, 99.0, 90.9),
                 (48, 102.7, 94.1), (54, 106.2, 97.1), (60, 109.4, 99.9)],
}
DAYS_PER_MONTH = 30.4375


def _provisional_ref(sex, age_days):
    mode = "L" if age_days < 731 else "H"
    a = np.array(_ANCHORS[(sex, mode)], dtype=float)
    m = age_days / DAYS_PER_MONTH
    med = np.interp(m, a[:, 0], a[:, 1])
    m2 = np.interp(m, a[:, 0], a[:, 2])
    return med, (med - m2) / 2.0


def load_lenanthro(path):
    t = pd.read_csv(path, sep=r"\s+")
    t.columns = [c.lower() for c in t.columns]
    return {(int(r.sex), int(r.age)): (r.l, r.m, r.s) for r in t.itertuples()}


def compute_haz(height_cm, age_days, sex, position, lenanthro_path=None):
    """sex: 'M'/'F'; position: 'standing'/'recumbent'. Mengembalikan (haz, mode_string)."""
    h = np.asarray(height_cm, dtype=float).copy()
    d = np.asarray(age_days, dtype=float)
    pos = np.asarray(position)
    h = np.where((d < 731) & (pos == "standing"), h + 0.7, h)
    h = np.where((d >= 731) & (pos == "recumbent"), h - 0.7, h)

    z = np.full(len(h), np.nan)
    if lenanthro_path and os.path.exists(lenanthro_path):
        ref = load_lenanthro(lenanthro_path)
        for i, (hi, di, si) in enumerate(zip(h, d, sex)):
            if np.isnan(hi) or np.isnan(di):
                continue
            key = (1 if si == "M" else 2, int(round(di)))
            if key in ref:
                l, m, s = ref[key]
                z[i] = ((hi / m) ** l - 1) / (l * s)
        return z, "WHO-LMS-official(lenanthro.txt)"

    for i, (hi, di, si) in enumerate(zip(h, d, sex)):
        if np.isnan(hi) or np.isnan(di) or di < 0 or di > 1856:
            continue
        med, sd = _provisional_ref(si, di)
        z[i] = (hi - med) / sd
    return z, "WHO-approx-PROVISIONAL(median/-2SD anchors, interpolated)"
