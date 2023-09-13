import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import plotly.express as px
# pip install bokeh==2.4.3
from bokeh.plotting import figure as bok

from data_analysis import get_HPFC_data, merge_HPFC_data

st.set_page_config(
    page_title="Streamlit for HPFC",
    page_icon="📈",
    layout="wide"
)

st.title("Test Streamlit !")
st.write("We want to see if it would make a good data visualisation tool.")
st.write("We will recreate the HPFC Grafiken here.")


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

#ne_plotte_pas_tout = """
HPFC_Prognose = st.columns(len(countries))
colors = ["green", "blue", "red"]
dates_prognose = [dates[d] for d in [0,1,3]]

with st.container():
    with HPFC_Prognose[0]:
        st.header("HPFC Prognose - " + countries[0] + "\nstreamlit line chart")
        st.line_chart(data=merged_df, x="Datum", y=["HPFC_" + countries[0] + "_" + d for d in dates_prognose])
    with HPFC_Prognose[1]:
        st.header("HPFC Prognose - " + countries[1] + "\nmatplotlib figure")
        #fig, ax = plt.plot(x=merged_df["Datum"], y=merged_df["HPFC_" + countries[1] + "_" + dates[d]] for d in [0,1,3])
        #st.pyplot(fig)
        fig, ax = plt.subplots()
        for i, d in enumerate(dates_prognose):
            ax.plot(merged_df["Datum"], merged_df["HPFC_" + countries[1] + "_" + d], label=d, color=colors[i])
            ax.legend()
        st.pyplot(fig)
    with HPFC_Prognose[2]:
        st.header("HPFC Prognose - " + countries[2] + "\naltair chart")

        hover = alt.selection_single( fields=["date"], nearest=True, on="mouseover", empty="none" )
        line1 = alt.Chart(merged_df).mark_line().encode( x='Datum', y='HPFC_FR_20230102', color=alt.value("green"))
        line2 = alt.Chart(merged_df).mark_line().encode( x='Datum', y='HPFC_FR_20230407', color=alt.value("blue"))
        line3 = alt.Chart(merged_df).mark_line().encode( x='Datum', y='HPFC_FR_20230414', color=alt.value("red"))
    
        tooltips = (
            alt.Chart(merged_df) .mark_rule() .encode(
                x="Datum", y="HPFC_FR_20230102",
                opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
                tooltip=[
                    alt.Tooltip("Datum", title="Datum"),
                    alt.Tooltip("HPFC_FR_20230102", title="HPFC FR 20230102 (EUR/MWh)"),
                    alt.Tooltip("HPFC_FR_20230407", title="HPFC FR 20230407 (EUR/MWh)"),
                    alt.Tooltip("HPFC_FR_20230414", title="HPFC FR 20230414 (EUR/MWh)"),
                ],
            ).add_selection(hover)
        )
        chart = alt.layer(line1, line2, line3, tooltips).resolve_scale(color='independent').interactive()
        st.altair_chart(chart)

with st.container():
    day_ahead_HPFC_Prognose = st.columns(len(countries))
    today = datetime.date(datetime(2023,4,17)) #dt.date.today()
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
#"""


with st.container():
    monatlicher_Mittelwerte = st.columns(len(countries))
    per_month = merged_df.set_index('Datum').groupby(pd.Grouper(freq='M')).mean()
    per_month["Datum"] = per_month.index.get_level_values('Datum')

    with monatlicher_Mittelwerte[0]:
        st.header("Monatlicher Mittelwert von HPFC Prognose - " + countries[0] + "\nvega_lite line chart")

        prognoseb1 = {
            "repeat": { "layer": ["HPFC_CH_20230407", "HPFC_CH_20230413", "HPFC_CH_20230414"] },
            "spec": { "layer": [{
                "mark": {"type": "line"},
                "encoding": {
                    "x": {"field": "Datum", "type": "temporal", "timeUnit": "yearmonth"},
                    "y": {"field": {"repeat": "layer"}, "type": "quantitative", "aggregate": "mean" , "title": "HPFC (EUR/MWh)"},
                    "stroke": {"datum": {"repeat": "layer"}, "type": "nominal"}
                }
                }]
            }}
        st.vega_lite_chart(merged_df, prognoseb1, use_container_width=True)
    
    with monatlicher_Mittelwerte[1]:
        st.header("Monatlicher Mittelwert von HPFC Prognose - " + countries[1] + "\nplotly line")
        prognoseb2 = px.line(per_month, x="Datum", y=["HPFC_DE_20230407", "HPFC_DE_20230413", "HPFC_DE_20230414"])
        st.plotly_chart(prognoseb2, use_container_width=True)

    with monatlicher_Mittelwerte[2]:
        st.header("Monatlicher Mittelwert von HPFC Prognose - " + countries[2] + "\nbokeh")
        mittelwert = bok(
            y_axis_label = "HPFC (EUR/MWh)hfoejfipezjfeom"
        )
        mittelwert.line(x=per_month["Datum"], y=per_month["HPFC_FR_20230407"], line_color="blue")
        mittelwert.line(x=per_month["Datum"], y=per_month["HPFC_FR_20230413"], line_color="lightblue")
        mittelwert.line(x=per_month["Datum"], y=per_month["HPFC_FR_20230414"], line_color="red")
        st.bokeh_chart(mittelwert, use_container_width=True)

