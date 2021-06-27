import streamlit as st
import pandas as pd

from datetime import *

from swfd.manage_data import loadPredict,infoDatesPredicts
from swfd.load_model import modelPrediction,getCsvData

from swfd.resources import getInfo
import base64

import altair as alt

import numpy as np
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")

#Colores oscuros
#colorpast="#3C21FF"
#colorpredict="#7E26FF"
#colorfuture="#33AFFF"
#colorruns="#BFE3F9"
#colorstd='#5117A5'

colorpast="#F39C12"
colorpredict="#A93226"
colorfuture="#2874A6"
colorruns="#BFC9CA"
colorstd='#F5B7B1'

backgroundchart='white'

#Colores manual
daycolorsnotselected="grey"
daycolorselected="#73b9c7:N"
schemepredictcolor="blues"
schemestdcolor="blues"
valuesfucolor="#F39C12"
valuesfucolorselected="#F39C12"


# menu() Make menu with all options

def menu():

    st.sidebar.title('Menu')
    botonMenuDownload = st.sidebar.selectbox(
        label="Select menu",
        options=["Predict","Download"],
        index=0,

    )  
    
    if botonMenuDownload=="Download":
        st.title('Space weather forecast: Download predicts')
        menuDownload()
    else:
        st.title('Space weather forecast: Make predicts')
        st.sidebar.title('Type')
        predicttype = st.sidebar.selectbox(
            label="Type",
            options=["Manual","Static"],
            index=0,

        )
        if(predicttype=="Manual"):
            menuManual()

        if(predicttype=="Static"):
            st.sidebar.title('Options ')
            horizon = st.sidebar.selectbox(
                label="Horizonte",
                options=["3", "5", "7",
                         "10", "14", "21","27"],
                index=1,
            )
            today=datetime.now()

            gendate=st.sidebar.date_input("When do the predict start?", min_value =datetime(1950, 1, 1), max_value=today,value=today-(timedelta(days=1)))

            allpredictions=st.sidebar.checkbox("All predictions")
            botonPredecir=st.sidebar.button("Predict")
            if botonPredecir:
                    showprediction(gendate,int(horizon),allpredictions)
            else:
                    st.markdown(
                        "Select the date, the horizon and click on the 'Predict' button."
                    )
# downloadSfu() return the link to download f10.7  

def downloadSfu():
    try:
        path=getInfo("csvdirectory")+"sfuData.csv"
        allsfudata = pd.read_csv(path,header=None)
        allsfudata = allsfudata.to_csv(index=False)
        b64 = base64.b64encode(allsfudata.encode()).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="extract.xlsx">Download csv Sfu</a>'
    except:
        st.error("An error ocurred, please try later")
        return ""

# downloadSfu() return the link to download predicts selected 

def downloadPredicts(past,future):

    path=getInfo("csvdirectory")+"predictionData.csv"
    allpredictdata = loadPredict()
    reqd_Indexpast = allpredictdata[allpredictdata['Date']==past].index.tolist()
    reqd_Indexfuture = allpredictdata[allpredictdata['Date']==future].index.tolist()
    allpredictdata=allpredictdata.iloc [reqd_Indexfuture[0]:reqd_Indexpast[0]+1, :]
    st.write(allpredictdata)
    allpredictdata = allpredictdata.to_csv(index=False)

    b64 = base64.b64encode(allpredictdata.encode()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="extract.xlsx">Download csv predicts </a>' 

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

# showprediction() collect all data and make the graph in a specific day

def showprediction(gendate,horizon,allpredictions):

    #---------------------------    Collect data    ---------------------------
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
    try:      
        predict,mean,std=findprediction(horizon,gendate-(timedelta(days=1)),allpredictions)
        datap = pd.DataFrame({'date': predictdate, 'f10_7': mean})
        datastd = pd.DataFrame({'date': predictdate, 'y1': mean+std,'y2': mean-std})

        #Collect past data
        pastdata=getCsvData(lookback,gendate-(timedelta(days=1)))[::-1] #Desde startdaterecord hasta enddaterecord
        for i in range(0,lookback):
            pastdate.append(startdaterecord+(timedelta(days=i)))
        pastframe = pd.DataFrame({'date': pastdate, 'f10_7': pastdata})

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



        
        #---------------------------    Build graph    ---------------------------


        brush = alt.selection(type='interval', encodings=['x'])

        datapredict =alt.Chart(datap).mark_line(color='coral', point={
              "filled": False,
              "fill": "white",
               "size":50,
            } ).encode(
            x=alt.X('date', axis=alt.Axis(title="Date")),
            y=alt.Y('f10_7', axis=alt.Axis(title="Sfu"),scale=alt.Scale(domain=[min(mean)-10, max(mean)+10])),
            color=alt.Color('variable:N',scale=alt.Scale(
                    range=[colorpast, colorpredict, colorfuture,colorruns],
                    domain=["past", "predict", "future","runs"])),
            tooltip=['date', 'f10_7',"variable:N"],
        ).properties(
                        width=1600,
                        height=600,
                        title=str('Prediction H' + str(horizon)),
        ).transform_fold(
            fold=['predict'], 
            as_=['variable', "value"]
        ).add_selection(alt.selection_interval(bind='scales', encodings=['y']))


        datapast =alt.Chart(pastframe).mark_line(point=True).encode(
            x='date',
            y='f10_7',
            color='variable:N',
            tooltip=['date', 'f10_7',"variable:N"],
        ).transform_fold(
            fold=['past'], 
            as_=['variable', 'value']
        )

        std = alt.Chart(datastd).mark_area(
            opacity=0.4, color=colorstd
        ).encode(
            x='date',
            y='y1',
            y2='y2'
        )

        finalgraph=datapredict+datapast+std

        if(allpredictions):
            for elem in predict:
                elemdf=pd.DataFrame({'date': predictdate, 'f10_7': elem})
                run =alt.Chart(elemdf).mark_line(point=True).encode(
                x='date',
                y='f10_7',
                color='variable:N',
                tooltip=['date', 'f10_7',"variable:N"],
                opacity=alt.value(0.1)
                ).transform_fold(
                fold=['runs'], 
                as_=['variable', 'value']
                )
                finalgraph=finalgraph+run

        if(len(futuredata)>0):
            futureframe = pd.DataFrame({'date': futuredate, 'f10_7': futuredata})
            futuredata =alt.Chart(futureframe).mark_line(point=True).encode(
            x='date',
            y='f10_7',
            color='variable:N',
            tooltip=['date', 'f10_7',"variable:N"],
            ).transform_fold(
            fold=['future'], 
            as_=['variable', 'value']
            )
            finalgraph=finalgraph+futuredata

            alldataframe=pd.concat([pastframe, futureframe])
        else:
            alldataframe=pastframe

        #Optional
        alldata =alt.Chart(alldataframe).mark_line(opacity=0.2).encode(
            x='date',
            y='f10_7',
            color='variable:N',
            tooltip=['date', 'f10_7',"variable:N"],
        ).transform_fold(
            fold=['past'], 
            as_=['variable', 'value']
        )


        finalgraph=finalgraph+alldata
        chart = alt.vconcat(background=backgroundchart)
        chart &= finalgraph
        chart

        
        #Show data
        st.subheader('Predict data')
        st.dataframe(datap.T, 2000, 100)
        st.subheader('Record data')
        st.dataframe(alldataframe.T, 2000, 100)

    except:
        st.error("Data is not updated for this day, try another day")

#menuDownload(): Make menu to download data 

def menuDownload():
        st.subheader('Download record f10.7 ')
        st.markdown(DownloadSfu(), unsafe_allow_html=True)

        future,past=infoDatesPredicts()
        if future != None and past !=None:
            st.subheader('Download predicts ')
            csvvalues = st.slider(
                'Select a range of values to predict',
                past.to_pydatetime(), future.to_pydatetime(), (past.to_pydatetime(),future.to_pydatetime()))
            getLinkCsv=st.button("Get Link")
            if getLinkCsv:
                st.write("Values to download")
                st.markdown(downloadPredicts(csvvalues[0],csvvalues[1]), unsafe_allow_html=True)
            

#  menuManual(): Make menu collect all data and make a interactive graph
def menuManual():

    valuehorizon = st.sidebar.selectbox(
            label="Horizonte",
            options=[3, 5, 7,
                     10, 14, 21,27],
            index=1,
        )
    stdboolean=st.sidebar.checkbox("Std")

    #---------------------------    Collect data    ---------------------------
    future,past=infoDatesPredicts()
    if future != None and past !=None:
        delta = future-past
        sfudata=getCsvData(delta.days+1,future)[::-1]
        allloadpredictions=loadPredict()
        allloadpredictions['sfu']=sfudata[::-1]

        horizonpredict=[]
        horizonstd=[]
        for i in range(0,delta.days+1):
                horizonpredict.append(allloadpredictions['H'+str(valuehorizon)][i][0])
                horizonstd.append(allloadpredictions['H'+str(valuehorizon)][i][1])

        final = pd.DataFrame()
        for fila in range(0,(delta.days+1)):
            for h in range(0,valuehorizon):
                final = final.append( { 'date':future +(timedelta(days=h-fila)) , 'id': fila ,'valuepredict':horizonpredict[fila][h],'std+':horizonpredict[fila][h]+horizonstd[fila][h],'std-':horizonpredict[fila][h]-horizonstd[fila][h] }   ,ignore_index=True)
                  
        sfurecord = pd.DataFrame({'date': allloadpredictions['Date'], 'H': horizonpredict,'f10_7':allloadpredictions['sfu']})
        locations = pd.DataFrame({
        'id': range(delta.days+1),
        'daypredict': allloadpredictions['Date'],
        'f10_7': allloadpredictions['sfu']
        })

        final['id'] = final['id'].astype(int)
        data2 = pd.merge(final, locations, on='id')
        
        #---------------------------    Build graph    ---------------------------

        selector = alt.selection_multi(empty='all', fields=['id'])
        
        
        globalbase = alt.Chart(data2).properties(
            width=250,
            height=250,

        ).add_selection(selector)


        

        points = globalbase.mark_point(filled=True, size=200).encode(
            x=alt.X('daypredict', title = 'Date'),
            y=alt.Y('f10_7', axis=alt.Axis(title="Sfu"),scale=alt.Scale(domain=[min(locations['f10_7'])-10, max(locations['f10_7'])+10])),
            tooltip=['daypredict', 'f10_7'],
            color=alt.condition(selector,alt.Color(daycolorselected, legend=None),alt.value(daycolorsnotselected)),
        ).properties(width=1600,height=100)

        timeseries = globalbase.mark_line(point=True,opacity=0.8).encode(
            x=alt.X('date', title = 'Date'),
            y=alt.Y('valuepredict', title = 'Sfu'),
            color=alt.Color('id',scale=alt.Scale(scheme=schemepredictcolor),legend=None),
            tooltip=['date', 'f10_7'],
        ).transform_filter(selector
        ).properties(width=1600,height=400)

        if stdboolean:
            selector2 = alt.selection_single(empty='all', fields=['id'])
            stdbase = alt.Chart(data2).properties(
                width=250,
                height=250,
            ).add_selection(selector2)
            std = stdbase.mark_area().encode(
                    x='date',
                    y='std+',
                    y2='std-',
                    color=alt.Color('id',   scale=alt.Scale(type='log',scheme=schemestdcolor),legend=None),
                    tooltip=['date', 'f10_7'],
                    opacity = alt.value(0.1)
            ).transform_filter(selector)
            timeseries=timeseries+std

        recordchart =alt.Chart(sfurecord).mark_line(point=True,opacity=0.3).encode(
            x='date',
            y='f10_7',
            color=alt.condition(selector, alt.value(valuesfucolor), alt.value(valuesfucolorselected)),
            tooltip=['date', 'f10_7',"variable:N"],
        )
        timeseries=timeseries+recordchart
        (timeseries & points)
        #st.markdown("<font color={daycolorselected}>&#149 Prediction</font> <font color='green'>&#149 Sfu Record</font> <font color={url}>&#149 Day selected</font> <font color={url}>&#149 Day not selected</font> <font color={url}>&#149 Std</font>", unsafe_allow_html=True)
        st.write("Datos SFU: ",sfurecord)
        st.write("Datos prediciones",final)
    #else:
        #Error message?

menu()

