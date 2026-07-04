"""
SevaSetu — data_loader.py
Team AstraSync | GEC Rajkot
Parses REAL Gujarat HMIS Excel file from hmis.mohfw.gov.in
"""

import pandas as pd
import numpy as np
import os

DISTRICT_COLUMNS = {
    "Ahmadabad":9,"Amreli":14,"Anand":19,"Arvalli":24,
    "Banas Kantha":29,"Bharuch":34,"Bhavnagar":39,"Botad":44,
    "Chhotaudepur":49,"Dang":54,"Devbhumi Dwarka":59,"Dohad":64,
    "Gandhinagar":69,"Gir Somnath":74,"Jamnagar":79,"Junagadh":84,
    "Kachchh":89,"Kheda":94,"Mahesana":99,"Mahisagar":104,
    "Morbi":109,"Narmada":114,"Navsari":119,"Panch Mahals":124,
    "Patan":129,"Porbandar":134,"Rajkot":139,"Sabar Kantha":144,
    "Surat":149,"Surendranagar":154,"Tapi":159,"Vadodara":164,"Valsad":169,
}

MEDICINE_ROWS = {
    "IFA Tablets (Adult)":438,
    "IFA Syrup (Paediatric)":453,
    "Paediatric Antibiotics":458,
    "Vitamin A Syrup":463,
    "ORS (New WHO)":468,
    "Albendazole 400mg":483,
    "Calcium Tablets":488,
}

SINGLE_ROWS = {
    "opd_attendance":191,
    "inpatient_male_adults":194,
    "inpatient_female_adults":196,
    "inpatient_head_count":223,
    "childhood_pneumonia":147,
    "childhood_malaria":156,
    "childhood_diarrhoea":157,
    "dengue_positive":170,
    "stockout_rate":235,
    "lab_tests_done":239,
    "patient_satisfaction":238,
    "anc_registered":8,
}

def _safe_int(val):
    try:
        if val is None or str(val).strip() in ["nan","None","","-"]: return 0
        return max(0, int(float(str(val).replace(",",""))))
    except: return 0

def _alert(days):
    if days<=7: return "CRITICAL"
    elif days<=14: return "WARNING"
    elif days<=30: return "WATCH"
    else: return "NORMAL"

def load_data(filepath="data/raw/B-Gujarat_May.xlsx"):
    print("[data_loader] Loading real HMIS file...")
    if not os.path.exists(filepath):
        print(f"[data_loader] File not found: {filepath}")
        return None

    raw = pd.read_excel(filepath, sheet_name="Data Item Wise Report", header=None)
    print(f"[data_loader] Raw shape: {raw.shape}")

    month = "May-2021"
    month_cell = str(raw.iloc[1,0])
    for m in ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]:
        if m in month_cell:
            month = f"{m}-2021"
            break

    records = []
    for medicine, start_row in MEDICINE_ROWS.items():
        for district, col in DISTRICT_COLUMNS.items():
            try:
                opening     = _safe_int(raw.iloc[start_row,   col])
                received    = _safe_int(raw.iloc[start_row+1, col])
                unusable    = _safe_int(raw.iloc[start_row+2, col])
                consumption = _safe_int(raw.iloc[start_row+3, col])
                closing     = _safe_int(raw.iloc[start_row+4, col])
                expected    = max(1, int((opening+received)*0.30))
                ratio       = round(consumption/max(expected,1), 3)
                daily       = consumption/30 if consumption>0 else 1
                days        = min(int(closing/max(daily,1)), 90)

                health = {}
                for ind, row in SINGLE_ROWS.items():
                    health[ind] = _safe_int(raw.iloc[row, col])

                opd = health.get("opd_attendance",1)
                lab = health.get("lab_tests_done",0)
                inpatients = health.get("inpatient_male_adults",0) + health.get("inpatient_female_adults",0)
                head = health.get("inpatient_head_count",0)
                bed_rate = min(round(head/max(60,1),3), 1.0)

                is_monsoon = int(any(m in month for m in ["Jun","Jul","Aug","Sep"]))
                month_idx  = {"Apr":0,"May":1,"Jun":2,"Jul":3,"Aug":4,"Sep":5,
                              "Oct":6,"Nov":7,"Dec":8,"Jan":9,"Feb":10,"Mar":11}.get(month[:3],0)

                records.append({
                    "month":month, "district":district, "medicine":medicine,
                    "opening_stock":opening, "stocks_received":received,
                    "unusable_stock":unusable, "consumption":consumption,
                    "closing_stock":closing, "expected_consumption":expected,
                    "consumption_ratio":ratio, "days_remaining":days,
                    "alert_level":_alert(days),
                    "is_monsoon":is_monsoon, "month_idx":month_idx,
                    "bed_occupancy_rate":bed_rate, "total_inpatients":inpatients,
                    "lab_to_opd_ratio":round(lab/max(opd,1),3),
                    "has_stockout":int(health.get("stockout_rate",0)>0),
                    **health
                })
            except Exception as e:
                continue

    df = pd.DataFrame(records)
    df["closing_stock"]     = df["closing_stock"].clip(lower=0)
    df["days_remaining"]    = df["days_remaining"].clip(lower=0, upper=90)
    df["consumption_ratio"] = df["consumption_ratio"].clip(upper=10.0)
    df = df.fillna(0)

    print(f"[data_loader] Records: {len(df):,}")
    print(f"[data_loader] Districts: {df['district'].nunique()}")
    print(f"[data_loader] Medicines: {df['medicine'].nunique()}")
    print(f"[data_loader] CRITICAL: {(df['alert_level']=='CRITICAL').sum()}")
    print(f"[data_loader] WARNING : {(df['alert_level']=='WARNING').sum()}")
    return df

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        print("\nSample:")
        print(df[["district","medicine","consumption","closing_stock","days_remaining","alert_level"]].head(10))
        os.makedirs("data/processed", exist_ok=True)
        df.to_csv("data/processed/hmis_processed.csv", index=False)
        print(f"\nSaved: data/processed/hmis_processed.csv")