import requests
import pandas as pd
from datetime import datetime

# โหลด JSON จากไฟล์หรือ URL
url = "https://data.go.th/dataset/d37c09dc-6939-492c-b7bf-6e15d3597998/resource/6dccd462-9d84-4f53-b8c2-7bfcda7e1d7c/download/risk.json"
data = requests.get(url).json()

# ดึง feature list
features = data["features"]

# เตรียมข้อมูลให้อยู่ในรูป list of dict
rows = []
for feature in features:
    prop = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    
    rows.append({
        "type": "{ที่ตั้งจุดเสี่ยงภัยสะพานลอยและป้ายรถโดยสารประจำทาง}", 
        "organization": "กรมป้องกันและบรรเทาสาธารณภัย",
        "comment": prop["location"],
        "photo": "",
        "photo_after": "",
        "coords": f"{coords[1]},{coords[0]}",  # NOTE: Y,X
        "address": prop["location"],
        "subdistrict": "",  # ไม่ระบุในข้อมูลต้นทาง
        "district": "",     # ไม่ระบุเช่นกัน
        "province": "กรุงเทพมหานคร",  # จาก dcode พอเดาได้ว่าอยู่ใน กทม.
        "timestamp": datetime.now().isoformat(),
        "state": "",  # ไม่มีข้อมูลเพิ่มเติมใน field นี้
        "star": 0,
        "count_reopen": 0,
        "last_activity": datetime.now().isoformat()
    })

# สร้าง DataFrame และบันทึกเป็น CSV
df_out = pd.DataFrame(rows)

df_out["ticket_id"] = ["EXT-%05d" % (i + 3828) for i in range(len(df_out))]

cols = ["ticket_id"] + [col for col in df_out.columns if col != "ticket_id"]
df_out = df_out[cols]

df_out.to_csv("data_raw/external_raw/risk_path.csv", index=False, encoding="utf-8-sig")

print("✅ บันทึกไฟล์ risk_points_cleaned.csv เรียบร้อย:", len(df_out), "รายการ")
