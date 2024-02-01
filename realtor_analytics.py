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

def getMergedDataframe(folder_id):
    print("Getting merged df")
    sheet_credentials = getSheetcredentials()
    drive_credentials = getDrivecredentials()

    drive = build('drive', 'v3', credentials=drive_credentials)
    results = drive.files().list(q = "'" + folder_id + "' in parents and mimeType= 'application/vnd.google-apps.spreadsheet'").execute()
    items = results.get('files', [])
    dflst = []
    for item in items[:5]:
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
    #dfOut["city"] = dfOut["AddressText"].str.split(" ").str[-3].str.split("|").str[-1].str.replace('(', '').\
    #    str.replace(')','').str.replace(',', '')

    return dfOut[['Bedrooms','price','Type','extract_time','fsa']]


def getDetails(df_indexed,key,output):
    try:
       result = df_indexed.loc[key, output]


       if isinstance(result, pd.Series):
            # If it's a list, join the elements into a single string
            out = result.unique()[0]
       else:
            # If it's a string, keep it as is
            out = str(result)
    except KeyError:
        out = ""

    return out

def display_map(df,option):
    print("render map")
    print(st.session_state["selected_fsa"])
    map = folium.Map(location=[45.51732805507313, -73.63700075840842], tiles='CartoDB positron',zoom_control=False,
               scrollWheelZoom=False,
               dragging=False)


    cities = gpd.read_file('geoJson/montreal.geojson')


    main_mp = folium.Choropleth(
        geo_data=cities,
        data=df,
        columns=('fsa',option),
        key_on='feature.properties.postal-fsa',
        fill_color="YlGn",
        line_opacity=0.5,
        highlight=True,
        opacity=0.2,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        uirevision='constant',
        legend_name="sale_price",
        name="All cities",

    )

    main_mp.geojson.add_child(
        folium.features.GeoJsonTooltip(["postal-fsa"])
    )

    df_indexed = df.set_index('fsa')

    for feature in main_mp.geojson.data['features']:
         city_fsa = feature['properties']['postal-fsa']

         feature['properties']['name'] = 'City: ' + '{:}'.format(city_fsa)
         feature['properties']['sale_price'] = 'Avg sale price: ' + '{:}'.format(getDetails(df_indexed,city_fsa,'sale_price'))
         feature['properties']['rent'] = 'Avg Rent : ' + '{:}'.format(getDetails(df_indexed, city_fsa, 'rent_price'))
         feature['properties']['no_of_sale'] = 'NUmber of properties-sale : ' + '{:}'.format(getDetails(df_indexed, city_fsa, 'no_of_sale'))
         feature['properties']['no_of_rent'] = 'NUmber of properties-rent : ' + '{:}'.format(
             getDetails(df_indexed, city_fsa, 'no_of_rent'))


    main_mp.geojson.add_child(
        folium.features.GeoJsonTooltip(['name','sale_price','rent','no_of_sale','no_of_rent'], labels=False)
    )

    main_mp.add_to(map)

    if st.session_state["selected_fsa"] != "" :
        folium.Choropleth(
            geo_data=cities[cities['postal-fsa'] == st.session_state["selected_fsa"]],
            line_opacity=0.8,
            highlight=True,
            opacity=0.5,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            uirevision='constant',
            name="Selected cities",

        ).add_to(map)

    folium.LayerControl().add_to(map)

    st_map = st_folium(map, width=700, height=450)

    if st_map['last_active_drawing']:
        state_fsa = st_map['last_active_drawing']['properties']['postal-fsa']
        st.session_state["selected_fsa"] = state_fsa

def getGroupedData(df):
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])

    df['Bedrooms'] = pd.to_numeric(df['Bedrooms'], errors='coerce')
    df = df.dropna(subset=['Bedrooms'])

    df_summery = df.groupby(["fsa", 'Bedrooms'])["price"].agg(['mean', 'count'])

    return df_summery

def main():
    print("starting app")
    sale_folderid = "14-vUH394CZ9BbjdbjKEHHcXbFxcHV--l"
    rent_folderid = "1xXUgEae8hpe1IQt8mye5lkaAIL4_ZKyO"

    if "selected_fsa" not in st.session_state:
        st.session_state["selected_fsa"] = ""

    sale_og_Df = getMergedDataframe(sale_folderid)
    rent_og_Df = getMergedDataframe(rent_folderid)

    st.title("Real Estate Analytics")
    st.subheader("Find the best area to invest money in Montreal based on the return of investment(ROI)")

    min_price, max_price = st.select_slider(
        'Select the price range',
        options=[x for x in range(200000,1000000,5000)],
        value=(300000, 500000))

    st.write('You selected sale price between', min_price, 'and', max_price)

    sale_latest = sale_og_Df[(sale_og_Df["price"] > min_price) & (sale_og_Df["price"] < max_price)]
    rent_latest = rent_og_Df[rent_og_Df["Bedrooms"].isin(sale_latest["Bedrooms"].unique())]

    rent_aggregate = getGroupedData(rent_latest)
    sale_aggregate = getGroupedData(sale_latest)

    merged_dataframe = pd.merge(sale_aggregate, rent_aggregate, on=["fsa", 'Bedrooms'], how='inner').reset_index()

    merged_dataframe = merged_dataframe.rename(columns={'mean_x': 'sale_price', 'count_x': 'no_of_sale','mean_y':
        'rent_price', 'count_y': 'no_of_rent'})

    merged_dataframe['rent_ratio'] = merged_dataframe['rent_price']/merged_dataframe['sale_price']



    map_option = st.selectbox("select map",['sale_price','rent_price','rent_ratio'])
    bedroom_option = st.selectbox("Number of bedrooms", list(merged_dataframe['Bedrooms'].unique()))

    st.caption('Select a town on the map for insight')
    display_map(merged_dataframe[merged_dataframe['Bedrooms'] == bedroom_option],map_option)


    if st.session_state["selected_fsa"] != "":
        selcted_city_fsa = st.session_state["selected_fsa"]

        st.header('You have selected :'+ selcted_city_fsa )

        st.dataframe(merged_dataframe[merged_dataframe['fsa'] == selcted_city_fsa])

        st.header("Trend Analysis")
        st.caption('Select the group key')

        options = st.multiselect(
            'Select group:',
            ['Type', 'Bedrooms'])

        if len(options) > 1 :
            grp_str = 'Type-Bedrooms'
        else :
            grp_str = options[0]


        sale_og_Df = sale_og_Df[sale_og_Df["fsa"]== selcted_city_fsa]
        sale_og_Df['Type-Bedrooms'] = sale_og_Df['Type'] + '-' + sale_og_Df['Bedrooms']
        rent_og_Df = rent_og_Df[rent_og_Df["fsa"]== selcted_city_fsa]
        rent_og_Df['Type-Bedrooms'] = rent_og_Df['Type'] + '-' + rent_og_Df['Bedrooms']

        ##########PRICE TREND#########
        tab1, tab2, tab3 = st.tabs(["Sale Price", "Rent", "Return of Investment"])



        sale_trend = sale_og_Df.groupby(['extract_time',grp_str])["price"].mean()
        sale_trend = sale_trend.reset_index()
        rent_trend = rent_og_Df.groupby(['extract_time',grp_str])["price"].mean()
        rent_trend = rent_trend.reset_index()


        rent_ration_df = pd.merge(sale_trend,rent_trend,on=['extract_time',grp_str],how='inner').reset_index()
        rent_ration_df = rent_ration_df.rename(columns={'price_x': 'sale_price', 'price_y': 'rent_price'})
        rent_ration_df['ratio'] = rent_ration_df['rent_price']/rent_ration_df['sale_price']



        with tab1:
           st.header("Sale Price")
           st.plotly_chart(px.line(sale_trend, x='extract_time',
                        y="price",color=grp_str
                        ))

        with tab2:
           st.header("Rent")
           st.plotly_chart(px.line(rent_trend, x='extract_time',
                        y="price",color=grp_str
                        ))

        with tab3:
           st.header("Ratio")
           st.plotly_chart(px.line(rent_ration_df, x='extract_time',
                        y="ratio",color=grp_str
                        ))



if __name__ == '__main__':
    main()
