
```mermaid
flowchart TB
    A["Usuario / OpenCode CLI"] -- Invoca comando --> B("Orchestrator Agent")
    B -- Planifica subtareas --> C["Background Subagents"]
    C -- Explorer --> D["Búsqueda AST / Código"]
    C -- Librarian --> E["Recuperación de Docs / MCP"]
    C -- Oracle --> F["Asesoría Arquitectónica"]
    D --> G["Reconciliación de Resultados"]
    E --> G
    F --> G
    G --> H["Salida Final al Desarrollador"]