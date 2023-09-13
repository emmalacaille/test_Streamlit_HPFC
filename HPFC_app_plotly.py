import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from data_analysis import get_HPFC_data, merge_HPFC_data

st.set_page_config(
    page_title="Streamlit & Plotly for HPFC",
    page_icon="🚉",
    layout="wide"
)

st.title("Test Streamlit with plotly graphs !")
st.write("We will recreate the HPFC Grafiken here, using plotly for visualisation.")

countries = ["CH", "DE", "FR"]
dates = []
dates.append(datetime.date(datetime(2023,1,2)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,7)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,13)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,14)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,17)).strftime("%Y%m%d"))
merged_df = merge_HPFC_data(countries, dates)
peak_df = merged_df.set_index('Datum').between_time('8:00', '19:30').reset_index()
st.dataframe(merged_df)


prog_colors = ["green", "blue", "red"]
prog_dates = [dates[d] for d in [0,1,3]]
HPFC_Prognose = st.columns(len(countries))
with st.container():
    for c, country in enumerate(countries):
        with HPFC_Prognose[c]:
            st.header("HPFC Prognose - " + country)
            prog = px.line(merged_df, x="Datum", y=["HPFC_" + country + "_" + date for date in prog_dates], color_discrete_sequence=prog_colors, labels=dict(Datum="", value="HPFC (EUR/MWh)", variable=""))
            st.plotly_chart(prog, use_container_width=True)
 

with st.container():
    day_ahead_HPFC_Prognose = st.columns(len(countries))
    today = datetime.date(datetime(2023,4,17))
    today = datetime.combine(today, datetime.min.time())
    tomorrow = today + timedelta(days = 1)
    after_tomorrow = today + timedelta(days = 2)
    yesterday = today - timedelta(days = 1)
    for c, country in enumerate(countries):
        base = merged_df[(merged_df["Datum"] >= tomorrow) & (merged_df["Datum"] < after_tomorrow)]
        peak = base[(base["Datum"] >= tomorrow + timedelta(hours = 8)) & (base["Datum"] < after_tomorrow - timedelta(hours = 4))]
        base = base["HPFC_" + country + "_" + today.strftime("%Y%m%d")]
        peak = peak["HPFC_" + country + "_" + today.strftime("%Y%m%d")]
        df_DA_HPFC_Prognose = pd.DataFrame({"Base" : [base.mean()], "Peak" : [peak.mean()]})
        with day_ahead_HPFC_Prognose[c]:
            st.header("Day-ahead " + tomorrow.strftime("%Y-%m-%d") + " HPFC " + country + " Prognose (EUR/MWh)")
            st.table(df_DA_HPFC_Prognose)


mittelwert_colors = [["blue", "dodgerblue"], ["forestgreen", "lawngreen"], ["red", "lightcoral"]]
mittelwert_dates = [dates[d] for d in [1,2,3]]
base_per_month = merged_df.set_index("Datum").groupby(pd.Grouper(freq='M')).mean()
base_per_month["Datum"] = base_per_month.index.get_level_values('Datum')
peak_per_month = peak_df.set_index("Datum").groupby(pd.Grouper(freq='M')).mean()
peak_per_month["Datum"] = peak_per_month.index.get_level_values('Datum')
with st.container():
    monatlicher_Mittelwerte = st.columns(len(countries))
    for c, country in enumerate(countries):
        with monatlicher_Mittelwerte[c]:
            st.header("Monatlicher Mittelwert von HPFC Prognose - " + country)
            mittelwert = go.Figure()
            for d, date in enumerate(mittelwert_dates):
                mittelwert.add_trace(go.Line(x=base_per_month["Datum"], y=base_per_month["HPFC_" + country + "_" + date], name=date+ " - base", line=dict(color=mittelwert_colors[d][0], width=2)))
                mittelwert.add_trace(go.Line(x=peak_per_month["Datum"], y=peak_per_month["HPFC_" + country + "_" + date], name=date+ " - peak", line=dict(color=mittelwert_colors[d][1], width=2)))
            mittelwert.update_layout(yaxis_title="HPFC (EUR/MWh) uizgfuiez")
            st.plotly_chart(mittelwert, use_container_width=True)
        