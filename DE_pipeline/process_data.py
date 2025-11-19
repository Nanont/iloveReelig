from pathlib import Path
import pandas as pd
import os

# ---------- 1. เตรียม path ของไฟล์ ----------
# project_root = โฟลเดอร์ project/ (หนึ่งระดับเหนือไฟล์นี้)
project_root = Path(__file__).resolve().parents[1]

traffy_path   = str(project_root / "data_clean" / "bangkok_traffy_clean.csv")
external_dir  = str(project_root / "data_raw" / "external_raw")
output_path   = str(project_root / "data_processed" / "processed_final_data.csv")

print("Traffy:", traffy_path)
print("External:", external_dir)
print("Output:", output_path)

# ---------- 2. อ่าน CSV ด้วย pandas ----------
try:
    traffy_df = pd.read_csv(traffy_path)
    print("Traffy rows:", len(traffy_df))
except FileNotFoundError:
    print(f"Warning: {traffy_path} not found")
    traffy_df = pd.DataFrame()

# โหลด external files ทั้งหมด และ concat เข้าด้วยกัน
external_files = []
for file in sorted(os.listdir(external_dir)):
    if file.endswith('.csv'):
        file_path = os.path.join(external_dir, file)
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded {file}: {len(df)} rows")
            external_files.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")

# concat all external files
if external_files:
    external_df = pd.concat(external_files, ignore_index=True)
    print(f"Total external rows (all files combined): {len(external_df)}")
else:
    external_df = pd.DataFrame()
    print("No external files loaded")

# ---------- 3. Join traffy กับ external data โดย ticket_id ----------
# เมื่อ join by ticket_id จะเพิ่มแถวใหม่สำหรับ external incidents ที่ไม่อยู่ใน traffy
join_col = "ticket_id"

if len(traffy_df) > 0 and len(external_df) > 0:
    # ทำให้ sure ticket_id เป็น string
    traffy_df[join_col] = traffy_df[join_col].astype(str)
    external_df[join_col] = external_df[join_col].astype(str)
    
    # outer join เพื่อเก็บ traffy ทั้งหมด + external records ที่ไม่มีใน traffy
    joined_df = traffy_df.merge(external_df, on=join_col, how="outer", suffixes=("_traffy", "_external"))
    print(f"Joined rows (traffy + new external): {len(joined_df)}")
    print(f"  Original traffy: {len(traffy_df)}")
    print(f"  New external incidents added: {len(joined_df) - len(traffy_df)}")
else:
    print(f"Warning: Using traffy_df only.")
    joined_df = traffy_df

# ---------- 4. Feature Engineering ตัวอย่าง ----------
if len(joined_df) > 0:
    # เลือกเฉพาะคอลัมน์ที่มีใน traffy_df เดิม
    # ได้คอลัมน์จาก traffy เป็น priority ถ้า outer join มี suffix _traffy/_external
    selected_cols = [
        "ticket_id",
        "type",
        "organization",
        "coords",
        "province",
        "timestamp",
        "state",
        "star",
        "count_reopen",
        "last_activity",
        "lat",
        "lon"
    ]
    
    # ต้องจัดการกับ suffixes (_traffy, _external) ที่เกิดจากการ outer join
    # ลองใช้คอลัมน์เดิมก่อน ถ้าไม่มีให้ใช้ version กับ suffix
    final_cols = []
    for col in selected_cols:
        if col in joined_df.columns:
            final_cols.append(col)
        elif f"{col}_traffy" in joined_df.columns:
            # rename ให้เป็นชื่อเดิม
            joined_df[col] = joined_df[f"{col}_traffy"].fillna(joined_df.get(f"{col}_external"))
            final_cols.append(col)
        elif f"{col}_external" in joined_df.columns:
            joined_df[col] = joined_df[f"{col}_external"]
            final_cols.append(col)
    
    if final_cols:
        processed_df = joined_df[final_cols]
    else:
        processed_df = joined_df
    
    # ---------- 5. เขียนออกเป็น CSV ----------
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_df.to_csv(output_path, index=False)
    print(f"Finished writing processed data to {output_path}")
    print(f"Output shape: {processed_df.shape}")
else:
    print("No data to process")
