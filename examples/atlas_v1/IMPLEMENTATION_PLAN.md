# Piano di Implementazione Atlas V1 - DeepAgents Alignment

## Executive Summary
Questo documento definisce il piano di implementazione per allineare Atlas V1 con i pattern e best practices del framework DeepAgents, risolvendo le priorità 1, 2 e 3 identificate nell'analisi di allineamento.

**Obiettivo principale**: Trasformare Atlas V1 da sistema over-engineered di 2000+ linee a implementazione pulita di ~400 linee (-80% reduction).

**Modello di riferimento**: Research example (167 linee) - dimostra l'approccio corretto con DeepAgents.

## Status Tracker
- [ ] **FASE 1**: Core Architecture Refactoring (Priorità 1 & 2)
- [ ] **FASE 2**: Tool Simplification (Priorità 3)  
- [ ] **FASE 3**: Integration & Optimization

---

## FASE 1: Core Architecture Refactoring (Priorità 1 & 2)
**Timeline**: Settimane 1-2  
**Obiettivo**: Risolvere violazioni architetturali critiche e crisis di state management

### 1.1 Implementare Proper State Management ⏳
**Status**: Not Started  
**Files da modificare**: `atlas_agent.py`, `subagents.py`  
**File da creare**: `atlas_state.py`

#### Tasks:
- [ ] Creare `AtlasState` schema che estende `DeepAgentState`
  ```python
  class AtlasState(DeepAgentState):
      """Properly typed state schema"""
      current_phase: NotRequired[Literal["investigation", "discussion", "planning", "task_generation"]]
      project_id: NotRequired[str]
      investigation_complete: NotRequired[bool]
      discussion_complete: NotRequired[bool]
      planning_complete: NotRequired[bool]
      # files: dict[str, str] inherited for virtual filesystem
  ```
- [ ] Eliminare `self.state` dictionary custom in `atlas_agent.py:77-87`
- [ ] Migrare a state management atomico con `Command` objects
- [ ] Rimuovere logica di sincronizzazione manuale (`atlas_agent.py:576-583`)

#### Success Criteria:
- Nessun dual state system
- Tutti gli updates via `Command` objects
- Stato atomico e consistente

### 1.2 Implementare StateGraph Decision Architecture ⏳
**Status**: Not Started  
**Files da modificare**: `atlas_agent.py`, `subagents.py`  
**File da creare**: `atlas_graph.py`

#### Tasks:
- [ ] Sostituire `get_next_phase()` lineare con StateGraph intelligente
- [ ] Implementare decision graph con routing condizionale:
  ```python
  def create_atlas_graph():
      workflow = StateGraph(AtlasState)
      
      # Add phase nodes
      workflow.add_node("investigate", InvestigationAgent())
      workflow.add_node("discuss", DiscussionAgent())
      workflow.add_node("plan", PlanningAgent())
      workflow.add_node("generate", TaskGenerationAgent())
      
      # Add conditional routing
      workflow.add_conditional_edges(
          "investigate",
          lambda x: "discuss" if x["investigation_complete"] else "investigate"
      )
      
      return workflow.compile()
  ```
- [ ] Aggiungere validation nodes per quality cycles
- [ ] Enable parallel processing per repository analysis

#### Success Criteria:
- StateGraph funzionante con routing intelligente
- Possibilità di quality cycles (investigation → discussion → investigation)
- Parallel repository analysis attivo

### 1.3 Decomporre God Class ⏳
**Status**: Not Started  
**Files da creare**: `agents/` directory con agent modulari  
**Files da modificare**: `atlas_agent.py`

#### Tasks:
- [ ] Estrarre agent classes separate:
  - [ ] `agents/investigation_agent.py`
  - [ ] `agents/discussion_agent.py`
  - [ ] `agents/planning_agent.py`
  - [ ] `agents/task_generation_agent.py`
- [ ] Creare `AtlasCoordinator` snello (< 100 linee)
- [ ] Rimuovere metodi da `AtlasAgentV1` god class
- [ ] Implementare hierarchical sub-agents pattern

#### Success Criteria:
- Nessuna classe > 200 linee
- Ogni agent con single responsibility
- Coordinatore focalizzato solo su orchestration

---

## FASE 2: Tool Simplification (Priorità 3)
**Timeline**: Settimana 3  
**Obiettivo**: Semplificare tool implementation allineandola a DeepAgents patterns

### 2.1 Eliminare MCPToolsWrapper Complexity ⏳
**Status**: Not Started  
**Files da modificare**: `mcp_tools.py`, `atlas_tools.py`  
**File da creare**: `mcp_tools_simple.py`

#### Tasks:
- [ ] Sostituire MCPToolsWrapper (368 linee) con funzioni dirette
- [ ] Creare semplici decoratori @tool per MCP tools:
  ```python
  @tool
  def list_projects(state: Annotated[AtlasState, InjectedState]) -> Command:
      """List all projects from MCP"""
      projects = mcp_client.list_projects()
      return Command(
          update={"projects": projects}
      )
  ```
- [ ] Rimuovere complex mapping logic
- [ ] Eliminare retry decorators non necessari

#### Success Criteria:
- Nessuna wrapper class
- Tools < 20 linee ciascuno
- Direct invocation pattern

### 2.2 Implementare Proper Tool Patterns ⏳
**Status**: Not Started  
**Files da modificare**: `atlas_tools.py`

#### Tasks:
- [ ] Convertire tools esistenti a pattern corretto:
  ```python
  @tool
  def human_input(
      question: str,
      state: Annotated[DeepAgentState, InjectedState],
      tool_call_id: Annotated[str, InjectedToolCallId]
  ) -> Command:
      """Get input from user with proper state injection"""
      return Command(
          update={"pending_input": question},
          goto=["human"]  # For interrupt handling
      )
  ```
- [ ] Implementare state injection ovunque
- [ ] Usare `Command` objects per tutti gli updates
- [ ] Seguire research example patterns

#### Success Criteria:
- Tutti i tools usano `InjectedState`
- Tutti ritornano `Command` objects
- Nessun manual state passing

---

## FASE 3: Integration & Optimization
**Timeline**: Settimana 4  
**Obiettivo**: Completare integrazione e ottimizzazione

### 3.1 Prompt Simplification ⏳
**Status**: Not Started  
**Files da modificare**: `prompts.py`, `subagents.py`

#### Tasks:
- [ ] Ridurre ORCHESTRATOR_PROMPT_TEMPLATE da 325 a ~50 linee
- [ ] Ridurre INVESTIGATION_AGENT_PROMPT_TEMPLATE da 525+ a ~50 linee
- [ ] Eliminare complex template variables (13+ vars)
- [ ] Rimuovere `format_agent_prompt()` (405 linee)
- [ ] Embed tool descriptions direttamente nei prompts

#### Success Criteria:
- Nessun prompt > 50 linee
- Nessun template system complesso
- Prompts chiari e concisi

### 3.2 Framework Integration ⏳
**Status**: Not Started  
**Files da modificare**: `atlas_agent.py`

#### Tasks:
- [ ] Usare standard `create_deep_agent()` pattern:
  ```python
  agent = create_deep_agent(
      tools=[...],
      instructions=atlas_instructions,
      subagents=[investigation_agent, discussion_agent, ...]
  ).with_config({"recursion_limit": 1000})
  ```
- [ ] Rimuovere `_create_orchestrator()` custom (70+ linee)
- [ ] Implementare proper subagents configuration
- [ ] Aggiungere configuration migration per backward compatibility

#### Success Criteria:
- Uso diretto di `create_deep_agent()`
- Nessuna custom orchestration logic
- Clean framework usage

### 3.3 Testing & Validation ⏳
**Status**: Not Started  
**Files da creare**: `tests/` directory completa

#### Tasks:
- [ ] Unit tests per ogni sub-agent
- [ ] Integration tests per decision graph
- [ ] End-to-end tests per complete flow
- [ ] Performance benchmarks:
  - [ ] Lines of code reduction
  - [ ] Context window usage
  - [ ] Execution speed
  - [ ] State consistency

#### Success Criteria:
- Test coverage > 80%
- All tests passing
- Performance metrics documented

---

## Risk Mitigation

### Backward Compatibility
- [ ] Mantenere public API surface identica
- [ ] Creare migration guide
- [ ] Feature flags per gradual rollout
- [ ] Supporto parallel deployment

### Quality Assurance
- [ ] Progressive refactoring (non tutto insieme)
- [ ] Comprehensive test coverage
- [ ] Performance monitoring ad ogni step
- [ ] Rollback procedures documentate

---

## Expected Outcomes

| Metric | Current | Target | Reduction |
|--------|---------|--------|-----------|
| Lines of Code | 2000+ | 400 | -80% |
| Prompt Complexity | 400-500 lines | 30-50 lines | -90% |
| State Systems | 2 (dual) | 1 (unified) | -50% |
| Tool Wrapper | 368 lines | 0 (direct) | -100% |
| God Class Size | 870 lines | <100 lines | -88% |

## Success Metrics

- **Code Complexity**: Cyclomatic complexity < 10 per function
- **Performance**: Phase transitions < 100ms, context usage -50%
- **Reliability**: Zero state sync issues, atomic updates only
- **Maintainability**: Test coverage > 80%, framework aligned
- **Extensibility**: New phases addable in < 50 lines

---

## Next Steps

1. **Immediate**: Review questo piano con il team
2. **Week 1**: Iniziare con Phase 1.1 (State Management)
3. **Daily**: Update status in questo documento
4. **Weekly**: Review progress e adjust timeline

---

## References

- [Atlas V1 DeepAgents Alignment Analysis](/specs/atlas-v1-deepagents-alignment-analysis.md)
- [Research Example](/examples/research/research_agent.py) - 167 lines best practice
- [DeepAgents Core](/src/deepagents/) - Framework documentation

---

**Last Updated**: 2025-08-22  
**Status**: Planning Phase  
**Owner**: Development Team