import streamlit as st
import pandas as pd
from datetime import *
from bokeh.plotting import figure, output_file
from bokeh.io import show
from bokeh.layouts import layout,column,row
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Toggle
from swfd.manage_data import loadPredict
from swfd.load_model import modelPrediction,getCsvData


import altair as alt
from vega_datasets import data

st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")

# menu() Make menu with all options
def menu():

    st.title('Space weather forecast')
    horizon = st.sidebar.selectbox(
        label="Horizonte",
        options=["3", "5", "7",
                 "10", "14", "21","27"],
        index=1,
    )
    today=datetime.now()

    gendate=st.sidebar.date_input("When do the predict start?", min_value =datetime(1949, 1, 1), max_value=today,value=today-(timedelta(days=1)))

    allpredictions=st.sidebar.checkbox("All predictions")
    botonPredecir=st.sidebar.button("Predict")
    
    if botonPredecir:
        showprediction(gendate,int(horizon),allpredictions)
    else:
        st.markdown(
            "Select the date, the horizon and click on the 'Predict' button."
        )

# findprediction(): Find or make the predict
# Stardate the first date that you catch the data
def findprediction(horizon,stardate,allpredictions):
    mean=[]
    std=[]
    predict=[]
    predictions=loadPredict()
    with st.spinner("Making prediction..."):
        if(not allpredictions):
            for nrow in range (len(predictions.index)):
                if stardate == pd.to_datetime(predictions.loc[nrow,"Date"]):

                        mean=predictions.loc[nrow,str('H'+str(horizon))][0] #mean
                        std=predictions.loc[nrow,str('H'+str(horizon))][1] #std


        if  len(mean)==0:
                predict,mean,std=modelPrediction(int(horizon), stardate)

    st.write("Show prediction")
    return predict,mean,std

# showprediction() collect all data and make the graph

def showprediction(gendate,horizon,allpredictions):

    #---------------------------Collect data-------------------
    lookback=int(horizon*6) 
    totaldays=lookback
    startdaterecord =(gendate-(timedelta(days=lookback)))

    enddaterecord=gendate+(timedelta(days=lookback))
    pastdate=[]
    futuredate=[]
    predictdate=[]

    #Collect predict data
    for i in range(0,horizon):
            predictdate.append(gendate+(timedelta(days=i)))
    predict,mean,std=findprediction(horizon,gendate-(timedelta(days=1)),allpredictions)

    #Collect past data
    pastdata=getCsvData(lookback,gendate-(timedelta(days=1)))[::-1] #Desde startdaterecord hasta enddaterecord
    for i in range(0,lookback):
        pastdate.append(startdaterecord+(timedelta(days=i)))

    #Collect future data
    if(enddaterecord >  date.today()):
        enddaterecord=date.today()- (timedelta(days=1))
        futuredata=getCsvData((date.today()-gendate).days,enddaterecord)[::-1]#today-gendate

        for i in range(0,(date.today()-gendate).days):
            futuredate.append(gendate+(timedelta(days=i)))
    else:
        futuredata=getCsvData(lookback,gendate+timedelta(lookback-1))[::-1] #gendate+timedelta(lookback-1) == startdate
        for i in range(lookback,lookback*2):
            futuredate.append(startdaterecord+(timedelta(days=i)))

    #---------------------------------------------------------------
    
    #----------------------------Bokeh------------------------------
    
    #Predict
    q = figure(title='Forecast ',x_axis_label='date',y_axis_label='f10_7', x_axis_type="datetime")
    q.toolbar.autohide = True

    datap = pd.DataFrame({'date': predictdate, 'f10_7': mean})
    allpredict=q.line(x='date', y='f10_7', source=datap, legend_label="Predict", line_width=2,color='red',line_dash="4 4")
    datastd = pd.DataFrame({'date': predictdate, 'y1': mean+std,'y2': mean-std})
    q.varea(x='date', y1='y1', y2='y2', source=datastd,alpha=0.1)

    if(allpredictions):
        for elem in predict:
            elemdf=pd.DataFrame({'date': predictdate, 'f10_7': elem})
            q.line(x='date', y='f10_7', source=elemdf, legend_label="Predict", line_width=2,color='grey',line_dash="4 4",alpha=0.2)
    #Past
    pastframe = pd.DataFrame({'date': pastdate, 'f10_7': pastdata})
    showpastline=q.line(x='date', y='f10_7', source=pastframe, legend_label="all records", line_width=2,color='black',line_dash="4 4")
    showpastsquare=q.square(x='date', y='f10_7', source=pastframe, legend_label="all records", line_width=2,color='black',line_dash="4 4")
    pastboton = Toggle(label="Past", button_type="success", active=True)
    pastboton.js_link('active', showpastline, 'visible')
    pastboton.js_link('active', showpastsquare, 'visible')

    #Future
    if(len(futuredata)>0):
        futureframe = pd.DataFrame({'date': futuredate, 'f10_7': futuredata})
        showfutureline=q.line(x='date', y='f10_7', source=futureframe, legend_label="all records", line_width=2,color='black',line_dash="4 4")
        showfuturesquare=q.square(x='date', y='f10_7', source=futureframe, legend_label="all records", line_width=2,color='black',line_dash="4 4")
        futureboton = Toggle(label="Future", button_type="success", active=True)
        futureboton.js_link('active', showfutureline, 'visible')
        futureboton.js_link('active', showfuturesquare, 'visible')

        layoutex=layout([q], [[pastboton], [futureboton]],sizing_mode="scale_width")
    else:
        layoutex=layout([q], [pastboton],sizing_mode="scale_width")

    st.bokeh_chart(layoutex, use_container_width=True)

    #----------------------------------------------------------Altair---------------------
    

    #pastframe = pd.DataFrame({'date': pastdate, 'f10.7': pastdata})
    
    
    
    #-------------------------------------------------------------------------------------
    brush = alt.selection(type='interval', encodings=['x'])
    base = alt.Chart(pastframe).mark_line().encode(
        x = 'date:T',
        y = 'f10_7:Q',
        tooltip=['date', 'f10_7']
    ).properties(
        width=1200,
        height=400
    )

    
    upper = base.encode(
        alt.X('date:T', scale=alt.Scale(domain=brush))
    )

    lower = base.properties(
        height=60
    ).add_selection(brush)

    
    #st.altair_chart(p, use_container_width=True)
    #datastd = pd.DataFrame({'date': predictdate, 'y1': mean+std,'y2': mean-std})
    line = alt.Chart(datap).mark_line().encode(
        x = 'date:T',
        y = 'f10_7:Q',
        tooltip=['date', 'f10_7']
    ).properties(
        width=1200,
        height=400
    )
    band = alt.Chart(datastd).mark_area(
        opacity=0.5
    ).encode(
        x='date',
        y='y2',
        y2='y1'
    )
    #line+band

    p=alt.vconcat(upper+upper, lower)
    st.altair_chart(p, use_container_width=True)
menu()

