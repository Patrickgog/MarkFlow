# Memoria Técnica de Tratamiento de Aguas Residuales Rurales

## 1. Introducción y Parámetros de Diseño

El presente documento evalúa las alternativas técnicas y dimensionamiento preliminar para el tratamiento biológico de efluentes domésticos rurales correspondientes a una población de diseño de **Pf = 250 habitantes**, con una dotación neta de agua potable estimada y un caudal medio residual de **Q = 28 m³/d**.

El objetivo primordial consiste en garantizar una remoción de carga orgánica expresada como $\text{DBO}_5$ superior al 90%, alcanzando concentraciones efluentes compatibles con los límites permisibles del marco regulatorio ambiental (TULSMA Tabla 3 $\le 100\text{ mg/L de DBO}_5$).

## 2. Diagrama de Flujo y Selección de Tecnología (Anexo A)

A continuación se presenta el esquema metodológico de tratamiento unifilar correspondiente al sistema primario y secundario mediante humedales construidos:

```mermaid
graph TD
classDef startFill fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
classDef calcFill fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
classDef outFill fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
classDef normFill fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40;

A[Efluente Doméstico Rural: Pf = 250 hab | Q = 28 m3/d] :::startFill --> B[Pretratamiento: Fosa Séptica 2 Cámaras CO 10-602 | Vol = 35 m3] :::calcFill
B --> C[Efluente Clarificado: Carga = 9.0 kg DBO5/d | Conc = 321.4 mg/L] :::calcFill
C --> D{Selección de Tecnología de Humedal} :::startFill

D -- Opción 1: Gravedad / Sifón --> E[Humedal Horizontal HCFSH | As = 500 m2 | Grava 10-20mm] :::outFill
D -- Opción 2: Sifón Autosifonante --> F[Cámara Sifón 3.5 m3 + Humedal Vertical HCFV | As = 750 m2] :::outFill
D -- Opción 3: Impulsión Electromecánica --> G[Cámara Estanque 3.5 m3 + 2 Bombas 1.5 HP + Humedal Vertical HCFV | As = 750 m2] :::outFill

E --> H[Efluente HCFSH: DBO5 = 29.8 mg/L | Remoción = 93.8%] :::normFill
F --> I[Efluente HCFV Sifón: DBO5 = 20.0 mg/L | Remoción = 95.8%] :::normFill
G --> J[Efluente HCFV Bombeo: DBO5 = 20.0 mg/L | Remoción = 95.8%] :::normFill

H --> K[Cuerpo Receptor Dulce / Riego:Cumple TULSMA Tabla 3 <= 100 mg/L DBO5] :::outFill
I --> K
J --> K
```

## 3. Discusión de Eficiencia y Figuras Flotantes

<div class="figura-flotante-der">
  <img src="/static/img/favicon.svg" alt="Isotipo MarkFlow" width="160" />
  <p class="epigrafe-figura">Figura 1. Esquema de control de calidad institucional MarkFlow.</p>
</div>

La selección de humedales artificiales subsuperficiales de flujo horizontal (HCFSH) versus humedales de flujo vertical (HCFV) responde a factores orográficos, disponibilidad de gradiente hidráulico y costos operativos. 

En situaciones donde no existe suministro eléctrico continuo en comunidades rurales aisladas, la **Opción 1** por gravedad estricta o sifonamiento pasivo minimiza la vulnerabilidad operativa eliminando grupos electrógenos y costos de bombeo electromecánico. Como se aprecia en la figura flotante de la derecha, el texto envuelve de manera armoniosa y continua los márgenes del bloque visual sin desbordar el diseño ni ocasionar cortes anómalos.

### 3.1 Resumen Comparativo de Alternativas

| Parámetro | Pretratamiento | Humedal Horizontal (HCFSH) | Humedal Vertical (HCFV) |
| :--- | :---: | :---: | :---: |
| Área Superficial ($A_s$) | 35 m³ (Vol) | 500 m² | 750 m² |
| Carga Orgánica $\text{DBO}_5$ | 321.4 mg/L | 29.8 mg/L | 20.0 mg/L |
| Eficiencia de Remoción | ~35% | 93.8% acumulada | 95.8% acumulada |
| Mantenimiento Requerido | Desazolve bianual | Podas trimestrales | Limpieza sifones mensual |
