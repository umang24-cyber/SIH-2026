"""Self-contained API reference and safe, local source citations."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from backend.app.core.config import BASE_DIR

router = APIRouter(include_in_schema=False)
ALLOWED_EXTENSIONS = {".md", ".py", ".ts", ".tsx", ".json", ".toml", ".sh", ".txt"}
ROOT_CITATIONS = {"DATA_DICTIONARY.md", "GRAPH_ENGINE.md", "DEADLOCK_PROTOCOL.md", "package.json", "vite.config.ts", "readme.md", "requirements.txt"}


@router.get("/source/{source_path:path}")
def local_source(source_path: str):
    """Read-only repository citation. Resolved symlinks and traversals stay inside the bundle."""
    root = Path(BASE_DIR).resolve()
    candidate = (root / source_path).resolve()
    relative = candidate.relative_to(root) if candidate.is_relative_to(root) else None
    cited = relative and relative.parts and not any(part.startswith(".") for part in relative.parts) and (
        (relative.parts[0] in {"docs", "backend", "cli", "src"})
        or (relative.parts[0] == "data" and relative.suffix.lower() == ".md")
        or (relative.parts[:2] == ("ml", "manifests") and relative.suffix.lower() == ".json")
        or (len(relative.parts) == 1 and relative.name in ROOT_CITATIONS)
    )
    if not cited or not candidate.is_file() or candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Source file unavailable in this offline bundle")
    return FileResponse(candidate, media_type="text/plain; charset=utf-8")


@router.get("/redoc")
def offline_redoc():
    return RedirectResponse("/docs", status_code=307)


@router.get("/docs", response_class=HTMLResponse)
def offline_api_reference():
    """No CDN, remote fonts, or third-party JavaScript needed to browse /openapi.json."""
    return HTMLResponse("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BitKaun Local API Reference</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1050px;margin:auto;padding:2rem;background:#f5f1e8;color:#252820}
h1{margin-bottom:.2rem}p{color:#46513b}input{font:inherit;padding:.6rem;width:min(100%,35rem);box-sizing:border-box}
details{margin:.55rem 0;border:1px solid #d9d1c2;background:white;padding:.6rem 1rem}
summary{cursor:pointer;overflow-wrap:anywhere}code,pre{font:13px/1.5 ui-monospace,monospace}
pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:32rem;overflow:auto;background:#eee;padding:1rem}
.method{font-weight:bold;color:#46513b;margin-right:1rem}a{color:#722f42}
</style></head><body><h1>BitKaun API Reference</h1>
<p>Served entirely from this device. <a href="/openapi.json">Download the local OpenAPI schema</a>.</p>
<label for="filter">Filter endpoints</label><br><input id="filter" type="search" placeholder="Search path, method, summary…">
<p id="status" role="status">Loading local schema…</p><main id="routes"></main>
<script>
(async()=>{const status=document.getElementById('status'),list=document.getElementById('routes'),filter=document.getElementById('filter');
try{const response=await fetch('/openapi.json');if(!response.ok)throw Error('OpenAPI schema unavailable');
const schema=await response.json(),rows=[];
for(const [path,methods] of Object.entries(schema.paths))for(const [method,operation] of Object.entries(methods)){
if(!['get','post','put','delete','patch'].includes(method))continue;
const panel=document.createElement('details'),summary=document.createElement('summary'),verb=document.createElement('span');
verb.className='method';verb.textContent=method.toUpperCase();summary.append(verb,document.createTextNode(path+' — '+(operation.summary||'')));
const description=document.createElement('p');description.textContent=operation.description||'';
const contract=document.createElement('pre');contract.textContent=JSON.stringify({parameters:operation.parameters||[],requestBody:operation.requestBody||null,responses:operation.responses||{}},null,2);
panel.append(summary,description,contract);list.append(panel);rows.push({panel,search:(method+' '+path+' '+(operation.summary||'')).toLowerCase()});}
const update=()=>{const query=filter.value.trim().toLowerCase();let count=0;for(const row of rows){row.panel.hidden=!row.search.includes(query);if(!row.panel.hidden)count++;}status.textContent=count+' endpoint'+(count===1?'':'s')+' in local schema';};
filter.addEventListener('input',update);update();}
catch(error){status.textContent=error.message||'Could not load the local API reference.';}})();
</script></body></html>""")
