# import requests
# import pandas as pd
# from datetime import datetime

# # API URL และ Header พร้อม Key
# url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood-freq"
# headers = {
#     "accept": "application/json",
#     "API-Key": "EFH7ZXZ0riZUP9oMgiRyC6x8UESdYK4CNOffGjF9x4d6lfrxq8V4gNUUIgWxnCJe"
# }
# params = {
#     "bbox": "100.28,13.52,100.95,14.2",  # ขอบเขตกรุงเทพฯ
#     "limit": 1000,
#     "offset": 0
# }

# # ดึงข้อมูล
# response = requests.get(url, headers=headers, params=params)
# data = response.json()

# # แปลงข้อมูล
# records = []
# for feature in data.get("features", []):
#     prop = feature.get("properties", {})
#     geom = feature.get("geometry", {}).get("coordinates", [])
#     if len(geom) >= 2:
#         coords = f"{geom[1]},{geom[0]}"
#     else:
#         coords = ""


#     records.append({
#         "type": "น้ำท่วม",
#         "organization": "GISTDA",
#         "comment": f"พื้นที่: {prop.get('tambon', '')} อ.{prop.get('amphoe', '')} จ.{prop.get('changwat', '')} | ความถี่น้ำท่วม: {prop.get('count_flood', '')} ครั้ง",
#         "photo": "",
#         "photo_after": "",
#         "coords": coords,
#         "address": "",
#         "subdistrict": prop.get("tambon", ""),
#         "district": prop.get("amphoe", ""),
#         "province": prop.get("changwat", ""),
#         "timestamp": datetime.now().isoformat(),
#         "state": "open",
#         "star": 0,
#         "count_reopen": 0,
#         "last_activity": datetime.now().isoformat()
#     })


# # # สร้าง DataFrame และบันทึก CSV
# # df_out = pd.DataFrame(records)
# # df_out.to_csv("gistda_floodrisk.csv", index=False, encoding="utf-8-sig")
# # print("✅ ดึงข้อมูลและแปลง CSV สำเร็จ:", len(df_out), "รายการ")

# import pandas as pd
# import requests

# url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood-freq"
# headers = {
#     "accept": "application/json",
#     "API-Key": "EFH7ZXZ0riZUP9oMgiRyC6x8UESdYK4CNOffGjF9x4d6lfrxq8V4gNUUIgWxnCJe"
# }
# params = {
#     "bbox": "100.28,13.52,100.95,14.2",  # กทม
#     "limit": 1000,
#     "offset": 0
# }

# response = requests.get(url, headers=headers, params=params)
# data = response.json()

# # แปลงเป็น DataFrame
# records = []
# for feature in data.get("features", []):
#     props = feature.get("properties", {})
#     geom = feature.get("geometry", {}).get("coordinates", [])
#     # เอาจุดกลางของ polygon แรกใน multipolygon มาเป็นจุดแสดง
#     try:
#         center = geom[0][0][0]
#         lon, lat = center[0], center[1]
#         coords = f"{lat},{lon}"
#     except Exception:
#         coords = ""

#     records.append({
#         "label": props.get("LabelTH", ""),
#         "year_2011": props.get("y_2011", ""),
#         "year_2012": props.get("y_2012", ""),
#         "year_2013": props.get("y_2013", ""),
#         "shape_area": props.get("shape_area", ""),
#         "shape_leng": props.get("shape_leng", ""),
#         "coords": coords
#     })

# df = pd.DataFrame(records)
# df.to_csv("flood_freq_gistda.csv", index=False, encoding="utf-8-sig")
# print(f"✅ บันทึกสำเร็จ {len(df)} รายการ")



import requests
import pandas as pd
from datetime import datetime

url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood/30days"
headers = {
    "accept": "application/json",
    "API-Key": "EFH7ZXZ0riZUP9oMgiRyC6x8UESdYK4CNOffGjF9x4d6lfrxq8V4gNUUIgWxnCJe"
}
params = {
    "bbox": "100.28,13.52,100.95,14.2",
    "limit": 1000,
    "offset": 0
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

records = []
for feature in data.get("features", []):
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [])

    # หาค่ากลางของพิกัด polygon
    try:
        lat = coords[0][0][0][1]
        lon = coords[0][0][0][0]
        coord_str = f"{lat},{lon}"
    except Exception:
        coord_str = ""

    records.append({
        "type": "น้ำท่วม",
        "organization": "GISTDA",
        "comment": props.get("LabelTH", "น้ำท่วม") + " | พท. (ตร.ม.): " + str(props.get("shape_area", "")),
        "photo": "",
        "photo_after": "",
        "coords": coord_str,
        "address": "",
        "subdistrict": "",
        "district": "",
        "province": "กรุงเทพมหานคร",
        "timestamp": props.get("_updatedAt", datetime.now().isoformat()),
        "state": "",  
        "star": 0,
        "count_reopen": 0,
        "last_activity": datetime.now().isoformat()
    })

df_out = pd.DataFrame(records)

df_out["ticket_id"] = ["EXT-%05d" % (i + 91) for i in range(len(df_out))]

cols = ["ticket_id"] + [col for col in df_out.columns if col != "ticket_id"]
df_out = df_out[cols]

df_out.to_csv("data_raw/external_raw/flood_30days_gistda_formatted.csv", index=False, encoding="utf-8-sig")
print("✅ บันทึกข้อมูลในรูปแบบ df_out สำเร็จ:", len(df_out), "รายการ")





