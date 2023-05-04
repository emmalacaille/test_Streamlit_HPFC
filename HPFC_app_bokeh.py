import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from bokeh.plotting import figure as bok
from bokeh.models import DatetimeTickFormatter, HoverTool

from data_analysis import get_HPFC_data, merge_HPFC_data

st.set_page_config(
    page_title="Streamlit & Bokeh for HPFC",
    page_icon="🚂",
    layout="wide"
)

st.title("Test Streamlit with bokeh graphs !")
st.write("We will recreate the HPFC Grafiken here, using bokeh for visualisation.")

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
            prog = bok( width=800, height=400, x_axis_type='datetime', y_axis_label = "HPFC (EUR/MWh)" )
            prog.xaxis.formatter = DatetimeTickFormatter(years="%Y", months="%d-%m-%Y", days="%d-%m-%Y", hours="%d-%m %Hh", hourmin="%d-%m %Hh%M",  minutes="%d-%m %Hh%Mmin%S")
            for d, date in enumerate(prog_dates):
                prog.line(source=merged_df, x="Datum", y="HPFC_" + country + "_" + date, line_color=prog_colors[d], legend_label=date)
            prog.legend.click_policy="hide"
            prog_hover = HoverTool(
                formatters={"@Datum": "datetime"},
                tooltips=[
                    ("Datum", "@Datum{%Y-%m-%d}"),
                    ("HPFC_"+country+"_"+prog_dates[0], "@HPFC_"+country+"_"+prog_dates[0]),
                    ("HPFC_"+country+"_"+prog_dates[1], "@HPFC_"+country+"_"+prog_dates[1]),
                    ("HPFC_"+country+"_"+prog_dates[2], "@HPFC_"+country+"_"+prog_dates[2])
            ])
            prog.add_tools(prog_hover)
            st.bokeh_chart(prog, use_container_width=True)
 

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
base_per_month = merged_df.set_index('Datum').groupby(pd.Grouper(freq='M')).mean()
base_per_month.columns = [col_name+"_base" for col_name in base_per_month.columns]
base_per_month["Datum"] = base_per_month.index.get_level_values('Datum')
base_per_month = base_per_month.reset_index(drop=True)
peak_per_month = peak_df.set_index('Datum').groupby(pd.Grouper(freq='M')).mean()
peak_per_month.columns = [col_name+"_peak" for col_name in peak_per_month.columns]
peak_per_month["Datum"] = peak_per_month.index.get_level_values('Datum')
peak_per_month = peak_per_month.reset_index(drop=True)
per_month =  pd.merge(base_per_month, peak_per_month, on="Datum")
st.dataframe(per_month)
with st.container():
    monatlicher_Mittelwerte = st.columns(len(countries))
    for c, country in enumerate(countries):
        with monatlicher_Mittelwerte[c]:
            st.header("Monatlicher Mittelwert von HPFC Prognose - " + country)
            mittelwert = bok( x_axis_type='datetime', y_axis_label = "HPFC (EUR/MWh)" )
            mittelwert.plot_height=400
            mittelwert.plot_width=800
            mittelwert.xaxis.formatter = DatetimeTickFormatter(years="%Y", months="%d-%m-%Y", days="%d-%m-%Y", hours="%d-%m %Hh", hourmin="%d-%m %Hh%M",  minutes="%d-%m %Hh%Mmin%S")
            mittelwert_tooltips=[("Datum", "@Datum{%Y-%m-%d}")]
            for d, date in enumerate(mittelwert_dates):
                mittelwert.line(source=per_month, x="Datum", y="HPFC_" + country + "_" + date + "_base", line_width=2, line_color=mittelwert_colors[d][0], legend_label=date+" - base")
                mittelwert.line(source=per_month, x="Datum", y="HPFC_" + country + "_" + date + "_peak", line_width=2, line_color=mittelwert_colors[d][1], legend_label=date+" - peak")
                mittelwert_tooltips.append( ("HPFC_"+country+"_"+date+" - base", "@HPFC_"+country+"_"+date+"_base") )
                mittelwert_tooltips.append( ("HPFC_"+country+"_"+date+" - peak", "@HPFC_"+country+"_"+date+"_peak") )
            mittelwert.legend.click_policy="hide"
            mittelwert_hover = HoverTool(
                formatters={"@Datum": "datetime"},
                tooltips=mittelwert_tooltips)
            mittelwert.add_tools(mittelwert_hover)
            st.bokeh_chart(mittelwert, use_container_width=True)
        
  
