# 1. CRITERIO HIDRÁULICO DE MONTANTES VERTICALES

En el diseño hidrosanitario de edificaciones, las **columnas montantes verticales matrices** deben dimensionarse con una **velocidad aproximada menor** ($V_{\text{aprox}} = 1.20\text{ a }1.50\text{ m/s}$) para proteger la presión residual en el último nivel.

$$
d_{\text{calc}} = \sqrt{\frac{4 \cdot Q}{\pi \cdot V_{\text{aprox}}}} \cdot 1000 \quad [\text{mm}]
$$

## 1.1 ANEXO A: DIAGRAMA LÓGICO DE SELECCIÓN EN MERMAID

### 1.1.1 Secuencia algorítmica validada sin barras de desplazamiento

```mermaid
graph TD
    A["Inicio: Cargar Caudal Q_k de la Montante"] --> B["Asignar V_aprox = 1.20 a 1.50 m/s"]
    B --> C["Calcular d_calc = SQRT(4*Q / (PI * V_aprox)) * 1000 [mm]"]
    C --> D{"¿Velocidad Real V_real <= 2.00 m/s?"}
    D -->|Sí: Conforme| E["🟢 TRAMO MONTANTE Y DIÁMETRO VALIDADO"]
    D -->|No: Exceso| F["🔴 RECALIBRAR: Aumentar Diámetro Comercial"]
    style E fill:#e2efda,stroke:#2b9348,stroke-width:2px
    style F fill:#f8d7da,stroke:#ff5555,stroke-width:1.5px
    style A fill:#dce6f1,stroke:#4472c4,stroke-width:1.5px
```
