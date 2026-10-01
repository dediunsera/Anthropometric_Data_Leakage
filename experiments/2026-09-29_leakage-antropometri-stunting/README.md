# Eksperimen: Data leakage antropometri pada prediksi stunting (SKI 2023)

> **DIGANTIKAN** oleh folder `2026-09-29_leakage-antropometri-stunting-WHO-official` (rujukan WHO resmi). Hasil di sini provisional.


- Tanggal: 2026-09-29
- RQ: Seberapa besar kinerja ML prediksi stunting melonjak ketika indikator antropometri saat ini (yang membentuk label HAZ) dimasukkan sebagai prediktor, dibanding model yang hanya memakai determinan hulu?
- Data: SKI 2023 balita 0-59 bulan ASLI (86.364 baris; 84.202 dianalisis; 19.283 stunting).
- **PERHATIAN (provisional):** HAZ dihitung dengan rujukan WHO-aproksimasi (median & -2SD WHO diinterpolasi) karena `lenanthro.txt` tidak tersedia di sesi. Prevalensi tertimbang 21,37% (resmi SKI 2023: 21,5%). Taruh `lenanthro.txt` di folder ini lalu jalankan ulang sebelum submit.

## Metode
Empat set fitur: B (119 determinan), A1 (B + berat badan), A2 (B + BB, TB/PB, LILA, lingkar perut), L0 (TB/PB + umur + jenis kelamin). Tiga model: Regresi Logistik, Random Forest, Gradient Boosting (HistGradientBoosting; pengganti XGBoost). Split 80/20 stratified-grouped per rumah tangga; preprocessing di dalam pipeline. Evaluasi: AUC + bootstrap CI (1000), ΔAUC berpasangan, CV 5-fold grouped (HGB), permutation importance.

## Hasil utama (test set, 16.842 balita dari 15.075 rumah tangga)
| Skenario | LR AUC | RF AUC | HGB AUC | HGB Akurasi |
|---|---|---|---|---|
| Baseline mayoritas | 0,500 | – | – | 0,771 |
| B (determinan) | 0,661 | 0,662 | 0,676 | 0,633 |
| A1 (+ berat badan) | 0,799 | 0,759 | 0,822 | 0,767 |
| A2 (+ semua antropometri) | 0,950 | 0,858 | 0,999 | 0,979 |
| L0 (TB + umur + JK) | 0,908 | 0,999 | 0,999 | 0,979 |

ΔAUC HGB A2 − B = 0,322 (95% CI 0,312–0,332). CV 5-fold grouped HGB: B 0,675 ± 0,002; A2 0,998 ± 0,000.

## Interpretasi
Hanya dengan tinggi badan, umur, dan jenis kelamin, model sudah "memprediksi" stunting dengan AUC 0,999 — karena ketiganya adalah rumus label itu sendiri, bukan faktor risiko. Menambahkan antropometri ke determinan menaikkan AUC dari 0,68 menjadi 0,999, dan permutation importance menunjukkan tinggi badan dan umur menguasai hampir seluruh keputusan model. Kinerja realistis model berbasis determinan hulu ada di kisaran AUC 0,66–0,68; akurasi pun menyesatkan karena model mayoritas saja sudah 77% akurat. Angka "95%+" di literatur adalah artefak target leakage, bukan kemampuan prediktif.

## Cara reproduce
```
python script.py --data SKI_2023_Balita_0-59_Bulan_asli_labels.xlsx --lenanthro lenanthro.txt
python make_manuscript_figures.py
```
