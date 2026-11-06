**MEMORIA TÉCNICA DE PRUEBA — SALTOS DE CAPÍTULO (FASE 3)**

Introducción breve del documento. Este bloque precede al primer capítulo y, por la excepción de primera hoja, debe compartir la Hoja 1 con el capítulo «1.».

# 1. Primer capítulo

Texto del primer capítulo, con **negrita** y una fórmula en línea $Q = V \cdot A$.

## 1.1 Caudal de diseño

Contenido del subtítulo 1.1.

---

## 1.2 Velocidades admisibles

Contenido del subtítulo 1.2 (precedido de un separador `---`, que no debe generar salto).

# 2. Segundo capítulo

Este capítulo debe iniciar en una hoja nueva.

## 2.1 Pérdidas de carga

Contenido del subtítulo 2.1.

---

## 2.2 Presiones residuales

Contenido del subtítulo 2.2.

# 3. Tercer capítulo

Este capítulo debe iniciar en una hoja nueva e incluye el diagrama del Anexo A, que no debe quedar roto por el salto.

```mermaid
graph TD
classDef startFill fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
classDef calcFill fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
classDef outFill fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
classDef normFill fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40;

A[Efluente Domestico Rural: Pf = 250 hab, Q = 28 m3/d]:::startFill --> B[Pretratamiento: Fosa Septica 2 Camaras]:::calcFill
B --> C[Efluente Clarificado: Carga = 9.0 kg DBO5/d]:::calcFill
C --> D{Seleccion de Tecnologia de Humedal}:::startFill
D -- Opcion 1: Gravedad --> E[Humedal Horizontal HCFSH]:::outFill
D -- Opcion 2: Sifon --> F[Camara Sifon + Humedal Vertical HCFV]:::outFill
D -- Opcion 3: Bombeo --> G[Camara Estanque + 2 Bombas + Humedal Vertical HCFV]:::outFill
E --> H[Efluente HCFSH: DBO5 = 29.8 mg/L]:::normFill
F --> I[Efluente HCFV Sifon: DBO5 = 20.0 mg/L]:::normFill
G --> J[Efluente HCFV Bombeo: DBO5 = 20.0 mg/L]:::normFill
H --> K[Cuerpo Receptor: Cumple TULSMA]:::outFill
I --> K
J --> K
```

