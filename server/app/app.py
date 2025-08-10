from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
import uuid

app = FastAPI(title="LLMSEO + CATADD API", version="0.1.1")

# ----- In-memory stubs (replace with DB) -----
TASKS: Dict[str, Dict[str, Any]] = {}

def create_task(account_id: str, site_id: str, type_: str, payload: dict) -> str:
    tid = str(uuid.uuid4())
    TASKS[tid] = {
        "id": tid,
        "account_id": account_id,
        "site_id": site_id,
        "type": type_,
        "payload": payload,
        "state": "proposed"
    }
    return tid

# ----- Models -----
class FixItem(BaseModel):
    title: str
    severity: str
    rationale: str
    action: str

class RunAuditRequest(BaseModel):
    account_id: str
    site_id: str
    domain: str
    keywords: List[str] | None = None
    serp_provider: Literal["serpapi","dataforseo"] = "serpapi"

class RunAuditResponse(BaseModel):
    top_fixes: List[FixItem]
    serp_snapshot_ids: List[str]
    task_id: str

class ContentProposeRequest(BaseModel):
    account_id: str
    site_id: str
    target_keywords: List[str]
    page_type: str = "blog"
    num_drafts: int = 3

class DraftBrief(BaseModel):
    keyword: str
    entities: List[str]
    outline: List[str]
    schema_plan: Dict[str, Any]

class ContentProposeResponse(BaseModel):
    briefs: List[DraftBrief]
    proposed_task_id: str

class AdsProposeRequest(BaseModel):
    account_id: str
    site_id: str
    objective: Literal["leads","sales","traffic"]
    max_daily_budget: float

class AdGroupPlan(BaseModel):
    name: str
    keywords: List[str]
    negatives: List[str]
    ads: List[Dict[str, str]]

class AdsProposeResponse(BaseModel):
    campaign_name: str
    adgroups: List[AdGroupPlan]
    proposed_task_id: str

class DecisionPayload(BaseModel):
    decision: Literal["approve","reject"]
    reason: str | None = None

# ----- Routes -----
@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/audit/run", response_model=RunAuditResponse)
async def run_audit(req: RunAuditRequest):
    fixes = [
        FixItem(title="Add Organization schema", severity="high", rationale="LLM + SEO entity clarity", action="Inject JSON-LD on homepage"),
        FixItem(title="Create pillar page for primary topic", severity="high", rationale="Topical authority foundation", action="New /guides/<topic> with cluster links"),
        FixItem(title="Compress hero images", severity="medium", rationale="LCP improvement", action="WebP + lazy loading"),
    ]
    serp_ids = [str(uuid.uuid4())]
    task_id = create_task(req.account_id, req.site_id, "audit", {"fixes":[f.dict() for f in fixes], "serp_ids": serp_ids})
    return RunAuditResponse(top_fixes=fixes, serp_snapshot_ids=serp_ids, task_id=task_id)

@app.post("/content/propose", response_model=ContentProposeResponse)
async def content_propose(req: ContentProposeRequest):
    briefs = []
    for kw in req.target_keywords[: req.num_drafts]:
        briefs.append(DraftBrief(
            keyword=kw,
            entities=["PrimaryEntity","RelatedEntityA","RelatedEntityB"],
            outline=["Intro (answer-first)","What/Why","How","FAQs"],
            schema_plan={"@type":"Article","mentions":["PrimaryEntity"]}
        ))
    task_id = create_task(req.account_id, req.site_id, "content_draft", {"briefs":[b.dict() for b in briefs], "page_type": req.page_type})
    return ContentProposeResponse(briefs=briefs, proposed_task_id=task_id)

@app.post("/ads/propose", response_model=AdsProposeResponse)
async def ads_propose(req: AdsProposeRequest):
    adgroups = [AdGroupPlan(
        name="Core Terms",
        keywords=["best <product>","buy <product>","<brand> <product>"],
        negatives=["free","cheap"],
        ads=[{"headline":"Get <Product> Today","description":"Fast delivery. 30-day returns.","path":"shop"}]
    )]
    task_id = create_task(req.account_id, req.site_id, "ads_change", {
        "objective": req.objective,
        "budget": req.max_daily_budget,
        "campaign": "CATADD Launch",
        "adgroups": [ag.dict() for ag in adgroups]
    })
    return AdsProposeResponse(campaign_name="CATADD Launch", adgroups=adgroups, proposed_task_id=task_id)

@app.post("/tasks/{task_id}/decide")
async def decide_task(task_id: str, body: DecisionPayload):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["state"] = "approved" if body.decision == "approve" else "rejected"
    if body.reason:
        task["reason"] = body.reason
    return {"ok": True, "task": task}

# Ads sandbox reader (requires env later; read-only)
from fastapi import APIRouter
ads_router = APIRouter(prefix="/ads", tags=["ads"])
@ads_router.get("/{customer_id}/campaigns")
async def campaigns(customer_id: str):
    # TODO: replace with google-ads client; return dummy for now
    return [{"id": "123", "name":"Test Campaign", "status":"ENABLED"}]

app.include_router(ads_router)

from server.app.routers.publish_wp import router as publish_wp_router
app.include_router(publish_wp_router)
