import pandas as pd
from datetime import datetime

csv_url = "https://data.bangkok.go.th/dataset/3fcbe9f7-d2b0-4442-b110-4a5620ebdce3/resource/8f1102d5-52a2-4494-9131-403e4f87a242/download/flood_risk.csv"

df_raw = pd.read_csv(csv_url)

# สร้าง DataFrame ตาม schema ที่ต้องการ

df_out = pd.DataFrame({
    "type": "{น้ำท่วม}",
    "organization": "Bangkok Flood Report",
    "comment": df_raw["name"] + " | รายละเอียด: " + df_raw["detail"].fillna(""),
    "photo": "",
    "photo_after": "",
    "coords": df_raw["y"].astype(str) + "," + df_raw["x"].astype(str),
    "address": df_raw["name"],
    "subdistrict": "",  # ถ้ายังไม่มีข้อมูลแขวง ให้เว้นไว้
    "district": df_raw["district"],
    "province": "กรุงเทพมหานคร",
    "timestamp": datetime.now().isoformat(),  # หรือใช้คอลัมน์เวลา (ถ้ามี)
    "state": df_raw["status_detail"].fillna(""),  
    "star": 0,
    "count_reopen": 0,
    "last_activity": datetime.now().isoformat()
})

df_out["ticket_id"] = ["EXT-%05d" % (i + 1091) for i in range(len(df_out))]

cols = ["ticket_id"] + [col for col in df_out.columns if col != "ticket_id"]
df_out = df_out[cols]

df_out.to_csv("data_raw/external_raw/flood_risk!!!.csv", index=False, encoding="utf-8-sig")
print("✅ แปลงข้อมูลสำเร็จ:", len(df_out), "รายการ")

