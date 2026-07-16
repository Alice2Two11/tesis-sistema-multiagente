from __future__ import annotations

def _list(v):
    if v is None:return []
    if isinstance(v,list):return v
    if isinstance(v,dict):return [v]
    raise ValueError('INVALID_THEMATIC_SCHEMA')
def normalize_thematic_output(payload):
    if isinstance(payload,list) and len(payload)==1 and isinstance(payload[0],dict): payload=payload[0]
    if not isinstance(payload,dict): raise ValueError('INVALID_LLM_OUTPUT')
    out=dict(payload)
    aliases={'gaps':'research_gaps','structure':'suggested_state_of_art_structure','dimensions':'comparative_dimensions'}
    for a,b in aliases.items():
        if b not in out and a in out: out[b]=out[a]
    for key in ['themes','research_gaps','suggested_state_of_art_structure','comparative_dimensions']:
        out[key]=_list(out.get(key,[]))
    if not any(out[k] for k in ['themes','research_gaps','suggested_state_of_art_structure','comparative_dimensions']): raise ValueError('EMPTY_THEMATIC_OUTPUT')
    issues=[]
    for key,code in [('themes','INVALID_THEME_RECORD'),('research_gaps','INVALID_GAP_RECORD'),('suggested_state_of_art_structure','INVALID_STRUCTURE_RECORD'),('comparative_dimensions','INVALID_COMPARATIVE_DIMENSION_RECORD')]:
        good=[]
        for x in out[key]:
            if isinstance(x,dict):good.append(x)
            else:issues.append({'code':code,'value':repr(x)})
        out[key]=good
    return out,issues
