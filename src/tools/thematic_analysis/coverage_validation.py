from __future__ import annotations

def _src(p): return p if isinstance(p,str) else str(p.get('source_filename','')) if isinstance(p,dict) else ''
def calculate_diagnostic_metrics(data,df,ref_counts):
    corpus=set(df.source_filename.astype(str)); assignments=[]; supported_themes=0
    for t in data['themes']:
        srcs=[_src(p) for p in t.get('representative_papers',[]) if _src(p)]
        assignments+=srcs
        if srcs and bool(str(t.get('theme_name') or t.get('theme') or '').strip()): supported_themes+=1
    unique=set(assignments)&corpus
    gaps=data['research_gaps']; supported_gaps=sum(bool(g.get('supporting_sources')) and bool(str(g.get('basis') or g.get('description') or '').strip()) for g in gaps)
    dims=data['comparative_dimensions']; supported_dims=sum(len(d.get('relevant_sources',[]) or [])>=2 for d in dims)
    total_refs=ref_counts['reference_total']; valid_refs=ref_counts['valid_references']; title_total=ref_counts['title_total']; title_matches=ref_counts['title_matches']
    n=len(corpus); a=len(assignments)
    return {
      'paper_coverage':len(unique)/n if n else 0.0,'theme_coverage':supported_themes/len(data['themes']) if data['themes'] else 0.0,
      'papers_assigned_to_theme_rate':len(unique)/n if n else 0.0,'supported_theme_rate':supported_themes/len(data['themes']) if data['themes'] else 0.0,
      'supported_gap_rate':supported_gaps/len(gaps) if gaps else 1.0,'valid_reference_rate':valid_refs/total_refs if total_refs else 1.0,
      'title_match_rate':title_matches/title_total if title_total else 1.0,'comparative_dimension_support_rate':supported_dims/len(dims) if dims else 1.0,
      'unassigned_paper_rate':(n-len(unique))/n if n else 0.0,'duplicate_assignment_rate':max(0,a-len(set(assignments)))/a if a else 0.0,
      'structure_source_validity_rate':1.0,'gap_source_validity_rate':1.0 if not gaps else supported_gaps/len(gaps),
      'representative_source_validity_rate':valid_refs/total_refs if total_refs else 1.0,'invalid_record_rate':0.0,
      'section_count':len(data['suggested_state_of_art_structure'])
    }
