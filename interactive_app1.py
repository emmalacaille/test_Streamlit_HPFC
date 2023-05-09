import streamlit as st
from datetime import datetime
import pandas as pd
from bokeh.plotting import figure as bok
from bokeh.models import DatetimeTickFormatter, HoverTool, Range1d
from bokeh.palettes import Category10, Reds, Greens, Blues, Purples

from data_analysis import get_HPFC_data, merge_HPFC_data

st.set_page_config(
    page_title="Preistool",
    page_icon="📈",
    layout="wide"
)

st.title("Preistool Energie-SBB")
st.write("Sie können mit diesem Tool die Energiepreise für verschiedene Länder, Datum und Produkte vergleichen.")

countries = ["CH", "DE", "FR"]#, "AT"]

with st.sidebar:

    st.header("Country")
    country_options = tuple( countries+["Alle"] )
    selected_country = st.selectbox( label="Choose a country:", options=country_options )

    if selected_country == "CH":
        st.caption("Blabla 1 🤑")
    if selected_country == "DE":
        st.caption("Blabla 2 🥨")
    if selected_country == "FR":
        st.caption("Blabla 3 🥐")
    if selected_country == "AT":
        st.caption("Blabla 4 🌭")
    if selected_country == "Alle":
        st.caption("All countries (Switzerland, Germany, France and Austria)")

    st.header("Product")
    product_options = ("base", "peak", "off-peak")
    selected_product = st.selectbox( label="Choose a product:", options=product_options )

    if selected_product == "base":
        st.caption("All hours of the day, everyday")
    if selected_product == "peak":
        st.caption("Week days from 8 am to 8 pm")
    if selected_product == "off-peak":
        st.caption("Week days from midnight to 8 am and from 8 pm to midnight and week-end days, all hours of the day")

    st.header("Type")
    st.write("Choose a type of HPFC data:")
    checked_spot = st.checkbox(
        label="spot",
        help="Past prices"
    )
    checked_hpfc = st.checkbox(
        label="HPFC",
        help="HPFC predictions"
    )

    if checked_hpfc:
        st.header("HPFC date(s)")
        number_of_selected_hpfc_dates = st.number_input(
            label="How many HPFC dates do you want to display ?",
            min_value=1,
            max_value=8
        )
        selected_hpfc_dates = []
        for i in range(number_of_selected_hpfc_dates):
            selected_hpfc_dates.append( st.date_input( label="Date n°"+str(i+1)+":" ) )

    st.header("Date")
    selected_date = st.slider( 
        label="Choose dates to display the prices:",
        value=( datetime(2023, 1, 1),  datetime(2026, 12, 31)),
        format="DD-MM-YYYY"
    )


hpfc_dates = []
for date in selected_hpfc_dates:
    hpfc_dates.append(date.strftime("%Y%m%d"))

@st.cache_data
def get_products_df(countries, dates):
    merged_df = merge_HPFC_data(countries, dates)
    peak_df = merged_df.set_index('Datum').between_time('8:00', '19:30').reset_index()
    peak_df = peak_df[peak_df["Datum"].dt.dayofweek < 5]
    off_peak_df = pd.merge(merged_df, peak_df, how='outer', indicator=True)
    off_peak_df = off_peak_df.loc[off_peak_df._merge == 'left_only'].drop("_merge", axis=1)

    return merged_df, peak_df, off_peak_df

base_df, peak_df, off_peak_df = get_products_df(countries, hpfc_dates)

if selected_product == "base":
    source_df = base_df
if selected_product == "peak":
    source_df = peak_df
if selected_product == "off-peak":
    source_df = off_peak_df

  
if number_of_selected_hpfc_dates < 3:
    countries_colors = [Blues[3][:number_of_selected_hpfc_dates], Greens[3][:number_of_selected_hpfc_dates], Reds[3][:number_of_selected_hpfc_dates], Purples[3][:number_of_selected_hpfc_dates]]
    plot_colors = Category10[3][:number_of_selected_hpfc_dates]
else:
    countries_colors = [Blues[number_of_selected_hpfc_dates], Greens[number_of_selected_hpfc_dates], Reds[number_of_selected_hpfc_dates], Purples[number_of_selected_hpfc_dates]]
    plot_colors = Category10[number_of_selected_hpfc_dates]


plot = bok( width=800, height=400, x_axis_type='datetime', y_axis_label = "HPFC (EUR/MWh)" )
plot.xaxis.formatter = DatetimeTickFormatter(years="%Y", months="%d-%m-%Y", days="%d-%m-%Y", hours="%d-%m %Hh", hourmin="%d-%m %Hh%M",  minutes="%d-%m %Hh%Mmin%S")
plot.x_range = Range1d(selected_date[0], selected_date[1])
plot_tooltips=[ ("Datum", "@Datum{%Y-%m-%d}") ]
for d, date in enumerate(hpfc_dates):
    if selected_country == "Alle":
        for c, country in enumerate(countries):
            plot.line(source=source_df, x="Datum", y="HPFC_" + country + "_" + date, line_color=countries_colors[c][d], legend_label=country+"-"+date)
            plot_tooltips.append( ("HPFC_"+country+"_"+date, "@HPFC_"+country+"_"+date) )
    else:
        plot.line(source=source_df, x="Datum", y="HPFC_" + selected_country + "_" + date, line_color=plot_colors[d], legend_label=date)
        plot_tooltips.append( ("HPFC_"+selected_country+"_"+date, "@HPFC_"+selected_country+"_"+date) )
plot.legend.click_policy="hide"
plot_hover = HoverTool(
    formatters={"@Datum": "datetime"},
    tooltips=plot_tooltips)
plot.add_tools(plot_hover)
st.bokeh_chart(plot, use_container_width=True)
