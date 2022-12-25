from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
import geopandas as gpd

def getDrivecredentials():
    print("fetching drive credentials")
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('tokens/token-drive.json'):
        creds = Credentials.from_authorized_user_file('tokens/token-drive.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'tokens/drive_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('tokens/token-drive.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def getSheetcredentials():
    print("getting sheet credentials")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('tokens/sheet-token.json'):
        creds = Credentials.from_authorized_user_file('tokens/sheet-token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'tokens/sheet_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('tokens/sheet-token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def getDataFrame(credentials,SPREADSHEET_ID):
    print("reading " + SPREADSHEET_ID)
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    df = pd.DataFrame(result["values"], columns=result["values"][0])
    df.drop(0, inplace=True)
    return df

@st.cache(allow_output_mutation=True)
def getMergedDataframe(folder_id):
    print("Getting merged df")
    sheet_credentials = getSheetcredentials()
    drive_credentials = getDrivecredentials()

    drive = build('drive', 'v3', credentials=drive_credentials)
    results = drive.files().list(q = "'" + folder_id + "' in parents and mimeType= 'application/vnd.google-apps.spreadsheet'").execute()
    items = results.get('files', [])
    dflst = []
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))
        df = getFormatedDf(getDataFrame(sheet_credentials,item['id']))
        dflst.append(df)

    combined_df = pd.concat(dflst)

    combined_df["price"] = pd.to_numeric(combined_df["price"])
    return combined_df

def getFormatedDf(dfIn):
    print("Formating DF")
    dfOut = dfIn[['Bedrooms','price','Type','extract_time','PostalCode','AddressText']]
    dfOut["fsa"] = dfOut["PostalCode"].str[0:3]
    dfOut["city"] = dfOut["AddressText"].str.split(" ").str[-3].str.split("|").str[-1].str.replace('(', '').\
        str.replace(')','').str.replace(',', '')

    return dfOut[['Bedrooms','price','Type','extract_time','fsa','city']]

def display_map(df):
    print("render map")
    print(st.session_state["selected_fsa"])
    map = folium.Map(location=[45.51732805507313, -73.63700075840842], tiles='CartoDB positron',zoom_control=False,
               scrollWheelZoom=False,
               dragging=False)


    df = df.reset_index()
    cities = gpd.read_file('geoJson/montreal.geojson')


    main_mp = folium.Choropleth(
        geo_data=cities,
        data=df,
        columns=('fsa', 'roi'),
        key_on='feature.properties.postal-fsa',
        fill_color="YlGn",
        line_opacity=0.8,
        highlight=True,
        opacity=0.5,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        uirevision='constant',
        legend_name="ROI Ratio",
        name="All cities",

    )

    main_mp.geojson.add_child(
        folium.features.GeoJsonTooltip(["postal-fsa"])
    )

    df_indexed = df.set_index('fsa')

    for feature in main_mp.geojson.data['features']:
        city_fsa = feature['properties']['postal-fsa']
        feature['properties']['city_name'] = 'City: ' + '{:}'.format(df_indexed.loc[city_fsa, 'city']) if city_fsa in list(df_indexed.index) else ''
        feature['properties']['roi'] = 'ROI: ' + '{:}'.format(df_indexed.loc[city_fsa, 'roi']) if city_fsa in list(df_indexed.index) else ''
        feature['properties']['sale count'] = 'Sale count: ' + '{:}'.format(df_indexed.loc[city_fsa, 'total_sale_count']) if city_fsa in list(df_indexed.index) else ''
        feature['properties']['rent count'] = 'Rent count: ' + '{:}'.format(df_indexed.loc[city_fsa, 'total_rent_count']) if city_fsa in list(df_indexed.index) else ''


    main_mp.geojson.add_child(
        folium.features.GeoJsonTooltip(['city_name','roi','sale count','rent count'], labels=False)
    )

    main_mp.add_to(map)

    # if st.session_state["selected_fsa"] != "" :
    #     folium.Choropleth(
    #         geo_data=cities[cities['name'] == st.session_state["selected_fsa"]],
    #         line_opacity=0.8,
    #         highlight=True,
    #         opacity=0.5,
    #         margin={"r": 0, "t": 0, "l": 0, "b": 0},
    #         uirevision='constant',
    #         name="Selected cities",
    #
    #     ).add_to(map)

    #folium.LayerControl().add_to(map)

    st_map = st_folium(map, width=700, height=450)

    if st_map['last_active_drawing']:
        state_name = st_map['last_active_drawing']['properties']['city_name']
        state_fsa = st_map['last_active_drawing']['properties']['name']

        st.session_state["selected_city"] =  str(state_name).replace('City:','')
        st.session_state["selected_fsa"] = state_fsa

def getROILatest(sale_df, rent_df):
    sale_summery = sale_df.groupby(["fsa",'city']).agg(['mean', 'count'])["price"]
    rent_summary = rent_df.groupby(["fsa",'city']).agg(['mean', 'count'])["price"]


    roi_df = sale_summery.merge(rent_summary, left_on=['fsa','city'], right_on=['fsa','city'])

    roi_df['roi'] = ((roi_df['mean_y'] * 12)/roi_df['mean_x']) * 100
    roi_df = roi_df.rename(columns={"mean_x": "sale_price", "count_x": "total_sale_count", "mean_y": "rent_price",
                                    "count_y": "total_rent_count"})
    return roi_df

def getLatestMonth(in_df):
    return in_df[in_df["extract_time"] == in_df["extract_time"].max()]

def main():
    print("starting app")
    sale_folderid = "14-vUH394CZ9BbjdbjKEHHcXbFxcHV--l"
    rent_folderid = "1xXUgEae8hpe1IQt8mye5lkaAIL4_ZKyO"


    if "selected_city" not in st.session_state:
        st.session_state["selected_city"] = ""

    if "selected_fsa" not in st.session_state:
        st.session_state["selected_fsa"] = ""

    sale_og_Df = getMergedDataframe(sale_folderid)
    rent_og_Df = getMergedDataframe(rent_folderid)

    sale_latest = getLatestMonth(sale_og_Df)
    rent_latest = getLatestMonth(rent_og_Df)

    ########UI############
    #st.set_page_config(page_title = "Property finder",layout="wide")

    st.title("Real Estate Analytics")
    st.subheader("Find the best area to invest money in Montreal based on the return of investment(ROI)")

    min_price, max_price = st.select_slider(
        'Select the price range',
        options=[x for x in range(200000,1000000,5000)],
        value=(300000, 500000))

    st.write('You selected sale price between', min_price, 'and', max_price)



    sale_latest = sale_latest[(sale_latest["price"] > min_price) & (sale_latest["price"] < max_price)]
    rent_latest = rent_latest[rent_latest["Bedrooms"].isin(sale_latest["Bedrooms"].unique())]
    roi_df = getROILatest(sale_latest, rent_latest)

    display_map(roi_df)
    st.caption('Select a town on the map for insight')

    if st.session_state["selected_city"] != "":
        selcted_city_fsa = st.session_state["selected_fsa"]
        selcted_city = st.session_state["selected_city"]

        st.header('You have selected :'+ selcted_city )


        sale_city_df = sale_latest[sale_latest["fsa"]== selcted_city_fsa]
        rent_city_df = rent_latest[rent_latest["fsa"]== selcted_city_fsa]


        sale_summery = sale_city_df.groupby(["Bedrooms","Type"]).agg(['mean', 'count'])["price"]
        rent_summary = rent_city_df.groupby(["Bedrooms","Type"]).agg(['mean', 'count'])["price"]

        roi_df = sale_summery.merge(rent_summary, left_on=["Bedrooms","Type"], right_on=["Bedrooms","Type"])
        roi_df['roi'] =  ((roi_df['mean_y'] * 12)/roi_df['mean_x']) * 100
        roi_df = roi_df.rename(columns={"mean_x": "sale_price", "count_x": "total_sale_count", "mean_y": "rent_price",
                                    "count_y": "total_rent_count"})


        st.plotly_chart(px.histogram(roi_df,hover_data=["total_sale_count"],x=roi_df.index.get_level_values(1) ,y="roi",
                       color=roi_df.index.get_level_values(0), barmode='group',histfunc='avg',
                       height=400,
                       labels={
                             "x": "Property Type",
                             "roi": "ROI",
                             "color": "Number of Bedrooms"
                         },
                       title="ROI by Property Type"
                                     ))

        st.header("Trend Analysis")

        sale_og_Df = sale_og_Df[sale_og_Df["fsa"]== selcted_city_fsa]
        rent_og_Df = rent_og_Df[rent_og_Df["fsa"]== selcted_city_fsa]

        ##########PRICE TREND#########
        sale_trend = sale_og_Df.groupby(["extract_time","Bedrooms","Type"]).mean()["price"]
        rent_trend = rent_og_Df.groupby(["extract_time", "Bedrooms","Type"]).mean()["price"]
        roi_trend = rent_trend/sale_trend


        st.plotly_chart(px.line(sale_trend, x=sale_trend.index.get_level_values(0),
                                y="price", color=sale_trend.index.get_level_values(
                2) + "-" + sale_trend.index.get_level_values(1),
                                labels={
                                    "x": "Date",
                                    "price": "Price",
                                    "color": "Property Type"
                                },
                                title="Sale Price Trends"
                                ))

        st.plotly_chart(px.line(rent_trend, x=rent_trend.index.get_level_values(0),
                                y="price", color=rent_trend.index.get_level_values(
                2) + "-" + rent_trend.index.get_level_values(1),
                                labels={
                                    "x": "Date",
                                    "price": "Rent",
                                    "color": "Property Type"
                                },
                                title="Rent Trends"
                                ))


        st.plotly_chart(px.line(roi_trend, x=roi_trend.index.get_level_values(0),
                                y="price",
                                color=roi_trend.index.get_level_values(2) + "-" + roi_trend.index.get_level_values(
                                    1),
                                labels={
                                    "x": "Date",
                                    "price": "ROI",
                                    "color": "Property Type"
                                },
                                title="ROI Trends"
                                ))








if __name__ == '__main__':
    main()