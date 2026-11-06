```mermaid
graph TD
    A["Inicio: Salida del Medidor Individual en PB (Presión P_inicio)"] --> B["Identificar Unidades de Gasto Totales SUM(P) de los Pisos Superiores"]
    B --> C["Calcular Caudal Inicial de la Montante Q_base = C * SQRT(SUM P_total)"]
    
    C --> D["Dimensionar Diámetro Base d_base para Velocidad V <= 2.50 m/s"]
    D --> E{"¿Edificación de Baja Altura (3 a 4 Pisos)?"}
    
    E -->|Sí: Opción Recomendada| F["SELECCIONAR DIÁMETRO UNIFORME: Mantener d_base en Toda la Altura Vertical"]
    E -->|No: Edificio Alto| G["EVALUAR TELESCOPÍA: Calcular d_k según SUM(P) remanente en Piso k"]
    
    F --> H["Iniciar Balance Piezométrico Ascendente desde Piso 1 hasta Piso N"]
    G --> H
    
    H --> I["Tramo k: Sumar Desnivel Geometrico Delta_z = z_k - z_PB (1.00 mca/m)"]
    I --> J["Tramo k: Calcular Pérdida por Fricción y Accesorios hf_k = j_k * L_tot"]
    
    J --> K["Calcular Presión Disponible: P_disp,k = P_inicio - SUM(hf) - Delta_z_k"]
    K --> L{"¿Presión P_disp,k >= P_mínimo Requerido (5.0 mca / 15.0 mca)?"}
    
    L -->|Sí: Conforme| M["🟢 TRAMO DE MONTANTE VALIDADO Y APROBADO"]
    L -->|No: Deficitario| N["🔴 ALERTA: Incrementar Diámetro de Montante o Diseñar Presurización"]

    style M fill:#e2efda,stroke:#2b9348,stroke-width:2px
    style N fill:#f8d7da,stroke:#ff5555,stroke-width:1.5px
    style A fill:#dce6f1,stroke:#4472c4,stroke-width:1.5px
    style B fill:#ececec,stroke:#595959,stroke-width:1.5px
    style C fill:#ececec,stroke:#595959,stroke-width:1.5px
    style D fill:#ececec,stroke:#595959,stroke-width:1.5px
    style F fill:#ececec,stroke:#595959,stroke-width:1.5px
    style G fill:#ececec,stroke:#595959,stroke-width:1.5px
    style H fill:#ececec,stroke:#595959,stroke-width:1.5px
    style I fill:#ececec,stroke:#595959,stroke-width:1.5px
    style J fill:#ececec,stroke:#595959,stroke-width:1.5px
    style K fill:#ececec,stroke:#595959,stroke-width:1.5px
