from pathlib import Path
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    coalesce,
    lit,
    split,
    trim,
    concat_ws,
)



import pandas  # เอาไว้ใช้ตอน toPandas() + to_csv

# บังคับให้ Spark ใช้ Python ตัวเดียวกับที่รันสคริปต์นี้
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


def main():
    # ---------- 1. เตรียม path ----------
    project_root = Path(__file__).resolve().parents[1]

    traffy_path = str(project_root / "data_clean" / "bangkok_traffy_clean.csv")
    external_dir = str(project_root / "data_raw" / "external_raw")
    output_path = str(project_root / "data_processed" / "processed_final_data")  # โฟลเดอร์

    print("Traffy:", traffy_path)
    print("External dir:", external_dir)
    print("Output dir:", output_path)

    # ---------- 2. สร้าง SparkSession ----------
    spark = (
        SparkSession.builder
        .appName("iloveReelig_process_data")
        .master("local[*]")  # รันบนเครื่องเรา
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow")
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow")
        .config("spark.sql.ansi.enabled", "false")  # กัน error cast datetime แบบ strict
        .getOrCreate()
    )

    # ---------- 3. อ่าน traffy CSV ----------
    try:
        traffy_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("multiLine", True)   # <— สำคัญสุด!
    .option("quote", '"')        # field ที่ครอบด้วย " ... "
    .option("escape", '"')       # escape " ข้างใน field
    .csv(traffy_path)
)
        print("Traffy rows:", traffy_df.count())
        print("Traffy columns:", traffy_df.columns)
    except Exception as e:
        print(f"Warning: cannot load traffy: {e}")
        # สร้าง DF ว่าง ๆ ไว้ก่อน (เดี๋ยวเติมคอลัมน์ทีหลัง)
        traffy_df = spark.createDataFrame([], schema="ticket_id string")

    # ---------- 4. โหลด external CSV ทั้งโฟลเดอร์ แล้ว union ----------

    external_df = None

    if os.path.isdir(external_dir):
        csv_files = [
            os.path.join(external_dir, f)
            for f in sorted(os.listdir(external_dir))
            if f.endswith(".csv")
        ]

        if csv_files:
            print("External files:")
            dfs = []
            for f in csv_files:
                print("  ", f)
                try:
                    df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("multiLine", True)
    .option("quote", '"')
    .option("escape", '"')
    .csv(f)
)

                    print(f"Loaded {os.path.basename(f)}: {df.count()} rows")
                    dfs.append(df)
                except Exception as e:
                    print(f"Error loading {f}: {e}")

            if dfs:
                external_df = dfs[0]
                for d in dfs[1:]:
                    external_df = external_df.unionByName(d, allowMissingColumns=True)

                print("Total external rows:", external_df.count())
                print("External columns:", external_df.columns)
            else:
                print("No external files loaded (all failed)")
        else:
            print("No external .csv files found in directory")
    else:
        print(f"Warning: external directory {external_dir} not found")

    # ============================================================
    #   5. เตรียม schema ปลายทางที่เราอยากได้ (เหมือน pandas version)
    # ============================================================

    final_cols = [
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
        "lon",
    ]

    # ---------- 5.1 Normalize Traffy ให้มีทุกคอลัมน์ + type ให้ตรง ----------

    traffy_norm = traffy_df

    # ticket_id เป็น string
    if "ticket_id" in traffy_norm.columns:
        traffy_norm = traffy_norm.withColumn("ticket_id", col("ticket_id").cast("string"))
    else:
        traffy_norm = traffy_norm.withColumn("ticket_id", lit(None).cast("string"))

    # เติมคอลัมน์ที่อาจยังไม่มีใน traffy ให้ครบ
    for c in [
        "type",
        "organization",
        "coords",
        "lat",
        "lon",
        "subdistrict",
        "district",
        "province",
        "timestamp",
        "state",
        "star",
        "count_reopen",
        "last_activity"
    ]:
        if c not in traffy_norm.columns:
            traffy_norm = traffy_norm.withColumn(c, lit(None))

    # แปลง lat/lon เป็น double
    traffy_norm = (
        traffy_norm
        .withColumn("lat", col("lat").cast("double"))
        .withColumn("lon", col("lon").cast("double"))
    )

    # ถ้า coords ใน traffy ว่าง ให้สร้างจาก lat/lon
    traffy_norm = traffy_norm.withColumn(
        "coords",
        coalesce(
            col("coords").cast("string"),
            concat_ws(",", col("lat").cast("string"), col("lon").cast("string")),
        ),
    )

    # เลือกเฉพาะคอลัมน์ปลายทาง
    traffy_norm = traffy_norm.select(*final_cols)

    print("Traffy_norm schema:")
    traffy_norm.printSchema()

    # ---------- 5.2 Normalize External ให้ schema เหมือนกัน ----------

    if external_df is not None:
        # กันแถวเพี้ยน ๆ: เอาเฉพาะ ticket_id ที่ขึ้นต้นด้วย "EXT-" (ตาม sample ที่ให้มา)
        if "ticket_id" in external_df.columns:
            external_df = external_df.filter(col("ticket_id").startswith("EXT-"))

        ecols = external_df.columns

        # เติมคอลัมน์ที่อาจยังไม่มีให้ครบ
        for c in [
        "type",
        "organization",
        "coords",
        "lat",
        "lon",
        "subdistrict",
        "district",
        "province",
        "timestamp",
        "state",
        "star",
        "count_reopen",
        "last_activity"
    ]:
            if c not in ecols:
                external_df = external_df.withColumn(c, lit(None))

        external_norm = external_df

        # ticket_id เป็น string
        external_norm = external_norm.withColumn(
            "ticket_id", col("ticket_id").cast("string")
        )

        # ทำ coords ให้เป็น string สะอาด ๆ
        external_norm = external_norm.withColumn(
            "coords", trim(col("coords").cast("string"))
        )

        # แตก coords: "lat,lon" → lat, lon
        external_norm = (
            external_norm
            .withColumn(
                "lat",
                split(col("coords"), ",").getItem(0).cast("double"),
            )
            .withColumn(
                "lon",
                split(col("coords"), ",").getItem(1).cast("double"),
            )
        )

        # แปลง timestamp / last_activity เป็น string (หรือจะ cast เป็น timestamp ก็ได้ ถ้าอยากใช้ต่อ)
        external_norm = (
            external_norm
            .withColumn("timestamp", col("timestamp").cast("string"))
            .withColumn("last_activity", col("last_activity").cast("string"))
        )

        # เลือกเฉพาะคอลัมน์ปลายทาง
        external_norm = external_norm.select(*final_cols)

    else:
        # ถ้าไม่มี external เลย สร้าง DF ว่าง ๆ ที่ schema เหมือน traffy
        external_norm = spark.createDataFrame([], traffy_norm.schema)

    print("External_norm schema:")
    external_norm.printSchema()

    # ============================================================
    #   6. รวม Traffy + External ด้วย union (ไม่ join แล้ว)
    # ============================================================

    processed_df = traffy_norm.unionByName(external_norm, allowMissingColumns=True)

    # กันแถวขยะ: ticket_id null / ว่าง
    processed_df = processed_df.filter(
        col("ticket_id").isNotNull() & (trim(col("ticket_id")) != "")
    )

    print("Output row count:", processed_df.count())
    print("Output schema:")
    processed_df.printSchema()

    # ---------- 7. เขียนออกเป็น CSV ด้วย pandas (เลี่ยง Hadoop/winutils) ----------

    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "processed_final_data.csv"

    # ให้ Spark ทำงานหนักเสร็จ แล้วค่อยดึงเป็น pandas
    pdf = processed_df.toPandas()

    # เขียน CSV ด้วย pandas (ไม่แตะ Hadoop I/O บน Windows)
    pdf.to_csv(out_file, index=False, encoding="utf-8-sig")

    print(f"Finished writing output CSV: {out_file}")


if __name__ == "__main__":
    main()
