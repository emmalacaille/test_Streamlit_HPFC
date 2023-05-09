import pandas as pd
from datetime import datetime
import streamlit as st

data_path = "small_HPFC_data/"

@st.cache_data
def get_HPFC_data(country, date):
    # need date as 8-characters string : yyyymmdd
    # will need to implement error detection at some point
    df = pd.read_csv(data_path + "HPFC_" + country +"_" + date + ".csv", sep=";")
    df.columns.values[0] = "Datum"
    df = df.transpose()
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index()
    df = df.melt(id_vars=["index"], value_vars=list(df.columns)[1:])
    df["Datum"] = df["Datum"].astype(str) + " " + df["index"].astype(str) + "h"
    df = df.drop("index", axis=1)
    df["Datum"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y %Hh")
    df["value"] = df["value"].astype(float)
    df.columns = ["Datum", "HPFC" + "_" + country +"_" + date]
    
    return df

@st.cache_data
def merge_HPFC_data(countries, dates):
    merged_df = pd.DataFrame()
    for country in countries:
        for date in dates:
            df = get_HPFC_data(country, date)
            if len(merged_df)==0:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="Datum")
    return merged_df

    

