import streamlit as st
from datetime import datetime
import pandas as pd
from bokeh.plotting import figure as bok
from bokeh.layouts import column, row
from bokeh.models import DatetimeTickFormatter, HoverTool
from bokeh.plotting import figure

from data_analysis import get_HPFC_data, merge_HPFC_data

st.set_page_config(
    page_title="Streamlit Interactive",
    page_icon="🦝",
    layout="wide"
)

st.title("Test Streamlit Interactive !")
st.write("We will create here an interactive HPFC visualisation.")

countries = ["CH", "DE", "FR"]
dates = []
dates.append(datetime.date(datetime(2023,1,2)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,7)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,13)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,14)).strftime("%Y%m%d"))
dates.append(datetime.date(datetime(2023,4,17)).strftime("%Y%m%d"))

@st.cache_data
def get_products_df(countries, dates):
    merged_df = merge_HPFC_data(countries, dates)
    peak_df = merged_df.set_index('Datum').between_time('8:00', '19:30').reset_index()
    peak_df = peak_df[peak_df["Datum"].dt.dayofweek < 5]
    off_peak_df = pd.merge(merged_df, peak_df, how='outer', indicator=True)
    off_peak_df = off_peak_df.loc[off_peak_df._merge == 'left_only'].drop("_merge", axis=1)

    return merged_df, peak_df, off_peak_df

base_df, peak_df, off_peak_df = get_products_df(countries, dates)


with st.sidebar:

    st.header("Country")
    country_options = ("CH", "DE", "FR", "All")
    selected_country = st.selectbox( label="Choose a country:", options=country_options )

    if selected_country == "CH":
        st.caption("""Blabla 1 🍫""")
    if selected_country == "DE":
        st.caption("""Blabla 2 🥨""")
    if selected_country == "FR":
        st.caption("""Blabla 3 🥐""")
    if selected_country == "All":
        st.caption("""All countries (Switzerland, Germany and France)""")

    st.header("Product")
    product_options = ("base", "peak", "off-peak")
    selected_product = st.selectbox( label="Choose a product:", options=product_options )

    if selected_product == "base":
        st.caption("""All hours of the day, everyday""")
        source_df = base_df
    if selected_product == "peak":
        st.caption("""Week days from 8 am to 8 pm""")
        source_df = peak_df
    if selected_product == "off-peak":
        st.caption("""Week days from midnight to 8 am and from 8 pm to midnight and week-end days, all hours of the day""")
        source_df = off_peak_df

    st.header("Type")
    type_options = ("HPFC spot", "HPFC predictions")
    selected_type = st.selectbox( label="Choose a type of HPFC data:", options=type_options )

    if selected_type == "HPFC spot":
        st.caption("""Spot prices, past prices""")
    if selected_type == "HPFC predictions":
        st.caption("""HPFC predictions""")

    st.header("Date")
    date_options = ("date1", "date2")
    selected_date = st.selectbox( label="Choose a date / Choose several dates:", options=date_options )

    

prog_colors = ["green", "blue", "red"]
prog_dates = [dates[d] for d in [0,1,3]]


prog = bok( width=800, height=400, x_axis_type='datetime', y_axis_label = "HPFC (EUR/MWh)" )
prog.xaxis.formatter = DatetimeTickFormatter(years="%Y", months="%d-%m-%Y", days="%d-%m-%Y", hours="%d-%m %Hh", hourmin="%d-%m %Hh%M",  minutes="%d-%m %Hh%Mmin%S")
for d, date in enumerate(prog_dates):
    prog.line(source=source_df, x="Datum", y="HPFC_" + selected_country + "_" + date, line_color=prog_colors[d], legend_label=date)
prog.legend.click_policy="hide"
prog_hover = HoverTool(
    formatters={"@Datum": "datetime"},
    tooltips=[
        ("Datum", "@Datum{%Y-%m-%d}"),
        ("HPFC_"+selected_country+"_"+prog_dates[0], "@HPFC_"+selected_country+"_"+prog_dates[0]),
        ("HPFC_"+selected_country+"_"+prog_dates[1], "@HPFC_"+selected_country+"_"+prog_dates[1]),
        ("HPFC_"+selected_country+"_"+prog_dates[2], "@HPFC_"+selected_country+"_"+prog_dates[2])
            ])
prog.add_tools(prog_hover)
st.bokeh_chart(prog, use_container_width=True)