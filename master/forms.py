from django import forms
from models import City,Survey
import urllib2,urllib
import json
from django.conf import settings
from shelter  import local_settings
import psycopg2

survey_list=[]

class SurveyCreateForm(forms.ModelForm):
    kobotool_survey_id = forms.ChoiceField(widget=forms.Select(),required=True)
    kobotool_survey_url = forms.CharField(required=True)    
    def __init__(self,*args,**kwargs):        
        try:
            self.survey=kwargs.pop('survey')
        except:
            print "No survey Id"
                
        super(SurveyCreateForm,self).__init__(*args,**kwargs)
        self.list_i=[]
        self.list_i=getKoboIdList()   
        self.fields['kobotool_survey_id'].choices=self.list_i
        self.fields['kobotool_survey_id'].initial=[0]
        self.fields['kobotool_survey_url'].required = False 
        #self.fields['kobotoolSurvey_url'].widget.attrs['readonly'] = True 
    class Meta:
        model=Survey
        fields = ['name','description','city','survey_type','analysis_threshold','kobotool_survey_id']
        
    def save(self, *args, **kwargs):        
        instance = super(SurveyCreateForm,self).save(commit=False)
       
        try:
            instance.id=self.survey
        except:
            print "Error for Survey_id"          
       
        kobourl=""
        data = self.cleaned_data
      
        for survey_value in survey_list:  
            if survey_value[0]== data['kobotool_survey_id']:
                kobourl= survey_value[1]
                
        instance.kobotool_survey_url=kobourl
        instance.save()
        return instance
        
def getKoboIdList():
    url=local_settings.KOBOCAT_FORM_URL
    req = urllib2.Request(url)
    req.add_header('Authorization', local_settings.KOBOCAT_TOKEN)
    resp = urllib2.urlopen(req)
    content = resp.read()         
    data = json.loads(content) 
    
    temp_arr=[]
    temp_arr.append(('','Select'))
    for value in data:  
        survey_list.append((value['id_string'],value['url']))  
        temp_arr.append((value['id_string'],value['id_string']))

    return temp_arr        



class SurveyReportForm(forms.ModelForm):
    kobotool_survey_id = forms.ChoiceField(widget=forms.Select(),required=True)

    def __init__(self,*args,**kwargs):
        try:
            self.kobotool_survey_id=kwargs.pop('kobo_survey_id')
        except:
            print "No kobo_survey_id Form"

        super(SurveyReportForm,self).__init__(*args,**kwargs)
        self.list_i=[]
        self.list_i=getKoboIdList()
        self.fields['kobotool_survey_id'].choices=self.list_i
        self.fields['kobotool_survey_id'].initial=[0]

    class Meta:
        model=Survey
        fields = ['city','survey_type','kobotool_survey_id']

def getKoboSurveyIdList(koboformid):
    url=local_settings.KOBOCAT_DATA_FORM_ID + getkoboFormID(koboformid)
    req = urllib2.Request(url)
    req.add_header('Authorization', local_settings.KOBOCAT_TOKEN)
    resp = urllib2.urlopen(req)
    content = resp.read()
    kobocatdata = json.loads(content)

    #Code for Dkobo Form Data
    url1=local_settings.DKOBO_FORM_ID + getkoboFormID(koboformid)+"/form"
    dkreq = urllib2.Request(url1)
    dkreq.add_header('Authorization', local_settings.KOBOCAT_TOKEN)
    dkresp = urllib2.urlopen(dkreq)
    dkcontent = dkresp.read()
    dkdata = json.loads(dkcontent)

    dkobodict={}
    for value in dkdata['children']:
        try:
            if value['bind']:
                if value['type']=="select one" or value['type']=="select all that apply":
                    dkobodict[value['name']]=(value['label'],value['type'],value['children'])
                else:
                     dkobodict[value['name']]=(value['label'],value['type'])
                #dkobodict[value['name']]=(value['label'])
        except:
            print "getKoboSurveyIdList Error"

    #code for KObocat Data values
    kobo_arr={}
    final_kobo_arr={}
    counter=0
    for value in kobocatdata:
        kobo_arr={}
        for key,kobovalue in value.items():
            for dkey,dkvalue in dkobodict.items():
                if dkey==key:
                    if dkvalue[1]=='select all that apply' or dkvalue[1]=='select one':
                        finaldkselval=""
                        for dkselchild in range(len(dkvalue[2])):
                            dkselsplit=kobovalue.split(" ")
                            for da in range(len(dkselsplit)):
                                if dkselsplit[da]==dkvalue[2][dkselchild]['name']:
                                    finaldkselval += dkvalue[2][dkselchild]['label']+" "

                            kobo_arr[dkvalue[0]]=finaldkselval
                    else:
                        kobo_arr[dkvalue[0]]=kobovalue
        if kobo_arr:
            final_kobo_arr[counter]=kobo_arr
        counter+=1

    return final_kobo_arr

def getkoboFormID(koboformid):
    conn = psycopg2.connect(database=settings.KOBOCAT_DATABASES['DBNAME'],
                            user=settings.KOBOCAT_DATABASES['USER'],
                            password=settings.KOBOCAT_DATABASES['PASSWORD'],
                            host=settings.KOBOCAT_DATABASES['HOST'],
                            port=settings.KOBOCAT_DATABASES['PORT'] )

    cursor = conn.cursor()
    query="select id from logger_xform where id_string='"+koboformid+"'"
    cursor.execute(query)
    jsonCursor = cursor.fetchall()

    koboid=""
    for jsonValue in jsonCursor[0]:
            koboid=jsonValue

    return  str(koboid)
