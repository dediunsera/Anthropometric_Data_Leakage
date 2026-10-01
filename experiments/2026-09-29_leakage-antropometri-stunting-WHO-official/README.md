# Eksperimen FINAL: Data leakage antropometri pada prediksi stunting (SKI 2023, rujukan WHO resmi)

- HAZ dihitung dengan metode LMS harian dari tabel WHO resmi `lenanthro.txt` (0–1.826 hari).
- Data: 86.364 baris → 84.205 balita dianalisis; 19.825 stunting (23,5% tidak tertimbang; 22,0% tertimbang).
- Split grouped per rumah tangga: latih 67.364 (60.286 RT), uji 16.841 (15.060 RT).
- Menggantikan hasil provisional di folder `2026-09-29_leakage-antropometri-stunting` (disimpan untuk jejak audit).

## Hasil utama (AUC pada data uji)
| Skenario | LR | RF | HGB | Akurasi HGB |
|---|---|---|---|---|
| Baseline mayoritas | 0,500 | – | – | 0,765 |
| B (determinan) | 0,656 | 0,654 | 0,670 | 0,629 |
| A1 (+ berat badan) | 0,803 | 0,759 | 0,825 | 0,763 |
| A2 (+ semua antropometri) | 0,951 | 0,862 | 0,998 | 0,978 |
| L0 (TB + umur + JK) | 0,910 | 0,999 | 0,999 | 0,978 |

ΔAUC HGB A2 − B = 0,328 (95% CI 0,320–0,337); inflasi di atas peluang 193%. CV 5-fold grouped HGB: B 0,671 ± 0,005; A2 0,998 ± 0,000.
Permutation importance A2: tinggi badan 0,473, umur 0,361, JK 0,016, determinan lain < 0,001.

## Interpretasi
Tinggi badan, umur, dan jenis kelamin saja sudah memberi AUC 0,999 karena ketiganya adalah rumus label. Model determinan-saja memberi baseline realistis AUC 0,65–0,67. Klaim akurasi 95%+ pada literatur yang memakai antropometri adalah artefak target leakage.

## Reproduce
python script.py --data SKI_2023_Balita_0-59_Bulan_asli_labels.xlsx --lenanthro lenanthro.txt
python make_manuscript_figures.py
