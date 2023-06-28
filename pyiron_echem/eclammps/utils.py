import pandas as pd
from pathlib import Path
import os

def collect_model_devi(filename="model_devi.out", ):

    if not os.path.exists(filename):
        return pd.DataFrame()
    with open(filename, "r") as f:
        f.seek(0)
        header_info = f.readline()
    header_info = header_info.split()[1::]
    df = pd.read_csv(filename, sep='\s{2,}',header=0, names=header_info)

    return df

