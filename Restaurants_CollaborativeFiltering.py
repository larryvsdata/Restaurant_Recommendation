# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 17:20:23 2018

@author: Erman
"""

import numpy as np
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scipy
from scipy.stats.stats import pearsonr
from numpy import corrcoef
import random as rd
import folium

class Restaurant_Rec():
    
    
    def __init__(self):
        self.ratingsDf = pd.read_csv('rating_final.csv')
        self.ratingsDfFiltered=None
        self.geoplacesDf=pd.read_csv('geoplaces2.csv')
        self.hoursDf=pd.read_csv('chefmozhours4.csv')
        self.ratingsPivot=None
        self.likedPlaces=None
        self.recommendedPlaces=[]
        self.distinctUsers=list(set(self.ratingsDf['userID']))
        self.distinctPlaces=list(set(self.ratingsDf['placeID']))
        self.placesForSuggestion=[]
        self.placeCountPerLiked=5
        self.packedDigits=3
        self.dayDesired=None
        self.timeDesired=None
        self.zipDesired=None
        
    def packNumbers(self,numberList):
        
        endString=""
        
        for num in numberList:
            endString+=str(num)
            
        return int(endString)
    
    def stripTime1(self,ts):
        tsList=ts[:-1].split(":")
        return float(tsList[0])+float(tsList[1])/100.0
    def stripTime2(self,ts):
        tsList=ts.split(":")
        return float(tsList[0])+float(tsList[1])/100.0
    
    def stripTimeRange(self,tsRange):
        tsRange=tsRange.split(";")
        
        tsRange=list(map(lambda x: x.split("-"),tsRange))[:-1]
        try:
            tsRange=list(map(lambda x: [self.stripTime2(x[0]),self.stripTime2(x[1])],tsRange))
        except:
#            print("Error: ",tsRange)
            tsRange=[[self.stripTime1(tsRange[0][0]),self.stripTime1(tsRange[0][1])]]
                
#        print(tsRange)
        return tsRange
    
    def checkRange(self,ts,tsRange):
        ts=self.stripTime1(ts)
        tsRange=self.stripTimeRange(tsRange)
        
        for rg in tsRange:
            if (ts>=rg[0] and ts<=rg[1]):
                return True
            
        return False
        
    def checkDay(self,dayName,daysString):
        return (dayName in daysString)
    
    def filterDay(self,dayName):
#        print(self.hoursDf[self.hoursDf["days"].apply(lambda x: self.checkDay(dayName,x))])
#        print(list(self.hoursDf[self.hoursDf["days"].apply(lambda x: self.checkDay(dayName,x))]["placeID"]))
        placeIdList=list(self.hoursDf[self.hoursDf["days"].apply(lambda x: self.checkDay(dayName,x))]["placeID"])
        filteredLength=len(self.ratingsDf[self.ratingsDf["placeID"].isin(placeIdList)])
#        print(self.ratingsDf[self.ratingsDf["placeID"].isin(idList)])
        self.ratingsDf=self.ratingsDf[self.ratingsDf["placeID"].isin(placeIdList)].copy()
#        print("Original length: ",len(self.ratingsDf))
        print("filtered length: ",filteredLength)
    def filterTime(self,ts):
        placeIdList=list(self.hoursDf[self.hoursDf["hours"].apply(lambda x: self.checkRange(ts,x))]["placeID"])
#        print(placeIdList)
#        print(len(placeIdList))
        self.ratingsDf=self.ratingsDf[self.ratingsDf["placeID"].isin(placeIdList)].copy()
#        print("New length of the df : ",len(self.ratingsDf))
        


    

    
        
    
    def pack3Columns(self):
        packedColumns=[]
        for ii in range(len(self.ratingsDf)):
            try:
                packedColumns.append(self.packNumbers([self.ratingsDf["rating"][ii],self.ratingsDf["food_rating"][ii],self.ratingsDf["service_rating"][ii]]))
            except:
                print("Error",ii)
        self.ratingsDf['packed_rating']=packedColumns
        
    def getRatingsPivot(self):
        self.ratingsPivot=self.ratingsDf.pivot_table(index=['userID'],columns=['placeID'],values=['packed_rating'])
        self.ratingsPivot.columns = list(map(lambda x: str(x[1]) ,self.ratingsPivot.columns))
    def getLikedPlaces(self,placesList):
        self.likedPlaces=placesList
        
    def getRandomPlaces(self,numberOfPlaces):
        
        return rd.sample(self.distinctPlaces,numberOfPlaces)
    
    def castIntoArray(self,num):
        ratings=[]
#        print("Number ",num)
        for ii in range(self.packedDigits):
            ratings.insert(0,num%10)
            num//=10

            
        return ratings
    
    def calculateSingleCorrelation(self,place1,place2):
        place1=str(place1)
        place2=str(place2)
        
        array1=[]
        array2=[]
        
        for ii in range(len(self.ratingsPivot)):
            if not pd.isnull(self.ratingsPivot.iloc[ii].loc[place2]) and not pd.isnull(self.ratingsPivot.iloc[ii].loc[place1]) :
                array1+=self.castIntoArray(self.ratingsPivot.iloc[ii].loc[place1])
                array2+=self.castIntoArray(self.ratingsPivot.iloc[ii].loc[place2])
#                print(self.ratingsPivot.iloc[ii].loc[place2],array1)
        
        if array1==[] or array2==[]:
            return 0.0 
        elif pd.isnull(corrcoef(array1,array2)[0,1]):
            return 0.0
        else:
            return corrcoef(array1,array2)[0,1] 
            
            
    def pilot(self):
        
        for place1 in self.distinctPlaces:
            for place2 in self.distinctPlaces:
                print(self.calculateSingleCorrelation(place1,place2))
                
    def getRecommendedPlaces(self):
        placeList=[]
        correlations=[]
        
        for likedPlace in self.likedPlaces:
            
            for place in self.distinctPlaces:
                if place !=likedPlace:
                    placeList.append(place)
                    correlations.append(self.calculateSingleCorrelation(place,likedPlace))
            
            selectedPlacesDf=pd.DataFrame({"Places":placeList,"Correlations":correlations})
            selectedPlacesDf=selectedPlacesDf.sort_values(by=["Correlations"], ascending=False)
            
#            print("Liked place: ",likedPlace)
            self.recommendedPlaces+=list(selectedPlacesDf["Places"])[:self.placeCountPerLiked]
            print(list(selectedPlacesDf["Places"])[:self.placeCountPerLiked])
            print(list(selectedPlacesDf["Correlations"])[:self.placeCountPerLiked])
            
        self.recommendedPlaces=list(set(self.recommendedPlaces))
        
        
    def getDayDesired(self,day):
        self.dayDesired=day
    def getTimeDesired(self,ts):
        self.timeDesired=ts
        
    def getDesiredsAndFilter(self,ts,day):
        self.getDayDesired(day)
        self.getTimeDesired(ts)
        
        self.filterDay(day)
        self.filterTime(ts)
        self.ratingsDf=self.ratingsDf.reset_index(drop=True)
        self.distinctUsers=list(set(self.ratingsDf['userID']))
        self.distinctPlaces=list(set(self.ratingsDf['placeID']))
        
        
    def foliumMap(self):
        
        lattitudes=[]
        longitudes=[]
        descriptions=[]
        self.geoplacesDf.set_index('placeID',inplace=True)
        
        for recommended in self.recommendedPlaces:
            lattitudes.append(self.geoplacesDf.loc[recommended]['latitude'])
            longitudes.append(self.geoplacesDf.loc[recommended]['longitude'])
            descriptions.append(self.geoplacesDf.loc[recommended]['name']+", "
                                +"Alcohol: "+self.geoplacesDf.loc[recommended]['alcohol']+
                                ", Smoking: "+self.geoplacesDf.loc[recommended]['smoking_area']+
                                ", Dress Code : "+self.geoplacesDf.loc[recommended]['dress_code'])
        data = pd.DataFrame({
        'lon':lattitudes,
        'lat':longitudes,
        'desc':descriptions
        })
        print(data)
         
        # Make an empty map
        m = folium.Map(location=[data.iloc[0]['lon'], data.iloc[0]['lat']], tiles="Mapbox Bright", zoom_start=9)
         
        # I can add marker one by one on the map
        for i in range(0,len(data)):
            folium.Marker([data.iloc[i]['lon'], data.iloc[i]['lat']], popup=data.iloc[i]['desc']).add_to(m)
         
        # Save it as html
        m.save('Recommended_Restaurants.html')
        

    
      
        
        
if __name__ == '__main__':
    
    RRev=Restaurant_Rec()
    
    dayName="Sun"
    timeSt="17:00"
    RRev.getDesiredsAndFilter(timeSt,dayName)
    
    RRev. pack3Columns()
    
    RRev.getRatingsPivot()
    likedPlaces=RRev.getRandomPlaces(5)
    RRev.getLikedPlaces(likedPlaces)
    RRev.getRecommendedPlaces()
    RRev.foliumMap()
   
    