# Necessary imports
import streamlit as st
from datetime import datetime, timezone
import pandas as pd
import os, requests
from bokeh.plotting import figure as bok
from bokeh.models import DatetimeTickFormatter, HoverTool, Range1d
from bokeh.palettes import Category10, Reds8, Oranges8, Blues8, Purples8


# This is a Streamlit-hosted python app
# It allows the user to fetch spot- and hpfc-prices for several countries and several dates, and study the data.
# The user chooses parameters in the sidebar (countrie(s), product, date(s), granularity)
# The app automatically displays an interactive bokeh graph showing the prices for the selected parameters
# Some statistics on the chosen data and over the selected period are also displayed
# A click on the "Save as csv file" button will export the dataset corresponding to the selected data

# Emma implement error detection (what to do if data unavailable, what to plot, change legend, explain what the error is and how to fix it directly on the app)


# initialization of the parameters

countries =                   ["CH",          "DE",         "FR",       "AT"]
captions_countries =          ["Switzerland", "Germany",    "France",   "Austria"]
siloveda_spot_country_codes = [ 17210,         17208,        17209,      17207]
spot_colours_countries      = ["darkred",     "darkorange", "darkblue", "darkmagenta"]
hpfc_colours_countries      = [Reds8,          Oranges8,     Blues8,     Purples8]
products =          ["base", "peak", "off-peak"]
captions_products = ["All hours of the day, everyday",
                     "Week days from 8 am to 8 pm",
                     "Week days from midnight to 8 am and from 8 pm to midnight and week-end days, all hours of the day"]
granularities =        ["hourly", "daily", "weekly", "monthly", "quarterly", "yearly"]
granularity_codes =    ["H",      "D",     "W",      "M",       "Q",         "Y"]
granularity_tooltips = ["{%Y-%m-%d %Hh}", "{%Y-%m-%d}", "{week%W %Y}", "{%b %Y}", "{%F}", "{%Y}"]

if "dataframe" not in st.session_state: 
    st.session_state.dataframe = pd.DataFrame()
if "country" not in st.session_state:
    st.session_state.country = countries[0]
if "product" not in st.session_state:
    st.session_state.product = products[0]
if "is_checked_spot" not in st.session_state:
    st.session_state.is_checked_spot = False
if "is_checked_hpfc" not in st.session_state:
    st.session_state.is_checked_hpfc = False
if "hpfc_dates" not in st.session_state:
    st.session_state.hpfc_dates = []
if "start_slider_date" not in st.session_state:
    st.session_state.start_slider_date = datetime(2022, 1, 1)
if "end_slider_date" not in st.session_state:
    st.session_state.end_slider_date = datetime(2027, 1, 1)
if "graph_dates" not in st.session_state:
    st.session_state.graph_dates = ( st.session_state.start_slider_date, st.session_state.end_slider_date )
if "granularity" not in st.session_state:
    st.session_state.granularity = granularities[0]

data_path = "small_HPFC_data/"
#data_path = "K:/Dept/W/HUV.A04974/1000_Handel Front Office/1100_Admin/1170_User/Lelievre/HPFC/"


# useful functions to fetch and aggregate the data

@st.cache_data
def fetch_HPFC_data_from_filer(country, date, data_path):
    # need date as 8-characters string : yyyymmdd
    file_path = data_path + "HPFC_" + country +"_" + date + ".csv"
    if os.path.isfile(file_path):
        df = pd.read_csv(file_path, sep=";")
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
    else:
        df = pd.DataFrame()  
    return df

@st.cache_data
def fetch_spot_data_from_siloveda(country): # emma fetch heure par heure et pas milliseconde par milliseconde
    most_recent_spot = datetime.date(datetime.now(timezone.utc))
    beg_of_year = datetime(datetime.now().year-1, 1, 1)
    old_spot = datetime.date(datetime(datetime.now().year, 1, 1)).strftime("%Y-%m-%d")
    token = 'e45b081a-712c-34c1-238f-f94a328e2dfa'
    headers = {'SilovedaAPIKey': token, 'Content-Type': 'application/json'}
    parameters = {"from": beg_of_year, "to": most_recent_spot, "inclFrom": True, "inclTo": True}
    c_index = countries.index(country)
    code = siloveda_spot_country_codes[c_index]
    response = requests.get(
        "https://192.168.46.6:8121/SiloVedaServices/measuringdata_api/v3/timeSeries/"+str(code)+"/values",
        params=parameters, headers=headers, verify=False)
    resp = response.json()
    df = pd.DataFrame(resp)
    df = df.drop("state", axis=1)
    df = df.rename(columns={"ts": "Datum", "val": "spot_"+country})
    df["Datum"] = pd.to_datetime(df["Datum"], utc=True).dt.tz_convert('Europe/Zurich').dt.tz_localize(None)
    df["spot_"+country] = df["spot_"+country].astype(float)
    return df

@st.cache_data
def merge_datasets(datasets):
    merged_df = pd.DataFrame()
    for df in datasets:
        if len(df)>0:
            if len(merged_df)==0:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="Datum", how="outer")
    return merged_df

@st.cache_data
def separate_data_products(merged_df):
    if len(merged_df)>0:
        peak_df = merged_df.set_index('Datum').between_time('8:00', '19:30').reset_index()
        peak_df = peak_df[peak_df["Datum"].dt.dayofweek < 5]
        off_peak_df = pd.merge(merged_df, peak_df, how='outer', indicator=True)
        off_peak_df = off_peak_df.loc[off_peak_df._merge == 'left_only'].drop("_merge", axis=1)
    else:
        peak_df, off_peak_df = pd.DataFrame(), pd.DataFrame()
    return merged_df, peak_df, off_peak_df

@st.cache_data
def average_for_granularity(df, granularity):
    g_index = granularities.index(granularity)
    gran = granularity_codes[g_index]
    gran_df = pd.DataFrame()
    if len(df)>0:
        gran_df = df.set_index('Datum').groupby(pd.Grouper(freq=gran)).mean()
        gran_df.insert( loc=0, column="Datum", value=gran_df.index)
    return gran_df

def save_data(): # emma change file name ? and ask where the user would like to save it ?
    # save data in a csv file
    save_path = "C:/Users/u241397/OneDrive - SBB/Docs/Data visualisation/HPFC/Streamlit/saved_graphs/"
    save_name = "Visu_"+datetime.date(datetime.now()).strftime("%Y%m%d")+"_"+st.session_state.country+"_"+st.session_state.product+"_"+st.session_state.granularity+".csv"
    df = st.session_state.dataframe
    df.to_csv( save_path + save_name )


# building of the app

st.set_page_config(
    page_title="Preistool",
    page_icon="📈",
    layout="wide"
)

st.title("Preistool Energie-SBB")
st.write("Sie können mit diesem Tool die Energiepreise für verschiedene Länder, Datum und Produkte vergleichen.")


with st.sidebar:

    st.title("Selection of the desired data")

    st.header("Country")
    country_options = tuple( countries+["Alle"] )
    selected_country = st.selectbox( label="Choose a country:", options=country_options )
    st.session_state.country = selected_country
    if selected_country in countries:
        c_index = countries.index(selected_country)
        st.caption(captions_countries[c_index])
    if selected_country == "Alle":
        st.caption("All countries (Switzerland, Germany, France and Austria)")

    st.header("Product")
    product_options = tuple( products )
    selected_product = st.selectbox( label="Choose a product:", options=product_options )
    st.session_state.product = selected_product
    p_index = products.index(selected_product)
    st.caption(captions_products[p_index])
    
    st.header("Type")
    st.write("Choose a type of HPFC data:")
    is_checked_spot = st.checkbox(
        label="spot",
        help="Past prices"
    )
    st.session_state.is_checked_spot = is_checked_spot
    is_checked_hpfc = st.checkbox(
        label="HPFC",
        help="HPFC predictions"
    )
    st.session_state.is_checked_hpfc = is_checked_hpfc

    selected_hpfc_dates = []
    if is_checked_hpfc:
        st.header("HPFC date(s)")
        number_of_selected_hpfc_dates = st.number_input(
            label="How many HPFC dates do you want to display ?",
            min_value=1,
            max_value=8
        )
        for d in range(number_of_selected_hpfc_dates):
            selected_hpfc_dates.append( st.date_input( label="Date n°"+str(d+1)+":" ) )

    st.header("Date")
    selected_date = st.slider( 
        label="Choose dates to display the prices:",
        value=( st.session_state.start_slider_date, st.session_state.end_slider_date ),
        format="DD-MM-YYYY"
    )
    st.session_state.graph_dates = (selected_date[0], selected_date[1])

    st.header("Granularity")
    granularity_options = tuple( granularities )
    selected_granularity = st.selectbox( label="Choose a granularity:", options=granularity_options )
    st.session_state.granularity = selected_granularity
    st.caption(selected_granularity+" average")

    st.header("Export")
    st.button( label="Save as csv file", on_click=save_data)


graphs_tab, correlations_tab = st.tabs(["Graphs", "Correlations"])

hpfc_dates = []
if is_checked_hpfc:
    for date in selected_hpfc_dates:
        # we don't want double dates
        if date.strftime("%Y%m%d") not in hpfc_dates:
            hpfc_dates.append(date.strftime("%Y%m%d"))
st.session_state.hpfc_dates = hpfc_dates
if len(st.session_state.hpfc_dates) < 3:
    graph_colors = Category10[3][:len(hpfc_dates)]
else:
    graph_colors = Category10[len(hpfc_dates)]

datasets = []
if st.session_state.country == "Alle":
    # if the user wants to display all countries at the same time
    for country in countries:
        if st.session_state.is_checked_spot:
            datasets.append( fetch_spot_data_from_siloveda(country) )
        for date in st.session_state.hpfc_dates:
            datasets.append( fetch_HPFC_data_from_filer(country, date, data_path) )
else:
    # if the user only wants to display data for one country
    if st.session_state.is_checked_spot:
        datasets.append( fetch_spot_data_from_siloveda(st.session_state.country) )
    for date in st.session_state.hpfc_dates:
        datasets.append( fetch_HPFC_data_from_filer(st.session_state.country, date, data_path) )
merged_df = merge_datasets(datasets)
if len(merged_df)>0:
    st.session_state.start_slider_date = datetime.strptime(str(merged_df["Datum"].iloc[0]), "%Y-%m-%d %H:%M:%S")
    st.session_state.end_slider_date = datetime.strptime(str(merged_df["Datum"].iloc[-1]), "%Y-%m-%d %H:%M:%S")
base_df, peak_df, off_peak_df = separate_data_products(merged_df)
if st.session_state.product == "base":
    source_df = base_df
if st.session_state.product == "peak":
    source_df = peak_df
if st.session_state.product == "off-peak":
    source_df = off_peak_df
graph_df = source_df
stats_df = source_df
save_df = source_df
if len(source_df)>0:
    # limit the dataset to the start- and end-dates selected by the user
    stats_df = stats_df[ (stats_df["Datum"] > st.session_state.graph_dates[0]) & (stats_df["Datum"] < st.session_state.graph_dates[1]) ]
    save_df = save_df[ (save_df["Datum"] > st.session_state.graph_dates[0]) & (save_df["Datum"] < st.session_state.graph_dates[1]) ]
# modify the datasets to account for the granularity selected by the user
graph_df = average_for_granularity(graph_df, st.session_state.granularity)
save_df = average_for_granularity(save_df, st.session_state.granularity)
st.session_state.dataframe = save_df
if len(source_df)>0:
    # modify the dataset that we want to plot to account for missing data
    g_index = granularities.index(st.session_state.granularity)
    gran = granularity_codes[g_index]
    all_grans = pd.DataFrame(pd.date_range(graph_df['Datum'].min(), graph_df['Datum'].max(), freq=gran), columns=["Datum"]).set_index('Datum')
    graph_df = all_grans.merge(right=graph_df.set_index('Datum'), how='left', on='Datum')


with graphs_tab:
    # plot the desired prices 
    st.write("Zeitliche Entwicklung der Spot- und Hpfc-Preise in €/MWh")
    graph = bok( width=800, height=400, x_axis_type='datetime', y_axis_label = "HPFC (EUR/MWh)" )
    graph.xaxis.formatter = DatetimeTickFormatter(years="%Y", months="%b %Y", days="%d %b %Y", hours="%d %b %Hh", hourmin="%d %b %Hh%M",  minutes="%d %b %Hh%Mmin%S")
    graph.x_range = Range1d(st.session_state.graph_dates[0], st.session_state.graph_dates[1])
    g_index = granularities.index(st.session_state.granularity)
    gran_tt = granularity_tooltips[g_index]
    graph_tooltips=[ ("Datum", "@Datum"+gran_tt) ]
    if st.session_state.country == "Alle":
        # if the user wants to display all countries at the same time
        for c, country in enumerate(countries):
            for d, date in enumerate(st.session_state.hpfc_dates):
                graph.line(source=graph_df, x="Datum", y="HPFC_"+country+"_"+date, line_color=hpfc_colours_countries[c][d], legend_label=country+"-"+date)
                graph_tooltips.append( ("HPFC_"+country+"_"+date, "@HPFC_"+country+"_"+date) )
            if st.session_state.is_checked_spot:
                # plot spot prices in dark colors
                graph.line(source=graph_df, x="Datum", y="spot_"+country, line_color=spot_colours_countries[c], legend_label=country+"-spot")
                graph_tooltips.append( ("spot_"+country, "@spot_"+country) )
    else:
        # if the user only wants to display data for one country
        for d, date in enumerate(st.session_state.hpfc_dates):
            graph.line(source=graph_df, x="Datum", y="HPFC_"+st.session_state.country+"_"+date, line_color=graph_colors[d], legend_label=date)
            graph_tooltips.append( ("HPFC_"+st.session_state.country+"_"+date, "@HPFC_"+st.session_state.country+"_"+date) )
        if st.session_state.is_checked_spot:
            # plot spot prices in black
            graph.line(source=graph_df, x="Datum", y="spot_"+st.session_state.country, line_color="black", legend_label=st.session_state.country+"-spot")
            graph_tooltips.append( ("spot_"+st.session_state.country, "@spot_"+st.session_state.country) )
    graph.legend.click_policy="hide"
    graph_hover = HoverTool(
        formatters={"@Datum": "datetime"},
        tooltips=graph_tooltips)
    graph.add_tools(graph_hover)
    st.bokeh_chart(graph, use_container_width=True)

    # display relevant statistics on the plotted data
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("Statistik über die ", st.session_state.country, " ", st.session_state.product, " Preise für den ausgewählten Zeitraum")
    mean_statistics = [stats_df[col].mean() for col in stats_df.columns[1:]]
    min_statistics = [stats_df[col].min() for col in stats_df.columns[1:]]
    max_statistics = [stats_df[col].max() for col in stats_df.columns[1:]]
    statistics_index = stats_df.columns[1:]
    graph_statistics = pd.DataFrame({"Mean value" : mean_statistics, "Min value" : min_statistics, "Max value" : max_statistics}, index=statistics_index)
    st.table(graph_statistics.style.format("{:.1f}"))

with correlations_tab:
    st.write("Blabla Correlations")

