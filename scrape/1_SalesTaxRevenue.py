#!/usr/bin/env python
# coding: utf-8

# # Scrape WA DOR Tax Sales Data

# #### (1) Scrape
# #### (2) Clean and Compile
# #### (3) Export

# #  

# In[2]:


# ----- IMPORT_REQUIREMENTS ----- 

from tqdm import tqdm_notebook as tqdm
from time import sleep
import requests
import lxml.html
import pandas as pd
import re


# In[3]:


# ----- SPECIFY_OUTPUT_LOCATION ----- 

output = '../static/data/'


# ### (1) Scrape

# In[3]:


# ----- Get_County_Codes ----- 

# From the point-and-click county filter on the original website,
# scrape the list of counties
site_query_options = lxml.html.fromstring(requests                                          .get('https://apps.dor.wa.gov/'                                               +'ResearchStats/Content/'                                               +'TaxableRetailSalesLocal/'                                               +'Report.aspx').content)                                    .xpath('//option')
county_codes = []

# This method depends on the explicit reference to the index of the rows
for county_n in range(68,409):
    county_codes.append(site_query_options[county_n].text_content()[0:4])
county_codes.append('Statewide')
print(county_codes[0:5]) # just a snippet of what we've got
print 'Number of Counties: '+ str(len(county_codes))


# In[4]:


# ----- Create_List_of_Year_for_the_UL ----- 

dates_list = [str(year) + str(datetype)
         for year in range(2005,2017)
         for datetype in ['AN','Q1','Q2','Q3','Q4']]
dates_str = ''
for i in dates_list:
    dates_str = dates_str + ',' + str(i)


# In[5]:


# ----- Define_Scrape_Function_for_Sales_Data ----- 

def scrape_sales_data(url):
    geturl = requests.get(url)
    page = lxml.html.fromstring(geturl.content)
    tr_elements = page.xpath('//tr')
    if ("That request does not appear to match any records in the database."               in geturl.text) or ('Runtime Error' in geturl.text):
        df = pd.DataFrame({'col1': [1]})
        return df
    else:
        col=[]
        for t in tr_elements[0]:
            name = t.text_content()
            col.append((name,[]))
        for j in range(1,len(tr_elements)):
            T = tr_elements[j]
            if len(T) != 5:
                break
            i = 0
            for t in T.iterchildren():
                data = t.text_content() 
                col[i][1].append(data)
                i += 1
            Dict = {title:column for (title,column) in col}
            df = pd.DataFrame(Dict)
        string = geturl.text
        newstring_a = re.search('''  Location: <span id="MainContent_lblLoc">'''                                 + '.*' + '<', string).group(0)
        newstring_b = re.sub('''  Location: <span id="MainContent_lblLoc">''',''                                         , newstring_a)
        newstring_c = re.sub('''<''','', newstring_b)
        df['location_name'] = newstring_c
        return df


# In[6]:


# ----- Execute_Scrape ----- 

results = []
i = 0
export_count = 1
for naicstyp in ['2']:
    for county in tqdm(county_codes):
        sleep(2)
        if county=='Statewide':
            location = ''
        else:
            location = '&Location=' + county
        url = str("http://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal"                   + "/Results.aspx?Year=2018Q1,2017Q4"                  + dates_str
                  + "&Code1=11&Code2=99&Sumby=n" \
                  + str(naicstyp) + "&SicNaics=2" + location \
                  + "&Format=HTML&TaxType=45")
        try:
            df = scrape_sales_data(url)
        except: 
            sleep(45)
            df = scrape_sales_data(url)
        checkpoint = '1_' + str(county) + str(i)
        if len(df) == 1:
            results.append(county + ' is Empty')
        else:
            results.append(str(df['location_name'][1]) + str(county))
            df['location_id'] = county
            df['naicstyp'] = str(naicstyp)
            if i == 0:
                salestaxrev = df
            else:
                salestaxrev = salestaxrev.append(df)
            i += 1
            if salestaxrev['location_id'].memory_usage() >= 100000:
                salestaxrev.to_csv(output + 'slices/salestaxrev_'                                    + str(export_count) + '.csv')
                del salestaxrev
                checkpoint = '3_' + str(export_count) + str(i)
                export_count += 1
                i = 0
                checkpoint = ' ---Export---' + str(export_count) + '---'


# In[9]:


# ----- Get_NAICS_Code_Names ----- 
# Get Category Names
tr = lxml.html.fromstring(requests.get('https://www.naics.com/search/').content).xpath('//tr')
# naics table is the first 22 rows, minus the first header row
names = []
codes = []
for row in range(1,21):
    codes.append(tr[row][0].text_content())
    names.append(tr[row][1].text_content())
df = pd.DataFrame(data = {'codes': codes, 'names': names})
# Resolve Ranges (e.g. Retail Trade is '44-45')
df = df.replace({'31-33': '31', '44-45': '44', '48-49':'48'})
appendage = pd.DataFrame(data = {'codes': ['32','33','45','49','99'],                                  'names': ['Manufacturing','Manufacturing','Retail Trade'                                            ,'Transportation and Warehousing','Other Govmt.']})
naics_lookup = df.append(appendage).sort_values(by='codes')
# Convert Codes to Int
naics_lookup['codes'] = naics_lookup['codes'].astype(int)
# Create Groups According to ad hoc Preference
naics_lookup['short_names'] = naics_lookup.names.replace({'Agriculture, Forestry, Fishing and Hunting': 'Ag. and Forestry'                                , 'Transportation and Warehousing': 'Distribution'                                , 'Finance and Insurance':'FIRE'                                , 'Real Estate Rental and Leasing':'FIRE'                                , 'Professional, Scientific, and Technical Services':'Services'
                                , 'Management of Companies and Enterprises':'Services'
                                , 'Administrative and Support and Waste Management and Remediation Services':'Admin Support'\
                                , 'Educational Services':'Education'\
                                , 'Health Care and Social Assistance':'Health Care'\
                                , 'Arts, Entertainment, and Recreation':'Arts and Entertainment'\
                                , 'Accommodation and Food Services': 'Hospitality'\
                                , 'Other Services (except Public Administration)':'Other Private'\
                                , 'Public Administration':'Government'})


# ### (2) Compile and Clean

# In[11]:


# ----- Compile_Slices ----- 

i = 1
for file_n in range(1,export_count):
    file = 'slices/salestaxrev_' + str(file_n) + '.csv'
    temp = pd.read_csv(output + file)
    for var in ['Total Taxable','Units']:
        temp[var] = temp[var].str.replace('$','')
        temp[var] = temp[var].str.replace(',','')
        temp[var] = temp[var].str.replace('D','0')
        temp[var] = temp[var].astype('int64')
    temp['location_name'] = temp['location_name'].str.replace('/span>','')
    if i == 1:
        salestaxrev = temp
        i += 1
    else:
        salestaxrev = pd.concat([salestaxrev,temp])


# In[12]:


# ----- Clean_Compilation ----- 
# Clean County Info
salestaxrev['county'] = salestaxrev['location_name'].str.contains('Unincorporated')
salestaxrev['county_name'] = salestaxrev['location_name'].where(salestaxrev['county'])    .str.replace('Unincorporated ','').ffill()
salestaxrev.drop(columns=['county','Unnamed: 0'],inplace=True)
# Add a State Column (Feels orderly. And it may be useful later)
salestaxrev['state'] = 'WA'
# Distinguish Between Quarterly and Annual
salestaxrev['datetyp'] = salestaxrev['Year'].replace(regex={'.* Quarter .':'Q'                                                            ,'.* Annual*.*': 'A'})
# Format Dates as Dates
salestaxrev['date'] = pd.to_datetime(salestaxrev['Year'].
                                     replace(regex={' Quarter 1':'/1/1',' Quarter 2':'/4/1'\
                                                    ,' Quarter 3':'/7/1',' Quarter 4':'/10/1'\
                                                    ,' Annual*.*':''}))
# Clean var names
salestaxrev = salestaxrev.rename(index=str, columns={'Total Taxable':'sales','NAICS':'naics'                                                     ,'Units':'units','naicstyp':'naics_typ'})
# Keep only wanted columns
salestaxrev = salestaxrev[['state','location_name','location_id','county_name','datetyp'                           ,'date','naics_typ','naics','sales','units']]
# Merge NAICS
salestaxrev = salestaxrev.merge(naics_lookup, left_on='naics', right_on='codes', how='left')                                    .drop(columns = ['names','codes'])
# Create a Quarterly and Annual 
salestaxrev_qtrly = salestaxrev[salestaxrev.datetyp == 'Q']
salestaxrev_annual = salestaxrev[salestaxrev.datetyp == 'A']


# ### (3) Export

# In[13]:


# ----- Tables_6 files ----- 
# ----- Group_Across_Place ----- 
# N1
salestaxrev_qtrly.to_csv(output + 'SalTaxRev_WA_place_N1_qtrly' + '.csv', index=0)
salestaxrev_annual.to_csv(output + 'SalTaxRev_WA_place_N1_annl' + '.csv', index=0)
# N0
salestaxrev_qtrly[['date','county_name','location_name','location_id','sales','units']]    .groupby(['county_name','location_name','location_id','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_place_N0_qtrly' + '.csv', index=0)
salestaxrev_annual[['date','county_name','location_name','location_id','sales','units']]    .groupby(['county_name','location_name','location_id','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_place_N0_annl' + '.csv', index=0)
# ----- Group_Across_County ----- 
# N1
salestaxrev_qtrly[['date','county_name','naics','short_names','sales','units']]    .groupby(['county_name','short_names','naics','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N1_qtrly' + '.csv', index=0)
salestaxrev_annual[['date','county_name','naics'                    ,'short_names','sales','units']]    .groupby(['county_name','short_names','naics','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_county_N1_annl' + '.csv', index=0)
# N0
salestaxrev_qtrly[['date','county_name','sales','units']]    .groupby(['county_name','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N0_qtrly' + '.csv', index=0)
salestaxrev_annual[['date','county_name','naics','sales','units']]    .groupby(['county_name','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_county_N0_annl' + '.csv', index=0)
# ----- Group_Across_State ----- 
# N1
salestaxrev_qtrly[['date','state','naics','short_names','sales','units']]    .groupby(['naics','short_names','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N1_qtrly' + '.csv', index=0)
SalTaxRev_WA_state_N1_annl = salestaxrev_annual[['date','state','naics','short_names'                                                 ,'sales','units']]    .groupby(['naics','short_names','date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N1_annl' + '.csv', index=0)
# N0
salestaxrev_qtrly[['date','state','sales','units']]    .groupby(['date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N0_qtrly' + '.csv', index=0)
salestaxrev_annual[['date','state','sales','units']]    .groupby(['date']).sum().reset_index()    .to_csv(output + 'SalTaxRev_WA_state_N0_annl' + '.csv', index=0)


# In[30]:


# ----- Export_to_suit_the_Viz ----- 

df1 = pd.read_csv(output + 'SalTaxRev_WA_county_N1_annl.csv')        .groupby(['county_name','short_names','date']).sum().reset_index()
df1['date'] = pd.to_datetime(df1.date).dt.strftime('%m/%d/%y')
df1['statewide'] = 'Statewide'
df2 = df1.groupby(['statewide','short_names','date'])        .sum().reset_index()        .rename(index=str, columns={"statewide": "county_name"})
df3 = df1.append(df2)
df4 = df3.rename(columns={"date":"year","county_name":"county"})
STR_WA_C_N1_A_W = pd.pivot_table(df4, values='sales',                     index=['year','county'], columns='short_names')
STR_WA_C_N1_A_W.to_csv(output + 'STR_WA_C_N1_A_W' + '.csv')

