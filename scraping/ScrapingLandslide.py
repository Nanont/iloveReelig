import requests
import pandas as pd
from datetime import datetime
from pyproj import Transformer #pip install pyproj

# ดึงข้อมูลจาก ArcGIS API
url = "https://gisportal.dmr.go.th/arcgis/rest/services/HAZARD/PLACE_IMP/MapServer/0/query"
params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "json"
}

res = requests.get(url, params=params)
data = res.json()

features = data.get("features", [])

# เตรียมแปลงพิกัดจาก UTM Zone 47N → WGS84
transformer = Transformer.from_crs("epsg:32647", "epsg:4326", always_xy=True)

# แปลงเป็น DataFrame พร้อมแปลงพิกัด
records = []
for f in features:
    attr = f["attributes"]
    geom = f.get("geometry", {})
    utm_x = geom.get("x")
    utm_y = geom.get("y")
    if utm_x and utm_y:
        lon, lat = transformer.transform(utm_x, utm_y)
        coords = f"{lat},{lon}"
    else:
        coords = ""

    records.append({
        "type": "พื้นที่เสี่ยงภัยดินถล่ม",
        "organization": "กรมทรัพยากรธรณี",
        "comment": attr.get("LOCATION", "") + " | รายละเอียด: " + attr.get("TYPE", ""),
        "photo": "",
        "photo_after": "",
        "coords": coords,
        "address": attr.get("LOCATION", ""),
        "subdistrict": attr.get("TAMBON", ""),
        "district": attr.get("DISTRICT", ""),
        "province": attr.get("PROVINCE", ""),
        "timestamp": datetime.now().isoformat(),
        "state": "",
        "star": 0,
        "count_reopen": 0,
        "last_activity": datetime.now().isoformat()
    })

df_out = pd.DataFrame(records)

df_out["ticket_id"] = ["EXT-%05d" % (i + 1828) for i in range(len(df_out))]

cols = ["ticket_id"] + [col for col in df_out.columns if col != "ticket_id"]
df_out = df_out[cols]

df_out.to_csv("data_raw/external_raw/landslide_TH.csv", index=False, encoding="utf-8-sig")
print(f"✅ ดึงและแปลงข้อมูลสำเร็จ: {len(df_out)} รายการ")
