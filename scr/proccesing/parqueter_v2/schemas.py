# schemas.py
import pyarrow as pa

# --------------------------------------------
# HUB definitions
# --------------------------------------------

HUBS = {
    "hub1": {"A": ["A33", "A34", "A35"],
             "S": ["S27", "S28", "S29"],
             "T": ["T4", "T5", "T6"]},

    "hub2": {"A": ["A30"],
             "S": ["S7","S8","S9","S10","S11","S12","S13","S14"],
             "T": ["T1"]},

    "hub3": {"A": ["A31"],
             "S": ["S15","S16","S17","S18"],
             "T": ["T2"]},

    "hub4": {"A": ["A32"],
             "S": ["S19","S20","S21","S22","S23","S24","S25","S26"],
             "T": ["T3"]},
}

# All accelerometers
ACCEL_ALL = (
    HUBS["hub1"]["A"]
  + HUBS["hub2"]["A"]
  + HUBS["hub3"]["A"]
  + HUBS["hub4"]["A"]
)

# --------------------------------------------
# ACCEL schema
# --------------------------------------------

accel_fields = [pa.field("datetime", pa.timestamp("us"))]
for a in ACCEL_ALL:
    accel_fields += [
        pa.field(f"{a}_t", pa.float32()),
        pa.field(f"{a}_x", pa.float32()),
        pa.field(f"{a}_y", pa.float32()),
        pa.field(f"{a}_z", pa.float32()),
    ]

ACCEL_ALL_SCHEMA = pa.schema(accel_fields)

# --------------------------------------------
# FFT schema
# --------------------------------------------

def make_fft_schema():
    return pa.schema([
        pa.field("datetime", pa.timestamp("us")),
        pa.field("sensor_id", pa.string()),
        pa.field("fft_main_f", pa.float32()),
        pa.field("fft_main_a", pa.float32()),
        pa.field("fft_freqs", pa.list_(pa.float32())),
        pa.field("fft_amps", pa.list_(pa.float32())),
    ])

# --------------------------------------------
# SST schema per hub
# --------------------------------------------

def make_sst_schema(hub):
    fields = [pa.field("datetime", pa.timestamp("us"))]
    for s in HUBS[hub]["S"]:
        fields.append(pa.field(s, pa.float32()))
    for t in HUBS[hub]["T"]:
        fields.append(pa.field(t, pa.float32()))
    return pa.schema(fields)
