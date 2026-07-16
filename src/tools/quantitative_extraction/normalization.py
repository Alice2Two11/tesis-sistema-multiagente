from __future__ import annotations
import re
from .input_validation import safe_str

def normalize_metric_name(value):
    text=safe_str(value).strip(); key=re.sub(r"[^a-z0-9]+","",text.casefold())
    aliases={"r2":"R²","rsquared":"R²","rmse":"RMSE","mae":"MAE","mape":"MAPE","accuracy":"Accuracy"}
    return aliases.get(key,text)

def extract_numeric_tokens(value):
    return re.findall(r"[-+]?\d+(?:[.,]\d+)?%?",safe_str(value))

def parse_float_from_value(value):
    tokens=extract_numeric_tokens(value)
    if len(tokens)!=1: return None
    try: return float(tokens[0].replace("%","").replace(",","."))
    except ValueError: return None

def ensure_list(value):
    return value if isinstance(value,list) else []

def aggregate_unique(values, max_chars=1000):
    seen=[]
    for value in values:
        text=safe_str(value).strip()
        if text and text not in seen: seen.append(text)
    return "; ".join(seen)[:max_chars]

def flatten_results(all_results):
    techniques=[]; datasets=[]; quantitative=[]
    for item in all_results:
        source=safe_str(item.get("source_filename")); title=safe_str(item.get("paper_title"))
        for x in ensure_list(item.get("techniques")):
            if isinstance(x,dict): techniques.append({"source_filename":source,"paper_title":title,"technique_name":safe_str(x.get("technique_name") or x.get("name")),"technique_family":safe_str(x.get("technique_family") or x.get("family")),"role":safe_str(x.get("role")),"source_text_evidence":safe_str(x.get("source_text_evidence") or x.get("evidence"))})
        for x in ensure_list(item.get("datasets")):
            if isinstance(x,dict): datasets.append({"source_filename":source,"paper_title":title,"dataset_name":safe_str(x.get("dataset_name") or x.get("name")),"case_study":safe_str(x.get("case_study")),"data_type":safe_str(x.get("data_type")),"temporal_resolution":safe_str(x.get("temporal_resolution")),"spatial_resolution":safe_str(x.get("spatial_resolution")),"analysis_scope":safe_str(x.get("analysis_scope")),"source_text_evidence":safe_str(x.get("source_text_evidence") or x.get("evidence"))})
        for x in ensure_list(item.get("quantitative_results")):
            if isinstance(x,dict): quantitative.append({"source_filename":source,"paper_title":title,"model_or_method":safe_str(x.get("model_or_method")),"metric":normalize_metric_name(x.get("metric")),"value":safe_str(x.get("value")),"numeric_value":parse_float_from_value(x.get("value")),"unit":safe_str(x.get("unit")),"dataset_or_case":safe_str(x.get("dataset_or_case")),"evaluation_scope":safe_str(x.get("evaluation_scope")),"data_resolution":safe_str(x.get("data_resolution")),"condition":safe_str(x.get("condition")),"source_text_evidence":safe_str(x.get("source_text_evidence") or x.get("evidence"))})
    return techniques,datasets,quantitative
