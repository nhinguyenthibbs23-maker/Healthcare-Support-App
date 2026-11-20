from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
TARGET='Diabetes_binary'
AGES=['18–24','25–29','30–34','35–39','40–44','45–49','50–54','55–59','60–64','65–69','70–74','75–79','80 or older']
SPECS={
'HighBP':('High blood pressure','0 no; 1 ever told high blood pressure','Include: known history; unknown is not no.'),
'HighChol':('High cholesterol','0 no; 1 ever told high cholesterol','Include: known history; unknown is not no.'),
'CholCheck':('Cholesterol check','0 no; 1 checked in past five years','Exclude: testing/access can proxy diagnosis.'),
'BMI':('Body mass index','kg/metres squared; observed 12–98','Include: two familiar measurements; original observed BMI values are retained without upper capping.'),
'Smoker':('Smoking history','0 no; 1 smoked >=100 cigarettes in lifetime','Include: an additional clearly defined survey behavior question; added to the eight-input model.'),
'Stroke':('Stroke history','0 no; 1 ever told had a stroke','Exclude: extra medical burden and possible disease consequence.'),
'HeartDiseaseorAttack':('Heart disease/attack','0 no; 1 coronary heart disease or myocardial infarction','Exclude: complex and possible disease consequence.'),
'PhysActivity':('Physical activity','0 no; 1 leisure activity in past 30 days excluding regular job','Include: an additional activity question; define that regular work activity does not count.'),
'Fruits':('Daily fruit','0 no; 1 fruit at least once daily','Exclude: extra recall burden; compare full model.'),
'Veggies':('Daily vegetables','0 no; 1 vegetables at least once daily','Exclude: extra recall burden; compare full model.'),
'HvyAlcoholConsump':('Heavy drinking','0 no; 1 >14 drinks/week men or >7 women','Exclude: sensitive and complex; adds <0.002 validation AUC and its association direction is counter-intuitive.'),
'AnyHealthcare':('Healthcare coverage','0 no; 1 any health coverage','Exclude: US-specific access proxy.'),
'NoDocbcCost':('Cost prevented doctor visit','0 no; 1 prevented by cost in past 12 months','Exclude: socioeconomic/access proxy.'),
'GenHlth':('General health','1 excellent; 2 very good; 3 good; 4 fair; 5 poor','Include: easy self-report; may reflect existing disease.'),
'MentHlth':('Poor mental health days','0–30 days in past 30 days','Exclude: recall burden and sensitive.'),
'PhysHlth':('Poor physical health days','0–30 days in past 30 days','Exclude: recall burden; general health already asked.'),
'DiffWalk':('Walking difficulty','0 no; 1 serious difficulty walking/climbing stairs','Include: an additional functional-health question; may reflect current health, not a cause.'),
'Sex':('Recorded sex','0 female; 1 male in source survey','Exclude from short model; audit only. Binary survey coding has limitations.'),
'Age':('Age group','1 18–24; 2 25–29; five-year bands to 12 75–79; 13 80+','Include: adult demographic, categorical codes are not years.'),
'Education':('Education','1 no school/kindergarten; 2 grades 1–8; 3 grades 9–11; 4 high-school/GED; 5 college 1–3 years; 6 college 4+ years','Exclude from short model; audit only.'),
'Income':('Household income (USD/year, 2015)','1 <10k; 2 10–<15k; 3 15–<20k; 4 20–<25k; 5 25–<35k; 6 35–<50k; 7 50–<75k; 8 >=75k','Exclude: intrusive, US-specific; audit only.')}
SHORT=['Age','BMI','HighBP','HighChol','GenHlth','Smoker','PhysActivity','DiffWalk']  # 8 user inputs; eligibility check is separate
SOURCES={'Dataset':'https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset','CDC codebook':'https://www.cdc.gov/brfss/annual_data/2015/pdf/CODEBOOK15_LLCP.pdf','CDC survey':'https://www.cdc.gov/brfss/annual_data/annual_2015.html'}
def load_data(path):
    df=pd.read_csv(path)
    if set(df.columns)!=set(SPECS)|{TARGET}: raise ValueError('Unexpected columns.')
    if len(df)!=253680 or set(df[TARGET])!={0,1}: raise ValueError('Use original imbalanced binary CSV, not 50/50.')
    if df.isna().any().any(): raise ValueError('Unexpected missing values: investigate before training.')
    for c in df:
        v=set(df[c]); limits={'Age':13,'Education':6,'Income':8,'GenHlth':5}
        if c=='BMI': valid=df[c].between(12,98).all()
        elif c in ['MentHlth','PhysHlth']: valid=v<=set(range(31))
        elif c in limits: valid=v<=set(range(1,limits[c]+1))
        else: valid=v<={0,1}
        if not valid: raise ValueError('Unexpected values: '+c)
    return df

def meta(): return json.loads((ROOT/'models/model_meta.json').read_text())


def load_validation_predictions():
    d = np.load(ROOT / "models" / "validation_predictions.npz")
    return d["y"], d["p"]


def load_tuned_validation_predictions():
    d = np.load(ROOT / "reports" / "tuned_validation_predictions.npz")
    y = d["y"]
    probs = {name: d["probabilities"][i] for i, name in enumerate(d["model_names"])}
    return y, probs


def load_tuned_model_validation():
    return pd.read_csv(ROOT / "reports" / "tuned_model_validation.csv")

