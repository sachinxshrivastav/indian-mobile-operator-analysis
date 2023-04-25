# Importing Libraries
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
import folium
from folium import Choropleth, Circle, Marker
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium



def display_title():
    st.set_page_config(layout="wide")
    st.title('Indian Mobile Operators Analysis')
    st.text('This is a web app to gain insights of Indian Mobile Operators')
    st.text('''The dataset used in the application is a subset of the main dataset with less records, to optimize the application performance.
The data has been collected sourced from Sourced from : https://opencellid.org/ 
    ''')

@st.cache_data
def read_datasets():
    # Reading the Dataset 404
    #df_data_404 = pd.read_csv('data/404.csv')

    # Reading the Dataset 405
    df_data_405 = pd.read_csv('data/405.csv')

    #Readin MCC-MNC Mapping
    df_data_mcc_mnc = pd.read_csv('data/MCC-MNC India.csv')

    # Merging the two Datasets
    #df = pd.concat([df_data_404, df_data_405])
    df = df_data_405

    return df,df_data_mcc_mnc


def display_dataset_preview(df):
    st.header('Getting a glimpse of the dataset')
    st.text(
    """
    Radio: The generation of broadband cellular network technology (Eg. LTE, GSM)

    MCC: Mobile country code.

    MNC: Mobile network code.

    LAC/TAC/NID: Location Area Code

    CID: This is a unique number used to identify each Base transceiver station or sector of BTS

    Longitude:This is a geographic coordinate that specifies the east-west position of a point on the Earth's surface

    Latitude:This is a geographic coordinate that specifies the north–south position of a point on the Earth's surface.

    Range: Approximate area within which the cell could be. (In meters)

    Samples: Number of measures processed to get a particular data point

    Changeable=1: The location is determined by processing samples

    Changeable=0: The location is directly obtained from the telecom firm

    Created: When a particular cell was first added to database (UNIX timestamp)

    Updated: When a particular cell was last seen (UNIX timestamp)

    AverageSignal: To get the positions of cells, OpenCelliD processes measurements from data contributors. 
    Each measurement includes GPS location of device + Scanned cell identifier (MCC-MNC-LAC-CID) + Other device properties (Signal strength). 
    In this process, signal strength of the device is averaged. Most ‘averageSignal’ values are 0 because OpenCelliD simply didn’t receive signal strength values.    
    """)

    st.header('Dataset Stats')
    st.write(df.describe())

    st.header('Top 10 rows of the dataset')
    st.write(df.head(10))


# Data Processing
def data_cleaning(df,df_data_mcc_mnc):
    # Replacing by Radio by Generation for better understanding
    df['radio'] = df['radio'].replace('UMTS', '3G').replace('GSM', '2G').replace('LTE', '4G').replace('CDMA', '3G').replace('NR','5G')

    # As the operator and cicle names are present in a different file, we will make a left join to get all values
    df_merged = pd.merge(df, 
                        df_data_mcc_mnc, 
                        on = ['mcc','mnc'],
                        how ='left')


    # Data Cleaning 
    # Taking only tower values that are supplied by the operators
    df_merged = df_merged[df_merged.changeable_0 == 0]

    # Removing columns that will not be used
    df_merged.drop(['lac', 'range','sample','avgsignal','changeable_1','changeable_0'], axis=1,inplace=True)

    # Removing Rows of Null Values
    df_merged = df_merged[df_merged['operator'].notna()]

    # Merge Operators with different names
    df_merged['operator'] = df_merged['operator'].replace(['Airtel'], 'AirTel')
    df_merged['operator'] = df_merged['operator'].replace(['Airtel (Old TATA DOCOMO)'], 'AirTel')
    df_merged['operator'] = df_merged['operator'].replace(['Reliance (Used for Jio in some area)'], 'Jio')

    # Removing Mobile Networks not used now.
    df_merged = df_merged[df_merged.operator != 'AIRCEL (Not in Use)' ]
    df_merged = df_merged[df_merged.operator != 'Uninor' ]
    df_merged = df_merged[df_merged.operator != 'DOLPHIN' ]
    df_merged = df_merged[df_merged.operator != 'Videocon Datacom' ]
    df_merged = df_merged[df_merged.operator != 'Loop Mobile (Not in Use)' ]

    # Jio has only 4G networks, converting 2G and 3G values to 4G
    df_merged.loc[(df_merged.operator == 'Jio') & (df_merged.radio == '2G'), 'radio'] = '4G'
    df_merged.loc[(df_merged.operator == 'Jio') & (df_merged.radio == '3G'), 'radio'] = '4G'

    # Fixing Circle Values
    df_merged['circle'] = df_merged['circle'].replace(['Karnataka (Bangalore)'], 'Karnataka')
    df_merged['circle'] = df_merged['circle'].replace(['Andhra Pradesh'], 'Andhra Pradesh and Telangana')
    df_merged['circle'] = df_merged['circle'].replace(['Maharashtra'], 'Maharashtra & Goa')
    df_merged['circle'] = df_merged['circle'].replace(['Delhi'], 'Delhi & NCR')
    df_merged['circle'] = df_merged['circle'].replace(['Tamil Nadu (incl. Chennai)'], 'Tamil Nadu')
    df_merged['circle'] = df_merged['circle'].replace(['Tamil Nadu including Chennai'], 'Tamil Nadu')
    df_merged['circle'] = df_merged['circle'].replace(['Chennai'], 'Tamil Nadu')
    df_merged['circle'] = df_merged['circle'].replace(['Uttar Pradesh (West)'], 'Uttar Pradesh (W) & Uttarakhand')
    df_merged['circle'] = df_merged['circle'].replace(['Uttar Pradesh (East)'], 'Uttar Pradesh (E)')
    df_merged['circle'] = df_merged['circle'].replace(['Bihar'], 'Bihar & Jharkhand')
    df_merged['circle'] = df_merged['circle'].replace(['Bihar/Jharkhand'], 'Bihar & Jharkhand')
    df_merged['circle'] = df_merged['circle'].replace(['Madhya Pradesh'], 'Madhya Pradesh & Chhattisgarh')
    df_merged['circle'] = df_merged['circle'].replace(['Madhya Pradesh & Chattishgarh'], 'Madhya Pradesh & Chhattisgarh')
    df_merged['circle'] = df_merged['circle'].replace(['Vodafone Punjab'], 'Punjab')
    df_merged['circle'] = df_merged['circle'].replace(['Kolkata'], 'West Bengal')
    df_merged['circle'] = df_merged['circle'].replace(['Assam'], 'Assam & North East')
    df_merged['circle'] = df_merged['circle'].replace(['North East'], 'Assam & North East')


    # Function to display Quantile
    def get_quantile(circle):
        return df_merged[df_merged.circle == circle][['lat','long']].describe(percentiles=[.01,.05,.1,.25,.5,.9,.95,.99])

    # Funcion to filter rows and update dataframe based on given quantile
    def get_rows_within_quantile(lower,upper,circle):
        df = df_merged[df_merged.circle == circle]
        df = df[ (  df.lat>= df.lat.quantile(lower)  )  &  (  df.lat <= df.lat.quantile(upper)  ) ]
        df = df[ (  df.long>= df.long.quantile(lower)  )  &  (  df.long <= df.long.quantile(upper)  ) ]
        return df


    # Fixing data by using data within a particular quantile 
    df_Karnataka = get_rows_within_quantile(.01,.99,'Karnataka')
    df_Andhra_Pradesh_Telangana = get_rows_within_quantile(.01,.95,'Andhra Pradesh and Telangana')
    df_TamilNadu = get_rows_within_quantile(.01,.99,'Tamil Nadu')
    df_Maharashtra_Goa = get_rows_within_quantile(.01,.99,'Maharashtra & Goa')
    df_Delhi_NCR = get_rows_within_quantile(.01,.99,'Delhi & NCR')
    df_Mumbai = get_rows_within_quantile(.01,.99,'Mumbai')
    df_Kerala = get_rows_within_quantile(.01,.99,'Kerala')
    df_Gujarat = get_rows_within_quantile(.01,.99,'Gujarat')
    df_WestBengal = get_rows_within_quantile(.01,.99,'West Bengal')
    df_MP_CG = get_rows_within_quantile(.01,.99,'Madhya Pradesh & Chhattisgarh')
    df_Rajasthan = get_rows_within_quantile(.01,.99,'Rajasthan')
    df_UpWest_Uttarakhand = get_rows_within_quantile(.01,.99,'Uttar Pradesh (W) & Uttarakhand')
    df_UpEast = get_rows_within_quantile(.01,.99,'Uttar Pradesh (E)')
    df_Punjab = get_rows_within_quantile(.01,.99,'Punjab')
    df_Bihar_Jharkhand = get_rows_within_quantile(.01,.99,'Bihar & Jharkhand')
    df_Haryana = get_rows_within_quantile(.01,.99,'Haryana')
    df_Orissa =  get_rows_within_quantile(.01,.99,'Orissa')
    df_HimachalPradesh = get_rows_within_quantile(.01,.99,'Himachal Pradesh')
    df_Assam_NorthEast = get_rows_within_quantile(.05,.99,'Assam & North East')
    df_Jammu_Kashmir = get_rows_within_quantile(.01,.99,'Jammu & Kashmir')

    # Final Corrected Records Dataframe
    df_corrected = pd.concat([df_Karnataka, df_Andhra_Pradesh_Telangana, df_TamilNadu, df_Maharashtra_Goa, df_Delhi_NCR, df_Mumbai, df_Kerala, df_Gujarat, df_WestBengal, df_MP_CG, df_Rajasthan, df_UpWest_Uttarakhand, df_UpEast, df_Punjab, df_Bihar_Jharkhand, df_Haryana, df_Orissa, df_HimachalPradesh, df_Assam_NorthEast, df_Jammu_Kashmir])
    
    circle_dict = {
    "Karnataka": df_Karnataka, 
    "Andhra Pradesh Telangana":df_Andhra_Pradesh_Telangana,
    "Tamil Nadu":df_TamilNadu,
    "Maharashtra Goa":df_Maharashtra_Goa,
    "Delhi NCR":df_Delhi_NCR,
    "Mumbai":df_Mumbai,
    "Kerala":df_Kerala,
    "Gujarat":df_Gujarat,
    "West Bengal":df_WestBengal,
    "MP & CG":df_MP_CG,
    "Rajasthan":df_Rajasthan,
    "Up West & Uttarakhand":df_UpWest_Uttarakhand,
    "Up East":df_UpEast,
    "Punjab":df_Punjab,
    "Bihar & Jharkhand":df_Bihar_Jharkhand,
    "Haryana":df_Haryana,
    "Orissa":df_Orissa,
    "Himachal Pradesh":df_HimachalPradesh,
    "Assam & NorthEast":df_Assam_NorthEast,
    "Jammu Kashmir":df_Jammu_Kashmir
    }

    return df_corrected,circle_dict


# Visualizations
# Returns Dataframe with Column Name and Respective Count
def draw_charts(df_corrected,circle_dict):

    def value_counts_df(df, col):
        df_new = df.copy()
        df_new = pd.DataFrame(df_new[col].value_counts().reset_index().values, columns=[col, "count"])
        df_new = df_new.sort_index(axis = 0, ascending=True)
        return df_new

    # Finding Tower Count by Operator
    df_towercount_byoperator = value_counts_df(df_corrected, 'operator')


    st.header('Tower Counts and Ratio for Each Operator')
    # Pie Chart
    df = df_towercount_byoperator
    fig_towercount_byoperator = px.pie(df, values='count', names='operator',
                title='Tower Count by Operator', width=1200)
    fig_towercount_byoperator.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_towercount_byoperator)


    # Finding Tower Count by Circle
    df_towercount_circle = value_counts_df(df_corrected, 'circle')
    #   df_towercount_circle


    st.header('Tower Count and Ratio for Each Circle')
    # Pie Chart
    df = df_towercount_circle
    fig_towercount_circle = px.pie(df, values='count', names='circle', title='Tower Count by Circle', width=1200)
    fig_towercount_circle.update_traces(textinfo='percent+label',)
    st.plotly_chart(fig_towercount_circle)


    st.header('Tower Types (2G/3G/4G) count for all Circles')
    # Tower Types Count of All Operators by Circles
    df_radio_count = df_corrected.groupby(["operator","circle","radio"], as_index=False)["cid"].count()


    # Getting the operator List
    df_operators = df_radio_count['operator'].unique()
    selected_operator = st.selectbox('Select operator',df_operators)
    df_tower_count_all_op = df_radio_count[df_radio_count.operator == selected_operator ]
    fig_tower_count_all_op = px.bar( df_tower_count_all_op , x="circle", y="cid", color="radio", title=f'Count of Radio Types in all the circles for {selected_operator}', text="radio", width=1200)
    st.plotly_chart(fig_tower_count_all_op)


    st.header('Tower types and Count by each Circle')
    df_circles = circle_dict.keys()
    #st.text(df_circles)
    
    selected_circle = st.selectbox('Select Circle',df_circles)

    #for key,value in circle_dict.items():
    df_circle_selected = circle_dict[selected_circle]
    df_circle_selected = df_circle_selected.groupby(["operator","circle","radio"], as_index=False)["cid"].count()
    fig_towertypes_bycircle = px.bar( df_circle_selected , x="operator", y="cid", color="radio", title=f'Tower types and Count : {selected_circle}', text="radio",width=1200)
    st.plotly_chart(fig_towertypes_bycircle)




@st.cache_data
def draw_kepler_map(circle_dict):
    st.header('Geo Location of the Towers')
    config = {
    'version': 'v1',
    'config': {
        'mapState': {
            'latitude': 20.5937,
            'longitude': 78.9629,
            'zoom': 5
        }
        
    }
    }

    map = KeplerGl(height=800, config=config ,data=circle_dict)
    keplergl_static(map)




def main():
    # Display Page Title
    display_title() 
    
    # Read Datasets
    df, df_data_mcc_mnc = read_datasets()

    #show dataset preview
    display_dataset_preview(df)

    # Data Cleaning
    df_corrected,circle_dict = data_cleaning(df,df_data_mcc_mnc)

    draw_charts(df_corrected,circle_dict)

    draw_kepler_map(circle_dict)


if __name__ == "__main__":
    main()