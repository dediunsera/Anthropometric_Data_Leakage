"""Figures for the IJECE manuscript (English labels), built only from results/*.csv."""
import sys, os
sys.path.insert(0, "/mnt/skills/plugins/experiment-report-kit/scripts")
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from plot_style import apply_style, COLORBLIND_SAFE_PALETTE as PAL
apply_style()
H = os.path.dirname(os.path.abspath(__file__)); R, F = f"{H}/results", f"{H}/figures"
EN = {"J02.b.Tinggi/Panjang Badan (cm)": "Current height/length", "age_months": "Child age (months)",
      "4. Jenis Kelamin": "Child sex", "I07.Berapa panjang badan [NAMA] saat dilahirkan": "Birth length",
      "1.Provinsi": "Province", "J01.c.Berat Badan (kg)": "Current weight",
      "I05.a.\tBerapa berat badan [NAMA] saat dilahirkan": "Birth weight",
      "1.a.Waktu yang diperlukan dari Rumah ke faskes - Puskesmas": "Travel time to primary care",
      "19.Bagaimana cara utama dalam menangan sampah [RUMAH TANGGA]?": "Household waste handling",
      "11. Kepemilikan Jaminan Kesehatan": "Health insurance type",
      "26.Jenis bahan bangunan utama plafon/langit-langit rumah terluas": "Ceiling material",
      "2.Luas lantai bangunan rumah  (BULATKAN DALAM METER PERSEGI)": "House floor area",
      "H29.Dimana tempat persalinan [NAMA ANAK]?": "Place of delivery",
      "8. Pendidikan tertinggi": "Maternal education",
      "3. Banyaknya anggota rumah tangga yang diwawancarai:": "Household members interviewed",
      "J01.b.KHUSUS BALITA, Kondisi kesehatan saat pengukuran?": "Health status at measurement",
      "I50.g.\tMinuman/cairan lainnya (seperti air gula, kental manis, teh, air tajin, susu kedelai, dll)": "Other liquids (24-h recall)",
      "I50.e.Jika Ya, berapa kali [Nama] minum susu? Jika 7 kali atau lebih, catat ‘7’": "Formula feeds (24-h recall)",
      "1.a.Alat Transportasi yang di gunakan - Puskesmas": "Transport to primary care",
      "I50.b.\tAir putih": "Plain water (24-h recall)",
      "1.Apakah jenis sarana air yang UTAMA digunakan oleh [RUMAH TANGGA] untuk keperluan minum saat ini?": "Main drinking-water source",
      "27.Jenis bahan bangunan utama lantai rumah terluas?": "Floor material",
      "H01.Berapa umur [NAMA] ketika pertama kali hamil?": "Maternal age at first pregnancy",
      "1. Banyaknya anggota rumah tangga:": "Household size"}
imp = pd.read_csv(f"{R}/permutation_importance_hgb.csv")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
for ax, s, c, t in zip(axes, ["A2 (B + all anthropometry)", "B (determinants only)"], [PAL[1], PAL[0]],
                       ["(a) Scenario A2: leaky", "(b) Scenario B: leakage-free"]):
    d = imp[imp.scenario == s].head(10)[::-1]
    ax.barh([EN.get(f, f[:35]) for f in d.feature], d.importance_mean_dAUC, xerr=d.importance_std, color=c)
    ax.set_xlabel("Permutation importance (decrease in AUC)"); ax.set_title(t)
fig.tight_layout(); fig.savefig(f"{F}/fig_permutation_importance_en.png", dpi=300); plt.close(fig)

# Flowchart (Figure 1)
fig, ax = plt.subplots(figsize=(10, 6.2)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
def box(x, y, w, h, t, fc="#f2f2f2", ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=8.5, wrap=True)
def arr(x1, y1, x2, y2): ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", lw=1.2))
box(3, 9.0, 4, 0.7, "SKI 2023 under-five records (n = 86,364)")
box(3, 7.9, 4, 0.75, "Cleaning: age 0-59 mo, valid height, |HAZ| <= 6\n(n = 84,205; stunted = 19,825)")
box(3, 6.8, 4, 0.75, "Target: stunting = HAZ < -2 SD (WHO 2006)\nfrom height, age, sex")
box(3, 5.7, 4, 0.75, "Household-grouped stratified split (80/20)\ntrain n = 67,364 | test n = 16,841")
labels = [("B: 119 upstream\ndeterminants", "#e6f0fa"), ("A1: B + current\nweight", "#fdebd9"),
          ("A2: B + weight, height,\nMUAC, waist", "#fbe0e0"), ("L0: height + age\n+ sex only", "#f3e3ee")]
for i, (t, c) in enumerate(labels):
    box(0.2 + i*2.45, 4.1, 2.2, 0.9, t, fc=c); arr(5, 5.7, 1.3 + i*2.45, 5.0)
box(1.5, 2.6, 7, 0.8, "Train LR, RF, gradient boosting (HGB) in leakage-safe pipelines\n(imputation/encoding fitted on training folds only)")
for i in range(4): arr(1.3 + i*2.45, 4.1, 5, 3.4)
box(1.5, 1.1, 7, 0.9, "Evaluation on unseen households: AUC (bootstrap 95% CI), PR-AUC, accuracy,\nrecall, specificity, F1, MCC, Brier; paired bootstrap dAUC; grouped 5-fold CV;\npermutation importance")
arr(5, 2.6, 5, 2.0)
for y1, y2 in [(9.0, 8.65), (7.9, 7.55), (6.8, 6.45)]: arr(5, y1, 5, y2)
fig.savefig(f"{F}/fig_method_flow.png", dpi=300, bbox_inches="tight"); plt.close(fig)
print("ok")
