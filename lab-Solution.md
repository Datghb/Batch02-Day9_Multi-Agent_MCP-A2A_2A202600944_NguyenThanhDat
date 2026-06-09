# Lab Solution - Multi-Agent MCP/A2A

## 1. Tong quan bai lab

Bai lab nay xay dung mot he thong tu van phap ly theo huong tang dan do phuc tap:

1. Goi LLM truc tiep.
2. Them RAG va tools.
3. Dong goi thanh single ReAct agent.
4. Tach thanh multi-agent chay trong cung mot process.
5. Trien khai distributed multi-agent bang A2A protocol.

Muc tieu cuoi cung la co mot he thong gom nhieu agent chuyen mon hoa. User gui cau hoi vao Customer Agent, Customer Agent chuyen cau hoi den Law Agent, Law Agent phan tich phap ly va neu can se goi Tax Agent va Compliance Agent song song thong qua A2A.

## 2. Cau hinh LLM dung chung

File `common/llm.py` duoc dung lam noi khoi tao LLM tap trung cho toan bo project.

Nhung diem da lam:

- Tao ham `get_llm()` de cac stage va agent co the tai su dung cung mot cach cau hinh model.
- Ho tro provider mac dinh la OpenRouter.
- Ho tro them provider Gemini thong qua bien moi truong `LLM_PROVIDER=gemini`.
- Dat temperature mac dinh la `0.3` de output on dinh hon, dung voi yeu cau cua bai tap Stage 1.
- Cho phep cau hinh model, API key va max tokens bang `.env`.

Cach nay giup tat ca agent khong phai tu khoi tao LLM rieng le, dong thoi de thay doi model khi can benchmark latency hoac chat luong.

## 3. Stage 1 - Direct LLM Calling

Stage 1 nam tai `stages/stage_1_direct_llm/main.py`.

Noi dung da thuc hien:

- Goi LLM truc tiep bang `get_llm()`.
- Gui message theo cau truc gom `SystemMessage` va `HumanMessage`.
- `SystemMessage` dung de dinh nghia vai tro cua model la legal assistant.
- `HumanMessage` la cau hoi that cua nguoi dung.

Y nghia cua Stage 1 la cho thay LLM co the tra loi truc tiep, nhung chua co tool, chua co RAG, chua co memory va chua co kha nang phoi hop voi agent khac.

Lenh chay:

```bash
uv run python stages/stage_1_direct_llm/main.py
```

## 4. Stage 2 - LLM + RAG & Tools

Stage 2 nam tai `stages/stage_2_rag_tools/main.py`.

Noi dung da thuc hien:

- Tao knowledge base gia lap bang bien `LEGAL_KNOWLEDGE`.
- Dung decorator `@tool` cua LangChain de khai bao cac tool.
- Bind tools vao LLM bang `.bind_tools(TOOLS)`.
- Viet manual tool loop:
  - Goi LLM lan dau de model quyet dinh tool can dung.
  - Thuc thi tool theo `tool_calls`.
  - Dua ket qua tool ve lai LLM bang `ToolMessage`.
  - Goi LLM lan hai de tong hop cau tra loi cuoi cung.

Cac tool hien co:

- `search_legal_database(query)`: tra cuu legal knowledge base bang keyword matching.
- `calculate_damages(breach_type, contract_value)`: uoc tinh thiet hai trong breach of contract.
- `check_statute_of_limitations(case_type)`: kiem tra thoi hieu khoi kien theo loai vu an.

Bai tap da lam trong Stage 2:

- Them entry `labor_law` ve Bo luat Lao dong Viet Nam 2019 vao `LEGAL_KNOWLEDGE`.
- Them tool `check_statute_of_limitations` voi cac case type `contract`, `tort`, `property`.
- Them tool moi vao danh sach `TOOLS` de LLM co the goi.

Lenh chay:

```bash
uv run python stages/stage_2_rag_tools/main.py
```

## 5. Stage 3 - Single ReAct Agent

Stage 3 nam tai `stages/stage_3_single_agent/main.py`.

Noi dung da thuc hien:

- Su dung `create_react_agent()` cua LangGraph de tao agent theo ReAct pattern.
- Thay vi viet manual tool loop nhu Stage 2, agent tu lap chu trinh:
  - Think: xac dinh can lam gi.
  - Act: goi tool phu hop.
  - Observe: doc ket qua tool.
  - Lap lai cho den khi du thong tin tra loi.
- Stream tung update cua graph de quan sat tool call va ket qua.

Cac tool hien co:

- `search_legal_database`
- `calculate_penalty`
- `check_compliance_requirements`
- `search_case_law`

Bai tap da lam trong Stage 3:

- Them tool `search_case_law(keywords)`.
- Them `search_case_law` vao danh sach `TOOLS`.
- Agent co the tra cuu an le nhu `Hadley v. Baxendale`, `Donoghue v. Stevenson`, `Carlill v. Carbolic Smoke Ball Co`.

Lenh chay:

```bash
uv run python stages/stage_3_single_agent/main.py
```

## 6. Stage 4 - Multi-Agent In-Process

Stage 4 nam tai `stages/stage_4_milti_agent/main.py`.

Noi dung da thuc hien:

- Xay dung multi-agent graph bang `StateGraph`.
- Dinh nghia shared state bang `LegalState`.
- Tao cac node chuyen trach:
  - `analyze_law`: phan tich phap ly tong quat.
  - `check_routing`: quyet dinh can goi specialist nao.
  - `call_tax_specialist`: agent chuyen ve tax.
  - `call_compliance_specialist`: agent chuyen ve compliance.
  - `call_privacy_specialist`: agent chuyen ve privacy/GDPR/data protection.
  - `aggregate`: tong hop tat ca ket qua.
- Dung `Send` API de dispatch nhieu specialist node song song.
- Dung reducer `_last_wins` voi `Annotated` de xu ly viec cac nhanh song song ghi vao state.

Bai tap da lam trong Stage 4:

- Them `privacy_agent` duoi dang node `call_privacy_specialist`.
- Them field `needs_privacy` va `privacy_result` vao `LegalState`.
- Sua routing de goi privacy specialist khi cau hoi co cac keyword nhu `data`, `privacy`, `gdpr`, `du lieu`, `consent`, `breach`.
- Ket noi privacy node vao `aggregate`.

Graph tong quat:

```text
analyze_law
  -> check_routing
      -> call_tax_specialist
      -> call_compliance_specialist
      -> call_privacy_specialist
      -> aggregate
  -> END
```

Lenh chay:

```bash
uv run python stages/stage_4_milti_agent/main.py
```

## 7. Stage 5 - Distributed A2A System

Stage 5 la phan he thong that su trong repo, gom cac service doc lap:

| Service | Port | Vai tro |
|---|---:|---|
| Registry | 10000 | Luu thong tin agent va ho tro discovery |
| Customer Agent | 10100 | Entry point nhan cau hoi tu user |
| Law Agent | 10101 | Orchestrator phan tich phap ly va dieu phoi |
| Tax Agent | 10102 | Specialist ve tax |
| Compliance Agent | 10103 | Specialist ve compliance |

### Registry

Registry nam tai `registry/__main__.py`.

Da thuc hien:

- Tao FastAPI service.
- Endpoint `POST /register` de agent tu dang ky khi khoi dong.
- Endpoint `GET /discover/{task}` de tim agent theo task name.
- Endpoint `GET /agents` de xem danh sach agent da dang ky.
- Endpoint `GET /health` de kiem tra trang thai.

### A2A client va registry client

File `common/registry_client.py`:

- `register(agent_info)`: gui thong tin agent len registry.
- `discover(task)`: lay endpoint cua agent phu hop voi task.

File `common/a2a_client.py`:

- Lay Agent Card tu `/.well-known/agent.json`.
- Tao A2A message bang `Message`, `Part`, `TextPart`.
- Gui request bang `A2AClient.send_message`.
- Truyen metadata gom `trace_id`, `context_id`, `delegation_depth`.
- Trich xuat text response tu artifact/message/task history.

### Customer Agent

Customer Agent nam tai `customer_agent/`.

Da thuc hien:

- Expose A2A server tren port `10100`.
- Tao Agent Card cho endpoint `/.well-known/agent.json`.
- Dung `CustomerAgentExecutor` de noi A2A request voi LangGraph.
- Dung `create_react_agent()` voi tool `delegate_to_legal_agent`.
- Khi nhan cau hoi phap ly, agent discover Law Agent theo task `legal_question` va delegate qua A2A.

### Law Agent

Law Agent nam tai `law_agent/`.

Da thuc hien:

- Xay dung `StateGraph` voi cac node:
  - `analyze_law`
  - `check_routing`
  - `call_tax`
  - `call_compliance`
  - `aggregate`
- Dung `route_to_subagents()` de dispatch Tax Agent va Compliance Agent song song bang `Send`.
- Goi sub-agent qua A2A thay vi goi ham noi bo.
- Co `MAX_DELEGATION_DEPTH = 3` de tranh vong lap delegate vo han.
- Ho tro `FAST_ROUTING=true` de route bang keyword thay vi ton them mot lan goi LLM.
- Neu Tax/Compliance Agent loi, Law Agent van tra ve ket qua voi thong bao phan tich khong kha dung.

### Tax Agent va Compliance Agent

Tax Agent nam tai `tax_agent/graph.py`.

- Dung `create_react_agent()`.
- System prompt chuyen ve corporate tax, IRS, FBAR/FATCA, tax fraud, penalties.
- Tra loi ngan gon theo bullet de giam do dai va latency.

Compliance Agent nam tai `compliance_agent/graph.py`.

- Dung `create_react_agent()`.
- System prompt chuyen ve SEC, SOX, FTC, FCPA, AML/BSA, GDPR, CCPA va corporate governance.
- Phan tich agency jurisdiction, remedies, individual liability va mitigating factors.

## 8. Luong request end-to-end

Luong xu ly khi chay `test_client.py`:

```text
User question
  -> Customer Agent
  -> Registry discover("legal_question")
  -> Law Agent
  -> analyze_law
  -> check_routing
  -> Registry discover("tax_question")
  -> Registry discover("compliance_question")
  -> Tax Agent va Compliance Agent chay song song
  -> Law Agent aggregate
  -> Customer Agent
  -> User
```

Trong moi lan delegate, he thong truyen them:

- `trace_id`: theo doi mot request xuyen qua nhieu service.
- `context_id`: gan voi conversation/task context.
- `delegation_depth`: gioi han do sau delegate.

## 9. Cach chay va kiem thu

Khoi dong toan bo he thong:

```bash
./start_all.sh
```

Script nay khoi dong theo thu tu:

1. Registry
2. Tax Agent
3. Compliance Agent
4. Law Agent
5. Customer Agent

Sau do chay client test:

```bash
uv run python test_client.py
```

`test_client.py` se:

- Lay Agent Card cua Customer Agent.
- Gui cau hoi mau:

```text
If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?
```

- In response tu he thong.
- In latency bang `perf_counter()`.

## 10. Cau hoi cong diem: latency va cach giam latency

Trong repo, `test_client.py` da co do latency:

```python
start = perf_counter()
response = await client.send_message(request)
elapsed = perf_counter() - start
```

De lay ket qua thuc te tren may, chay:

```bash
./start_all.sh
uv run python test_client.py
```

Ket qua latency se duoc in o cuoi output:

```text
Latency: <so_giay> seconds
```

Phuong an giam latency da ap dung trong repo:

- Them `FAST_ROUTING=true` cho Law Agent.
- Khi bat `FAST_ROUTING`, `check_routing` dung keyword matching de quyet dinh `needs_tax` va `needs_compliance`.
- Cach nay bo bot mot lan goi LLM chi de routing, nen request nhanh hon.
- Tax Agent va Compliance Agent van duoc goi song song thong qua `Send`, giup tong latency khong bang tong thoi gian cua hai specialist.

Cach benchmark:

```bash
# Lan 1: routing bang LLM
FAST_ROUTING=false ./start_all.sh
uv run python test_client.py

# Lan 2: routing bang keyword
FAST_ROUTING=true ./start_all.sh
uv run python test_client.py
```

So sanh hai gia tri `Latency` de thay muc giam thoi gian.

## 11. Ket luan

Sau bai lab, repo da the hien day du qua trinh tien hoa cua mot ung dung LLM:

- Stage 1: LLM co ban.
- Stage 2: LLM co RAG/tools.
- Stage 3: ReAct agent tu dieu phoi tool.
- Stage 4: Multi-agent in-process voi parallel routing.
- Stage 5: Distributed agents qua A2A protocol, co registry discovery, agent card, trace propagation va depth guard.

He thong cuoi cung co kien truc ro rang, de mo rong them specialist agent moi va co the quan sat request flow thong qua `trace_id`.
