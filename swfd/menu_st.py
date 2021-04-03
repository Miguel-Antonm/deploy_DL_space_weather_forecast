import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import *
from load_model import *
import csv
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import layout
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Toggle
from bokeh.models.tools import HoverTool

from web_scraping import *

st.set_option('deprecation.showPyplotGlobalUse', False)

def getAllCsvData():
    pathfoldercsv=getInfo("csvdirectory") #Obtiene del txt el path del csv
    csvname="sfuData.csv" 
    datalist=[]
    datelist=[]
    date=(datetime.now()-timedelta(1)) 
    date=date.strftime("%Y-%m-%d")
    #asdasdasd
    try:       
        with open(str(pathfoldercsv)+str(csvname)) as csv_file:
            for row in list(csv.reader(csv_file, delimiter=',')):
            	if(float(row[1])!=-1):

            		datalist.append(float(row[1]))
            	else:
            		datalist.append(None)
            	datelist.append( datetime.strptime(row[0], '%Y-%m-%d')) #csvdaybefore=datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)

    finally:
        csv_file.close()
    return datelist,datalist

def menu():

	st.title('Space weather forecast')
	horizon = st.sidebar.selectbox(
	    label="Horizonte",
	    options=["3", "5", "7",
	             "10", "14", "21","27"],
	    index=1,
	)
	#-------------------------------A probar test Dates----------------------------------------
	today=datetime.now()

	gendate=st.sidebar.date_input("When do the predict start?", min_value =datetime(1949, 1, 1), max_value=today-(timedelta(days=1)),value=today-(timedelta(days=1)))


	botonPredecir=st.sidebar.button("Predecir")
	botonprueba=st.sidebar.button("Prueba")
	#------------------------------------------------------------------------------
	if botonPredecir:
		st.write("-------------------Info de predicion---------------------------")
		st.write("Start predict",gendate)
		st.write("Horizon: ",horizon) 
		st.write(type(gendate))
		#------------------------------Añadir a otra funcion--------------------------
		pathfoldercsv=getInfo("csvdirectory") + "predictionData"+str(horizon)+".csv" 
		data = pd.read_csv(pathfoldercsv)
		data.columns=['date','mean','std']
		data_filter = data[data['date'] == gendate.strftime("%Y-%m-%d")]
		

		if(not data_filter.empty):
			st.write(data_filter)
			mean=(data_filter['mean'])
			std=(data_filter['std'])
		else:
			st.write("empty")
			predict,mean,std=modelPrediction(int(horizon),707.6, gendate)
		#----------------------------------------------------------------------
		st.write(mean,std)

		#showModel2(int(horizon), mean,std,gendate)
	else:
	    st.markdown(
	        "Selecciona la fecha, el horizonte y pulsa en "
	        "el botón 'Predecir'."
	    )
	if botonprueba:
		prueba(int(horizon),gendate)

def prueba(horizon, gendate):

    meanlist=[77.4848,77.6777,77.9052,77.6682,78.0481]
    stdlist=[3.8418,3.7804,3.3660,3.8424,3.5055]
    mean=np.array(meanlist)
    std=np.array(stdlist)
    predict,mean,std=modelPrediction(int(horizon),707.6, gendate)
    st.write((mean),(std))

    totaldays=date.today()-date(1949,1,3)
    startdaterecord =datetime(1949, 1, 3)
    #gendate=datetime.now()
    enddaterecord=datetime.now()-(timedelta(days=1))
    #datarecord=getsfurecord(enddaterecord,startdaterecord)
    #print(getCsvData(15,datetest))

    datadate,datarecord=getAllCsvData()
    TOOLTIPS = [
    ('index', "$index"),
    ("f10.7", "$y"),
    ("date", "$x")
    ]
    hover = HoverTool(
                  formatters={'date': 'datetime'})
    datelist=[]
    for i in range(0,horizon):
    	datelist.append(datetime.now()+(timedelta(days=i)))
    #datelist=np.array(datelist, dtype=np.datetime64)
    #output_file("patch.html")
    #st.write(type(gendate),type(datelist[0]),type(datadate[0]),type(date.today()))
    q = figure(title='Forecast ',x_axis_label='date',y_axis_label='f10.7', x_axis_type="datetime")#,x_range=(datetime.now()-(timedelta(days=20)), datetime.now()+(timedelta(days=5))),y_range=[0,120])
    """q.add_tools(HoverTool(
                tooltips=[
                    ( 'date',   '$x'            ),
                    ('f10.7','$y'),
                ],
            
                formatters={
                    'date'      : 'datetime', # use 'datetime' formatter for 'date' field
                                              # use default 'numeral' formatter for other fields
                },
            
                # display a tooltip whenever the cursor is vertically in line with a glyph
                mode='vline'
                ))"""
    q.toolbar.autohide = True


    #sourcedata = ColumnDataSource(data=dict(x=datadate, y=datarecord))
    data = pd.DataFrame({'date': datadate, 'f10.7': datarecord})
    #q.line(x='date', y='f10.7', source=data, legend_label="all records", line_width=2,color='black',line_dash="4 4")
    allrecords=q.line(x='date', y='f10.7', source=data, legend_label="all records", line_width=2,color='black',line_dash="4 4")
    #allrecords=q.line(datadate, datarecord, legend_label="all records", line_width=2,color='black',line_dash="4 4")
    toggle1 = Toggle(label="Green Box", button_type="success", active=True)
    toggle1.js_link('active', allrecords, 'visible')
    
    q.varea(x=datelist,y1=mean+std,y2=mean-std,alpha=0.5)
    #sourcemean = ColumnDataSource(data=dict(x=fechalista, y=mean))
    #q.line(datelist, mean, legend_label="predict", line_width=2,color='red')
    predict = pd.DataFrame({'date': datelist, 'f10.7': mean})
    q.line(x='date', y='f10.7', source=predict, legend_label="predict")
    q.circle(x='date', y='f10.7', source=predict, legend_label="predict", fill_color="red", line_color="red", size=6)

    layoutex=layout([q], [toggle1])
    st.bokeh_chart(layoutex, use_container_width=True)
menu()

