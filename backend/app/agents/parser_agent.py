import json
from langchain_core.prompts import ChatPromptTemplate
from ..core.llm import get_fast_llm

parser_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Resume Parser Agent. Extract structured data.
Return ONLY valid JSON: {{"skills": ["ALL technical skills open vocab, exhaustive"], "experience_years": int, "location": ["cities"], "domains": [], "education": [], "summary": str}}
Rules: No predefined list. Extract everything like Helm, ArgoCD, Next.js, K8s, EKS etc. Do not limit."""),
    ("human", "{resume_text}")
])


def parse_resume_node(state: dict):
    text = state.get("resume_text", "")[:6000]
    llm = get_fast_llm(temperature=0)
    if not llm:
        return {"parsed": {"skills": [], "experience_years": 0, "location": [], "domains": [], "summary": text[:300]}}
    chain = parser_prompt | llm
    try:
        res = chain.invoke({"resume_text": text})
        content = getattr(res, "content", str(res))
        s = content.find("{")
        e = content.rfind("}")
        data = json.loads(content[s:e+1] if s != -1 else content)
        return {"parsed": data}
    except Exception as e:
        return {"parsed": {"error": str(e), "skills": [], "experience_years": 0, "location": [], "domains": [], "summary": text[:300]}}
