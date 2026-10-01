# Rencana Eksperimen: Evaluasi Dampak Kebocoran Data (Data Leakage) pada Prediksi Stunting

## 1. Persiapan Data (Data Preparation)
- **Sumber Data:** Dataset Survei Kesehatan Indonesia (SKI) 2023.
- **Pembersihan Data (Data Cleaning):** Menangani *missing values* (imputasi atau penghapusan), mendeteksi *outliers*, dan memastikan konsistensi tipe data.
- **Encoding:** Melakukan *categorical encoding* pada variabel-variabel nominal/ordinal (misal: tingkat pendidikan ibu, jenis sanitasi, ketersediaan air bersih, dll).

## 2. Penentuan Variabel Target (Target Definition)
- **Target (Y):** Status Stunting balita (Biner: 1 = Stunting, 0 = Tidak Stunting).
- *Catatan:* Label ini biasanya diturunkan dari Z-score Tinggi Badan menurut Umur (TB/U) atau HAZ (Height-for-Age Z-score) < -2 SD.

## 3. Pembagian Skenario Fitur (Feature Engineering & Splitting)
Eksperimen akan dibagi secara ketat menjadi dua skenario utama berdasarkan pemilihan fitur (X):
- **Skenario A (Model dengan Data Leakage - Meniru Literatur Terdahulu):**
  - **Fitur (X_A):** Memasukkan indikator antropometri balita (seperti Tinggi Badan, Panjang Badan, atau Berat Badan) yang secara matematis berhubungan langsung dengan perhitungan Z-score.
  - Fitur lain (determinan sosial/lingkungan) tetap dimasukkan.
- **Skenario B (Model Tanpa Data Leakage - Metodologi Benar):**
  - **Fitur (X_B):** **MENGHAPUS SECARA TOTAL** semua indikator antropometri balita.
  - Hanya menggunakan variabel determinan "hulu" sejati (misal: Tingkat pendidikan ibu/ayah, riwayat ANC, IMT Ibu, sanitasi lingkungan, akses air minum, riwayat penyakit infeksi balita, pemberian ASI/MPASI).

## 4. Pembagian Data (Data Splitting)
- Membagi dataset menjadi *Training Set* (misal 70% atau 80%) dan *Testing Set* (misal 30% atau 20%).
- Sangat disarankan menggunakan teknik *Stratified Sampling* untuk memastikan proporsi kelas balita stunting seimbang antara data latih dan uji (mengingat kasus stunting biasanya bersifat *imbalanced*).

## 5. Pelatihan Model (Model Training)
- Memilih beberapa algoritma Machine Learning standar yang sering dipakai pada literatur terdahulu (misal: Logistic Regression, Random Forest, dan XGBoost).
- **Pelatihan A:** Melatih algoritma-algoritma tersebut menggunakan dataset **X_A** (Skenario Cacat).
- **Pelatihan B:** Melatih algoritma-algoritma tersebut menggunakan dataset **X_B** (Skenario Ideal/Benar).

## 6. Evaluasi dan Perbandingan (Evaluation & Comparison)
- Menguji kedua model menggunakan *Testing Set* yang belum pernah dilihat oleh model.
- **Metrik Evaluasi:** Akurasi, Precision, Recall/Sensitivity, F1-Score, dan AUC-ROC.
- **Analisis Feature Importance:** Mengekstraksi *feature importance* (misal dari Random Forest/XGBoost) untuk melihat fitur mana yang paling mendominasi pengambilan keputusan pada Model A versus Model B.

## 7. Interpretasi dan Kesimpulan (Interpretation)
- **Hipotesis/Ekspektasi Output:** Model A akan menunjukkan akurasi yang tidak realistis (misal >95%) dengan fitur tinggi/berat badan memonopoli *feature importance*. Model B akan menunjukkan performa prediktif *baseline* yang sebenarnya (mungkin akurasi/AUC lebih rendah, misalnya 70-80%), namun secara metodologi valid.
- **Sintesis:** Membuktikan dengan angka eksperimen bahwa klaim akurasi fantastis pada literatur terdahulu adalah *ilusi* yang disebabkan oleh kesalahan metodologi (*data leakage*), serta menawarkan Model B sebagai acuan realistis untuk penelitian selanjutnya.

---

## Flowchart Metodologi Penelitian

```mermaid
flowchart TD
    A[Mulai Penelitian] --> B[Pengumpulan Dataset SKI 2023]
    B --> C[Pra-pemrosesan Data \n - Data Cleaning \n - Encoding & Transformasi]
    C --> D[Penentuan Variabel Target \n Y = Status Stunting]
    
    D --> E{Pemisahan Skenario Fitur Eksperimen}
    
    %% Skenario A
    E -->|Skenario A \n (Terdapat Data Leakage)| FA[Ekstraksi Fitur X_A: \n Masukkan Antropometri \n Tinggi & Berat Badan]
    FA --> GA[Data Splitting \n Training & Testing]
    GA --> HA[Pelatihan Model ML \n Model Terdahulu]
    HA --> IA[Evaluasi Model A \n Akurasi, AUC, F1-Score, dll]
    
    %% Skenario B
    E -->|Skenario B \n (Bebas Data Leakage)| FB[Ekstraksi Fitur X_B: \n Hapus Total Antropometri, \n Hanya Pakai Faktor Determinan]
    FB --> GB[Data Splitting \n Training & Testing]
    GB --> HB[Pelatihan Model ML \n Model Ideal]
    HB --> IB[Evaluasi Model B \n Akurasi, AUC, F1-Score, dll]
    
    %% Komparasi
    IA --> J[Analisis Komparatif & \n Ekstraksi Feature Importance]
    IB --> J
    
    J --> K[Interpretasi: \n Bukti Overestimasi Performa ML di Literatur Terdahulu]
    K --> L[Selesai]
    
    %% Styling
    classDef red fill:#ffe6e6,stroke:#ff6666,stroke-width:2px,color:#000;
    classDef green fill:#e6ffe6,stroke:#66cc66,stroke-width:2px,color:#000;
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px,color:#000;
    
    class FA,HA,IA red;
    class FB,HB,IB green;
```
