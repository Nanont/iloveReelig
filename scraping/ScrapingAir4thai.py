# import requests
# import pandas as pd

# url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php?region=1"
# data = requests.get(url).json()

# df = pd.DataFrame(data["stations"])
# print(df.head())

# from datetime import datetime

# df_out = pd.DataFrame({
#     "type": "pm25",
#     "organization": "Air4Thai",
#     "comment": df["nameTH"],
#     "photo": "",
#     "photo_after": "",
#     "coords": df["lat"].astype(str) + "," + df["long"].astype(str),
#     "address": "",
#     "subdistrict": "",
#     "district": "",
#     "province": "กรุงเทพมหานคร",
#     "timestamp": datetime.now().isoformat(),
#     "state": "open",
#     "star": 0,
#     "count_reopen": 0,
#     "last_activity": datetime.now().isoformat()
# })

# df_out.to_csv("pm25_api.csv", index=False, encoding="utf-8-sig")


import requests
import pandas as pd
from datetime import datetime

url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php?region=1"
data = requests.get(url).json()

records = []

for station in data["stations"]:
    info = station.get("AQILast", {})
    
    comment = f"สถานี: {station.get('nameTH', '')} | "
    comment += f"PM2.5: {info.get('PM2.5', {}).get('value', '-')}"
    comment += f" (AQI {info.get('PM2.5', {}).get('aqi', '-')}) | "
    comment += f"PM10: {info.get('PM10', {}).get('value', '-')} | "
    comment += f"CO: {info.get('CO', {}).get('value', '-')} | "
    comment += f"O3: {info.get('O3', {}).get('value', '-')} | "
    comment += f"NO2: {info.get('NO2', {}).get('value', '-')} | "
    comment += f"SO2: {info.get('SO2', {}).get('value', '-')} | "
    comment += f"เวลา: {info.get('date', '')} {info.get('time', '')}"

    records.append({
        "type": "{PM2.5}",
        "organization": "Air4Thai",
        "comment": comment,
        "photo": "",
        "photo_after": "",
        "coords": f"{station.get('lat', '')},{station.get('long', '')}",
        "address": station.get("areaTH", ""),
        "subdistrict": "",
        "district": "",
        "province": "กรุงเทพมหานคร",
        "timestamp": datetime.now().isoformat(),
        "state": "open",
        "star": 0,
        "count_reopen": 0,
        "last_activity": datetime.now().isoformat()
    })

df_out = pd.DataFrame(records)

df_out["ticket_id"] = ["EXT-%05d" % i for i in range(1, len(df_out)+1)]

cols = ["ticket_id"] + [col for col in df_out.columns if col != "ticket_id"]
df_out = df_out[cols]

df_out.to_csv("data_raw/external_raw/pm25_api_full.csv", index=False, encoding="utf-8-sig")
print("✅ บันทึกข้อมูลสำเร็จ:", len(df_out), "รายการ")
