from __future__ import annotations
import re

def safe_str(value):
    if value is None: return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def tokenize_for_overlap(text):
    return {t for t in re.findall(r"[\wáéíóúüñ]+", safe_str(text).lower()) if len(t) > 2}

def is_non_substantive_evidence(text):
    low=safe_str(text).lower()
    blocked=("author contributions","funding","acknowledgments","acknowledgements","conflicts of interest","publisher's note","publisher note")
    return not low or any(x in low for x in blocked)

def dedupe_evidence(rows, top_k=None):
    best={}
    for row in rows:
        source=safe_str(row.get("source_filename")); chunk=safe_str(row.get("chunk_id")); text=safe_str(row.get("text") or row.get("chunk_text"))
        if not source or not chunk or is_non_substantive_evidence(text): continue
        key=(source,chunk); score=float(row.get("score",0.0) or 0.0)
        item=dict(row); item["source_filename"]=source;item["chunk_id"]=chunk;item["text"]=text;item["score"]=score
        if key not in best or score>best[key]["score"]:best[key]=item
    result=sorted(best.values(),key=lambda r:r["score"],reverse=True)
    return result[:top_k] if top_k else result

def build_section_query(section):
    parts=[section.get("section_title"),section.get("purpose")]
    parts += list(section.get("key_arguments") or [])
    parts += list(section.get("evidence_needs") or [])
    return " ".join(safe_str(x) for x in parts if safe_str(x))

def query_chroma_restricted(collection, query, sources, top_k):
    rows=[]
    for source in sources:
        response=collection.query(query_texts=[query],n_results=top_k,where={"source_filename":source},include=["documents","metadatas","distances"])
        docs=(response.get("documents") or [[]])[0]; metas=(response.get("metadatas") or [[]])[0]; dists=(response.get("distances") or [[]])[0]
        for doc,meta,dist in zip(docs,metas,dists):
            rows.append({"source_filename":source,"chunk_id":safe_str((meta or {}).get("chunk_id")),"text":safe_str(doc),"score":1.0-float(dist or 0.0),"retrieval_method":"chroma_restricted"})
    return dedupe_evidence(rows,top_k)

def query_csv_restricted(chunks_df, query, sources, top_k):
    q=tokenize_for_overlap(query); rows=[]
    subset=chunks_df[chunks_df["source_filename"].astype(str).isin(list(sources))]
    for _,r in subset.iterrows():
        text=safe_str(r.get("text") if "text" in r else r.get("chunk_text")); overlap=len(q & tokenize_for_overlap(text));
        if overlap<=0: continue
        rows.append({"source_filename":safe_str(r.get("source_filename")),"chunk_id":safe_str(r.get("chunk_id")),"text":text,"score":float(overlap),"retrieval_method":"csv_lexical_restricted"})
    return dedupe_evidence(rows,top_k)

def retrieve_section_evidence(section, collection, chunks_df, top_k):
    sources=[safe_str(p.get("source_filename") if isinstance(p,dict) else p) for p in (section.get("papers_to_use") or [])]
    sources=[s for s in sources if s]
    if not sources:return []
    query=build_section_query(section)
    evidence=query_chroma_restricted(collection,query,sources,top_k)
    if len(evidence)<top_k:
        evidence=dedupe_evidence(evidence+query_csv_restricted(chunks_df,query,sources,top_k),top_k)
    return evidence
