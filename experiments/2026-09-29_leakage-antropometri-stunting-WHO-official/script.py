"""
Eksperimen: Evaluasi dampak data leakage indikator antropometri terhadap overestimasi
kinerja ML dalam prediksi stunting (SKI 2023, balita 0-59 bulan).

Skenario fitur:
  B   : determinan hulu saja (sosial-ekonomi, maternal, perinatal, pemberian makan,
        WASH, perumahan, akses layanan) -- metodologi benar
  A1  : B + berat badan saat ini (proxy/indirect leakage)
  A2  : B + seluruh antropometri saat ini (BB, TB/PB, LILA, lingkar perut) -- meniru literatur
  L0  : hanya TB/PB + umur + jenis kelamin (komponen rumus HAZ) -- batas atas leakage murni
Model: Logistic Regression, Random Forest, Histogram Gradient Boosting (setara XGBoost;
xgboost tidak tersedia di lingkungan eksekusi).

Jalankan:  python script.py --data <xlsx|pkl> [--lenanthro lenanthro.txt]
"""
import argparse, json, os, sys, time, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, "/mnt/skills/plugins/experiment-report-kit/scripts")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (roc_auc_score, average_precision_score, accuracy_score, f1_score,
                             precision_score, recall_score, balanced_accuracy_score,
                             matthews_corrcoef, brier_score_loss, confusion_matrix, roc_curve)
from sklearn.inspection import permutation_importance
from who_haz import compute_haz

HERE = os.path.dirname(os.path.abspath(__file__))
RES, FIG = os.path.join(HERE, "results"), os.path.join(HERE, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)
SEED = 42

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="SKI_2023_Balita_0-59_Bulan_asli_labels.xlsx")
ap.add_argument("--lenanthro", default="lenanthro.txt")
ap.add_argument("--n_boot", type=int, default=1000)
args = ap.parse_args()
t0 = time.time()
log = lambda *a: print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

# ------------------------------------------------------------------ 1. Load
df = pd.read_pickle(args.data) if args.data.endswith(".pkl") else pd.read_excel(args.data)
n_raw = len(df)
log("rows", n_raw, "cols", df.shape[1])

# ------------------------------------------------------------------ 2. Target (HAZ < -2)
def parse_date(x):
    s = str(int(x)).zfill(8)
    return pd.Timestamp(year=int(s[4:]), month=int(s[2:4]), day=int(s[:2]))
birth = df["6. Tanggal Lahir"].map(lambda x: parse_date(x) if pd.notna(x) else pd.NaT)
visit = df["2. Tanggal Pengumpulan data: (tgl-bln)"].map(lambda x: parse_date(x) if pd.notna(x) else pd.NaT)
age_days = (visit - birth).dt.days.astype(float)
sex = np.where(df["4. Jenis Kelamin"].eq("Laki-laki"), "M", "F")
pos = np.where(df["J02.c.KHUSUS UNTUK BALITA, (Posisi pengukuran TB/PB)"].eq("Telentang"), "recumbent", "standing")
height = df["J02.b.Tinggi/Panjang Badan (cm)"].astype(float)
haz, ref_mode = compute_haz(height, age_days, sex, pos, args.lenanthro)
df["age_days"], df["HAZ"] = age_days, haz
log("reference:", ref_mode)

flow = {"raw": n_raw}
m = df["age_days"].between(0, 1856); flow["valid_age_0_59m"] = int(m.sum())
m &= height.notna() & df["J02.c.KHUSUS UNTUK BALITA, (Posisi pengukuran TB/PB)"].notna(); flow["height_available"] = int(m.sum())
m &= df["HAZ"].between(-6, 6); flow["plausible_HAZ_abs_le_6"] = int(m.sum())
df = df[m].reset_index(drop=True)
y = (df["HAZ"] < -2).astype(int).values
w = df["Penimbang Populasi Individu"].values
flow["stunted_n"] = int(y.sum()); flow["prevalence_unweighted"] = float(y.mean())
flow["prevalence_weighted"] = float(np.average(y, weights=w)); flow["reference"] = ref_mode
log("flow", flow)

# ------------------------------------------------------------------ 3. Feature sets
col = df.columns
def pick(prefixes): return [c for c in col if any(c.startswith(p) for p in prefixes)]
SENTINEL = {"I04.Usia kehamilan saat [NAMA] dilahirkan": [88],
            "I05.a.\tBerapa berat badan [NAMA] saat dilahirkan": [8888],
            "I07.Berapa panjang badan [NAMA] saat dilahirkan": [88, 88.8, 888],
            "H01.Berapa umur [NAMA] ketika pertama kali hamil?": [88, 98, 99]}
for c, vals in SENTINEL.items():
    df.loc[df[c].isin(vals), c] = np.nan
df.loc[df["I05.a.\tBerapa berat badan [NAMA] saat dilahirkan"] > 6000, "I05.a.\tBerapa berat badan [NAMA] saat dilahirkan"] = np.nan
df.loc[~df["I07.Berapa panjang badan [NAMA] saat dilahirkan"].between(30, 65), "I07.Berapa panjang badan [NAMA] saat dilahirkan"] = np.nan
df["age_months"] = df["age_days"] / 30.4375

DET = (["1.Provinsi", "5. Klasifikasi Desa/Kelurahan", "4. Jenis Kelamin", "age_months",
        "8. Pendidikan tertinggi", "9. Status Pekerjaan", "11. Kepemilikan Jaminan Kesehatan",
        "3. Hubungan dengan KRT"]
       + pick(["A12.", "A22.", "B01.", "B07.a", "B16.", "G01", "G03.a", "G07.", "G11.", "G21.", "G32.",
               "H01.", "H09.", "H29.", "H32.", "I01.", "I04.", "I05.a", "I07.", "I09.", "I12", "I15",
               "I16.", "I37.", "I50", "150.", "J01.b"])
       + [c for c in col[128:166]])
DET = list(dict.fromkeys(DET))
ANTHRO = {"weight": "J01.c.Berat Badan (kg)", "height": "J02.b.Tinggi/Panjang Badan (cm)",
          "muac": "J07.b.Lingkar Lengan Atas (cm)", "waist": "J03.b.Lingkar Perut (Cm)"}
EXCLUDED = {
    "identifiers/design": ["ID ART", "ID RT", "ID Ibu", "ID Anak Terakhir", "Penimbang Populasi Individu",
                           "Penimbang Populasi RT", "Primary Sampling Unit", "STRATA", "1. No Urut ART"],
    "target-definition components (used only in L0/A2)": ["J02.b.Tinggi/Panjang Badan (cm)", "6. Tanggal Lahir",
                           "2. Tanggal Pengumpulan data: (tgl-bln)", "7. Umur Bulan", "7. Umur hari", "Kode umur"],
    "measurement-process artefacts": ["J02.c.KHUSUS UNTUK BALITA, (Posisi pengukuran TB/PB)", "J03.a.Apakah [NAMA] diukur Lingkar Perut?",
                           "J07.a.Apakah [NAMA] diukur Lingkar Lengan Atas (LILA)?"],
    "outcome-derived (hidden leakage: PMT given because of undernutrition)": [c for c in col if c.startswith("I49")],
    "stunting-knowledge items possibly affected by child's status": [c for c in col if c.startswith("G03.") and not c.startswith("G03.a")],
    "high missingness (>95%) / free text": [c for c in col if c.startswith(("G14", "G18", "B07.b", "B18", "B24", "G47", "G03.c.Sebutkan"))]
                           + ["I10.Salin dari catatan/dokumen lingkar kepala [NAMA]", "2. Kabupaten/Kota"],
}
SETS = {
    "B (determinants only)": DET,
    "A1 (B + weight)": DET + [ANTHRO["weight"]],
    "A2 (B + all anthropometry)": DET + list(ANTHRO.values()),
    "L0 (height + age + sex)": [ANTHRO["height"], "age_months", "4. Jenis Kelamin"],
}
feat_doc = pd.DataFrame([(k, len(v)) for k, v in SETS.items()], columns=["feature_set", "n_raw_features"])
feat_doc.to_csv(os.path.join(RES, "feature_sets.csv"), index=False)
pd.DataFrame([(g, c) for g, cs in EXCLUDED.items() for c in cs], columns=["exclusion_reason", "variable"]
             ).to_csv(os.path.join(RES, "excluded_variables.csv"), index=False)
pd.DataFrame({"variable": DET}).to_csv(os.path.join(RES, "determinant_features_B.csv"), index=False)

# ------------------------------------------------------------------ 4. Split (household-grouped, stratified)
groups = df["ID RT"].values
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
folds = list(sgkf.split(df, y, groups))
tr, te = folds[0]
assert len(set(groups[tr]) & set(groups[te])) == 0
flow.update({"train_n": int(len(tr)), "test_n": int(len(te)), "train_prev": float(y[tr].mean()),
             "test_prev": float(y[te].mean()), "households_train": int(len(set(groups[tr]))),
             "households_test": int(len(set(groups[te])))})
json.dump(flow, open(os.path.join(RES, "data_flow.json"), "w"), indent=2)

def make_pre(X, scale):
    num = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    cat = [c for c in X.columns if c not in num]
    nsteps = [("imp", SimpleImputer(strategy="median", add_indicator=True))] + ([("sc", StandardScaler())] if scale else [])
    return ColumnTransformer([
        ("num", Pipeline(nsteps), num),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="constant", fill_value="Missing")),
                          ("oh", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=30, sparse_output=False))]), cat)])

def make_hgb(X):
    num = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    cat = [c for c in X.columns if c not in num]
    pre = ColumnTransformer([
        ("cat", Pipeline([("imp", SimpleImputer(strategy="constant", fill_value="Missing")),
                          ("ord", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                                 encoded_missing_value=-1))]), cat),
        ("num", "passthrough", num)], verbose_feature_names_out=False)
    mask = [True] * len(cat) + [False] * len(num)
    return Pipeline([("pre", pre),
        ("clf", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                               categorical_features=mask, class_weight="balanced",
                                               early_stopping=True, validation_fraction=0.1,
                                               n_iter_no_change=20, random_state=SEED))])

def models(X):
    return {
        "Logistic Regression": Pipeline([("pre", make_pre(X, True)),
            ("clf", LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced", solver="lbfgs"))]),
        "Random Forest": Pipeline([("pre", make_pre(X, False)),
            ("clf", RandomForestClassifier(n_estimators=200, min_samples_leaf=5, max_features="sqrt", max_samples=0.5,
                                           class_weight="balanced_subsample", random_state=SEED, n_jobs=1))]),
        "Gradient Boosting (HGB)": make_hgb(X),
    }

def metrics(yt, p, thr=0.5):
    yp = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(yt, yp).ravel()
    return {"AUC-ROC": roc_auc_score(yt, p), "PR-AUC": average_precision_score(yt, p),
            "Accuracy": accuracy_score(yt, yp), "Balanced accuracy": balanced_accuracy_score(yt, yp),
            "Precision": precision_score(yt, yp, zero_division=0), "Recall": recall_score(yt, yp),
            "Specificity": tn / (tn + fp), "F1": f1_score(yt, yp), "MCC": matthews_corrcoef(yt, yp),
            "Brier": brier_score_loss(yt, p)}

rng = np.random.default_rng(SEED)
boot_idx = [rng.integers(0, len(te), len(te)) for _ in range(args.n_boot)]
def boot_ci(yt, p, fn):
    v = []
    for b in boot_idx:
        if yt[b].min() == yt[b].max(): continue
        v.append(fn(yt[b], p[b]))
    return np.percentile(v, [2.5, 97.5])

# ------------------------------------------------------------------ 5. Train/evaluate
rows, preds, fitted = [], {}, {}
yte = y[te]
# naive baseline
prior = np.full(len(te), y[tr].mean())
bm = metrics(yte, prior); bm.update(scenario="Baseline", model="Majority/prior", n_features=0)
rows.append(bm)
for sname, feats in SETS.items():
    X = df[feats]
    for mname, pipe in models(X).items():
        ts = time.time()
        pipe.fit(X.iloc[tr], y[tr])
        p = pipe.predict_proba(X.iloc[te])[:, 1]
        r = metrics(yte, p)
        lo, hi = boot_ci(yte, p, roc_auc_score)
        r.update(scenario=sname, model=mname, n_features=len(feats), AUC_CI_low=lo, AUC_CI_high=hi,
                 fit_seconds=round(time.time() - ts, 1))
        rows.append(r); preds[(sname, mname)] = p; fitted[(sname, mname)] = pipe
        log(f"{sname:28s} {mname:24s} AUC={r['AUC-ROC']:.4f} [{lo:.4f},{hi:.4f}] Acc={r['Accuracy']:.4f} F1={r['F1']:.4f}")
met = pd.DataFrame(rows)
cols = ["scenario", "model", "n_features", "AUC-ROC", "AUC_CI_low", "AUC_CI_high", "PR-AUC", "Accuracy",
        "Balanced accuracy", "Precision", "Recall", "Specificity", "F1", "MCC", "Brier", "fit_seconds"]
met = met[cols]; met.to_csv(os.path.join(RES, "metrics.csv"), index=False, float_format="%.4f")

# paired bootstrap: AUC(A2) - AUC(B), AUC(A1) - AUC(B) per model
diff_rows = []
for mname in ["Logistic Regression", "Random Forest", "Gradient Boosting (HGB)"]:
    pb = preds[("B (determinants only)", mname)]
    for sa in ["A1 (B + weight)", "A2 (B + all anthropometry)", "L0 (height + age + sex)"]:
        pa = preds[(sa, mname)]
        d = [roc_auc_score(yte[b], pa[b]) - roc_auc_score(yte[b], pb[b]) for b in boot_idx]
        obs = roc_auc_score(yte, pa) - roc_auc_score(yte, pb)
        diff_rows.append({"model": mname, "comparison": f"{sa} vs B", "delta_AUC": obs,
                          "CI_low": np.percentile(d, 2.5), "CI_high": np.percentile(d, 97.5),
                          "p_boot(delta<=0)": float(np.mean(np.array(d) <= 0)),
                          "relative_inflation_%": 100 * obs / (roc_auc_score(yte, pb) - 0.5)})
pd.DataFrame(diff_rows).to_csv(os.path.join(RES, "auc_difference_bootstrap.csv"), index=False, float_format="%.4f")

# ------------------------------------------------------------------ 6. Grouped 5-fold CV (HGB) for stability
cv_rows = []
for sname, feats in SETS.items():
    X = df[feats]
    for k, (a, b) in enumerate(folds):
        pipe = models(X)["Gradient Boosting (HGB)"]
        pipe.fit(X.iloc[a], y[a]); p = pipe.predict_proba(X.iloc[b])[:, 1]
        cv_rows.append({"scenario": sname, "fold": k + 1, "AUC-ROC": roc_auc_score(y[b], p),
                        "F1": f1_score(y[b], (p >= .5).astype(int)), "Accuracy": accuracy_score(y[b], (p >= .5).astype(int))})
    log("CV done", sname)
cv = pd.DataFrame(cv_rows); cv.to_csv(os.path.join(RES, "cv5_grouped_hgb_folds.csv"), index=False, float_format="%.4f")
cv.groupby("scenario")[["AUC-ROC", "F1", "Accuracy"]].agg(["mean", "std"]).to_csv(os.path.join(RES, "cv5_grouped_hgb_summary.csv"), float_format="%.4f")

# ------------------------------------------------------------------ 7. Permutation importance (HGB; raw variables)
imp_rows = []
for sname in ["A2 (B + all anthropometry)", "B (determinants only)"]:
    pipe = fitted[(sname, "Gradient Boosting (HGB)")]
    Xte = df[SETS[sname]].iloc[te]
    sub = np.random.default_rng(SEED).choice(len(Xte), size=min(8000, len(Xte)), replace=False)
    pi = permutation_importance(pipe, Xte.iloc[sub], yte[sub], scoring="roc_auc", n_repeats=3, random_state=SEED, n_jobs=1)
    for f, mu, sd in zip(Xte.columns, pi.importances_mean, pi.importances_std):
        imp_rows.append({"scenario": sname, "feature": f, "importance_mean_dAUC": mu, "importance_std": sd})
    log("perm importance done", sname)
imp = pd.DataFrame(imp_rows).sort_values(["scenario", "importance_mean_dAUC"], ascending=[True, False])
imp.to_csv(os.path.join(RES, "permutation_importance_hgb.csv"), index=False, float_format="%.5f")

# ------------------------------------------------------------------ 8. Figures
import matplotlib.pyplot as plt
from plot_style import apply_style, COLORBLIND_SAFE_PALETTE as PAL
from comparison_table import build_comparison
apply_style()
SHORT = {"B (determinants only)": "B: determinants", "A1 (B + weight)": "A1: B + weight",
         "A2 (B + all anthropometry)": "A2: B + all anthropometry", "L0 (height + age + sex)": "L0: height + age + sex"}

# Fig: ROC overlay (HGB) per scenario
fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
for ax, mname in zip(axes, ["Logistic Regression", "Random Forest", "Gradient Boosting (HGB)"]):
    for i, s in enumerate(SETS):
        fpr, tpr, _ = roc_curve(yte, preds[(s, mname)])
        ax.plot(fpr, tpr, color=PAL[i], lw=1.8, label=f"{SHORT[s]} (AUC={roc_auc_score(yte, preds[(s, mname)]):.3f})")
    ax.plot([0, 1], [0, 1], ls="--", c="grey", lw=1)
    ax.set_title(mname); ax.set_xlabel("False positive rate")
    ax.legend(fontsize=7, loc="lower right")
axes[0].set_ylabel("True positive rate")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "main_result_roc.png"), dpi=300); plt.close(fig)

# Fig: comparison bar (HGB, key metrics)
comp = {}
for s in SETS:
    r = met[(met.scenario == s) & (met.model == "Gradient Boosting (HGB)")].iloc[0]
    comp[SHORT[s]] = {"AUC-ROC": r["AUC-ROC"], "Accuracy": r["Accuracy"], "Recall": r["Recall"],
                      "Precision": r["Precision"], "F1": r["F1"]}
b = met[met.scenario == "Baseline"].iloc[0]
comp["Baseline (prior)"] = {"AUC-ROC": b["AUC-ROC"], "Accuracy": b["Accuracy"], "Recall": b["Recall"],
                            "Precision": b["Precision"], "F1": b["F1"]}
build_comparison(comp, os.path.join(RES, "comparison.csv"), os.path.join(FIG, "comparison.png"),
                 title="Leaky vs leakage-free feature sets (Gradient Boosting, household-grouped test set)", value_label="Score")

# Fig: AUC by model x scenario with CI
fig, ax = plt.subplots(figsize=(8, 4.2))
ms = ["Logistic Regression", "Random Forest", "Gradient Boosting (HGB)"]
for i, s in enumerate(SETS):
    sub = met[met.scenario == s].set_index("model").loc[ms]
    x = np.arange(len(ms)) + (i - 1.5) * 0.2
    ax.bar(x, sub["AUC-ROC"], 0.2, color=PAL[i], label=SHORT[s],
           yerr=[sub["AUC-ROC"] - sub["AUC_CI_low"], sub["AUC_CI_high"] - sub["AUC-ROC"]], capsize=2)
ax.axhline(0.5, ls="--", c="grey", lw=1); ax.set_ylim(0.45, 1.02)
ax.set_xticks(range(len(ms))); ax.set_xticklabels(ms); ax.set_ylabel("AUC-ROC (95% bootstrap CI)")
ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1)); fig.tight_layout()
fig.savefig(os.path.join(FIG, "auc_by_model_scenario.png"), dpi=300); plt.close(fig)

# Fig: permutation importance top 12
LABEL = {v: k for k, v in ANTHRO.items()}
def short(f):
    if f in LABEL: return {"weight": "Current weight", "height": "Current height/length", "muac": "MUAC", "waist": "Waist circumference"}[LABEL[f]]
    return {"age_months": "Child age (months)"}.get(f, f.replace("\t", " ")[:48])
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, s, c in zip(axes, ["A2 (B + all anthropometry)", "B (determinants only)"], [PAL[1], PAL[2]]):
    t = imp[imp.scenario == s].head(12)[::-1]
    ax.barh([short(f) for f in t.feature], t.importance_mean_dAUC, xerr=t.importance_std, color=c)
    ax.set_title(SHORT[s]); ax.set_xlabel("Permutation importance (drop in AUC)")
    ax.tick_params(axis="y", labelsize=7)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "permutation_importance.png"), dpi=300); plt.close(fig)

# Fig: HAZ distribution
fig, ax = plt.subplots(figsize=(6.5, 3.8))
ax.hist(df["HAZ"], bins=120, color=PAL[0]); ax.axvline(-2, c=PAL[1], ls="--", label="HAZ = -2 (stunting cut-off)")
ax.set_xlabel("Height-for-age z-score"); ax.set_ylabel("Children"); ax.legend(); fig.tight_layout()
fig.savefig(os.path.join(FIG, "haz_distribution.png"), dpi=300); plt.close(fig)

# Fig: height vs age coloured by label (why leakage works)
fig, ax = plt.subplots(figsize=(6.5, 4.2))
s = np.random.default_rng(SEED).choice(len(df), 6000, replace=False)
ax.scatter(df["age_months"].iloc[s], df[ANTHRO["height"]].iloc[s], c=np.where(y[s] == 1, PAL[1], PAL[0]), s=3, alpha=.5)
ax.set_xlabel("Age (months)"); ax.set_ylabel("Height/length (cm)")
ax.scatter([], [], c=PAL[1], label="Stunted"); ax.scatter([], [], c=PAL[0], label="Not stunted"); ax.legend(markerscale=3)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "height_age_separability.png"), dpi=300); plt.close(fig)

json.dump({"experiment_name": "leakage-antropometri-stunting", "random_seed": SEED, "reference": ref_mode,
           "split": "StratifiedGroupKFold(5, groups=household ID RT), fold 1 = test",
           "n_boot": args.n_boot, "threshold": 0.5,
           "models": {"LR": "C=1, balanced", "RF": "200 trees, min_leaf=5, sqrt, max_samples=0.5, balanced_subsample",
                      "HGB": "native categorical, max_iter=300, lr=0.08, leaves=31, balanced, early stopping(20)"}},
          open(os.path.join(HERE, "config.json"), "w"), indent=2)
log("DONE")
