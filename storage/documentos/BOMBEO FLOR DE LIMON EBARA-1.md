---

## title: "MEMORIA TÉCNICA DE DISEÑO — SISTEMA DE BOMBEO" author: "AquaPulse Pump Studio Cloud" date: "29/10/2026" tipo: "Aguas Claras / Potable"

# MEMORIA TÉCNICA DE DISEÑO

### SISTEMA DE BOMBEO — Aguas Claras / Potable

|   |   |
|---|---|
| **Proyecto:** | BOMBEO FLOR DE LIMON-EBARA |
| **Diseño:** | ING. PATRICIO SARMIENTO REINOSO |
| **Provincia:** | MORONA SANTIAGO |
| **Cantón:** | LIMON INDANZA |
| **Localidad:** | FLOR DE LIMON |
| **Fecha:** | 29/10/2026 |
| **Tipo de Agua:** | Aguas Claras / Potable |
| "El diseño de sistemas de bombeo debe garantizar la continuidad del servicio, la eficiencia energética y la protección del equipo contra fenómenos transitorios como el golpe de ariete." |   |
| — *Norma ANSI/HI 9.6.1-2012, Rotodynamic Pumps — Guideline for NPSH Margin* |   |

 ![imagen-pegada][img-1]

# 1. INTRODUCCIÓN Y ALCANCE

## 1.1 Objeto del Documento

El presente documento constituye la **memoria técnica de diseño** del sistema de bombeo correspondiente al proyecto **BOMBEO FLOR DE LIMON-EBARA**. Su objeto es definir y justificar los parámetros hidráulicos, la selección de equipos y las condiciones de operación del sistema, cumpliendo con las normas técnicas nacionales e internacionales aplicables.

## 1.2 Alcance

Este informe abarca:

- Determinación del **caudal de diseño** del sistema
- Cálculo de la **altura dinámica total (ADT)**
- Selección del **diámetro óptimo** de tubería de impulsión
- **Análisis de pérdidas de carga** en succión e impulsión
- Verificación del **NPSH disponible** según ANSI/HI 9.6.1
- **Selección del equipo de bombeo** y motor eléctrico
- Análisis de **variador de frecuencia (VFD)** (si aplica)
- Estudio de **transientes hidráulicos** (golpe de ariete)
- **Optimización económica** del diámetro de impulsión

## 1.3 Normativa Aplicable

- **ANSI/HI 9.6.1-2012** — NPSH Margin Guideline
- **ANSI/HI 9.6.3-2012** — Rotodynamic Pumps for Vibration Measurement
- **ANSI/HI 9.8-2012** — Rotodynamic Pumps — Pump Intake Design
- **ANSI/HI 14.3-2013** — Rotodynamic Pumps for Hydraulic Performance
- **NFPA 20** — Standard for the Installation of Stationary Pumps for Fire Protection
- **AWWA M11** — Steel Pipe — A Guide for Design and Installation
- **AWWA M51** — Air Release, Air/Vacuum & Combination Air Valves
- **ISO 9906:2012** — Rotodynamic pumps — Hydraulic performance acceptance tests (Grades 1, 2 and 3)
- **ISO 13709:2009** — Centrifugal pumps for petroleum, petrochemical and natural gas industries (API 610)
- **NEMA MG-1-2018** — Motors and Generators
- **IEC 60034-30-1:2014** — Rotating electrical machines — Efficiency classes (IE1, IE2, IE3, IE4)
- **UNE-EN 752:2017** — External drainage and sewerage systems
- **UNE-EN 16932:2018** — Pumping systems for drainage and sewerage

---

# 2. DATOS DEL PROYECTO

## 2.1 Información General

| Parámetro | Valor | Unidad |
|---|---|---|
| Nombre del Proyecto | BOMBEO FLOR DE LIMON-EBARA | — |
| Diseñador / Responsable | ING. PATRICIO SARMIENTO REINOSO | — |
| Ubicación | MORONA SANTIAGO, LIMON INDANZA, FLOR DE LIMON | — |
| Tipo de Agua | Aguas Claras / Potable | — |
| Elevación del Sitio | 1214.50 | msnm |
| Aceleración de la Gravedad | 9.81 | m/s² |
| Fecha de Emisión | 29/10/2026 | — |

## 2.2 Condiciones de Operación

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Caudal de Diseño | *Q* | 2.00 | L/s |
| Caudal de Diseño | *Q* | 7.20 | m³/h |
| Número de Bombas en Operación | *N* | 1 | und |
| Caudal por Bomba | *Q<sub>b</sub>* | - | L/s |
| Altura de Succión | *h<sub>s</sub>* | 2.00 | m |
| Altura de Descarga | *h<sub>d</sub>* | 144.00 | m |
| Altura Estática Total | *H<sub>e</sub>* | 142.00 | m |
| Altura Dinámica Total (ADT) | *ADT* | 180.04 | m |
| Temperatura del Líquido | *T* | 25.0 | °C |
| Densidad del Líquido | *ρ* | 1.0 | kg/m³ |
| Viscosidad Cinemática del Agua a 25.0°C | *ν* | 1.004 × 10⁻⁶ | m²/s |
| Condición de Succión | — | Bomba Inundada | — |

## 2.3 Parámetros Ambientales

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Presión Barométrica | *P<sub>atm</sub>* | 8.67 | kPa |
| Presión de Vapor a 25.0°C | *P<sub>v</sub>* | 0.24 | kPa |
| Peso Específico del Agua | *γ* | 9.81 | kN/m³ |

[nota: La presión barométrica se calcula según la elevación del sitio mediante la ecuación hipsométrica estándar. La presión de vapor se determina con la correlación de Antoine para el agua en función de la temperatura de operación.]

---

# 3. CRITERIOS DE DISEÑO HIDRÁULICO

## 3.1 Número de Reynolds y Régimen de Flujo

El **número de Reynolds** determina el régimen de flujo dentro de la tubería y se calcula como:

$$ Re = \frac{\rho \cdot v \cdot D}{\mu} = \frac{v \cdot D}{\nu} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *Re* | Número de Reynolds (adimensional) | — |
| *ρ* | Densidad del fluido | kg/m³ |
| *v* | Velocidad media del flujo | m/s |
| *D* | Diámetro interno de la tubería | m |
| *μ* | Viscosidad dinámica del fluido | Pa·s |
| *ν* | Viscosidad cinemática (μ/ρ) | m²/s |

**Clasificación del régimen de flujo:**

| Régimen | Rango de Reynolds | Características |
|---|---|---|
| **Laminar** | *Re* < 2 000 | Flujo ordenado por capas, pérdidas proporcionales a *v* |
| **Transición** | 2 000 ≤ *Re* ≤ 4 000 | Zona crítica, comportamiento inestable |
| **Turbulento liso** | 4 000 < *Re* ≤ 10⁵ | Subcapa viscosa domina la fricción |
| **Turbulento rugoso** | *Re* > 10⁵ | Rugosidad de pared domina la fricción |

[nota: En sistemas de bombeo de agua, el flujo es típicamente turbulento (Re > 10⁵), lo que justifica el uso de ecuaciones como Hazen-Williams o Darcy-Weisbach con el diagrama de Moody.]

## 3.2 Ecuación de Hazen-Williams (Método Estándar)

Para el cálculo de las pérdidas por fricción en tuberías a presión se utiliza la **fórmula empírica de Hazen-Williams**, ampliamente aceptada para flujo de agua en tuberías a presión:

$$ hf = 10.67 \times L \times \frac{Q^{1.852}}{C^{1.852} \times D^{4.871}} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *hf* | Pérdida de carga por fricción | m |
| *L* | Longitud del tramo de tubería | m |
| *Q* | Caudal circulante | m³/s |
| *C* | Coeficiente de rugosidad de Hazen-Williams | adimensional |
| *D* | Diámetro interno de la tubería | m |

**Coeficientes *****C*** de Hazen-Williams para distintos materiales:

| Material | *C* (nuevo) | *C* (10 años) | *C* (20 años) |
|---|---|---|---|
| PVC (policloruro de vinilo) | 150 | 148 | 145 |
| PEAD (polietileno de alta densidad) | 150 | 148 | 145 |
| Hierro dúctil con revestimiento cemento | 140 | 130 | 120 |
| Hierro dúctil sin revestimiento | 130 | 110 | 90 |
| Acero al carbono nuevo | 140 | 120 | 100 |
| Acero galvanizado | 120 | 100 | 80 |
| Hormigón armado | 130 | 120 | 110 |
| Fibrocemento | 140 | 135 | 130 |
| Cobre | 140 | 135 | 130 |
| **Fuente:** *AWWA M11 — Steel Pipe Design Guide* y *McGhee, T.J., Water Supply and Sewerage, 6th Ed., McGraw-Hill, 1991.* |   |   |   |

## 3.3 Ecuación de Darcy-Weisbach con Colebrook-White (Método Universal)

La **ecuación de Darcy-Weisbach** es válida para cualquier fluido, régimen de flujo y temperatura, y se considera el método universal para el cálculo de pérdidas por fricción:

$$ hf = f \times \frac{L}{D} \times \frac{v^{2}}{2g} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *f* | Factor de fricción de Darcy (adimensional) | — |
| *L* | Longitud de la tubería | m |
| *D* | Diámetro interno | m |
| *v* | Velocidad media del flujo | m/s |
| *g* | Aceleración de la gravedad (9.81) | m/s² |

El **factor de fricción *****f*** se obtiene de la **ecuación de Colebrook-White**, que relaciona el número de Reynolds y la rugosidad relativa de la tubería:

$$ \frac{1}{\sqrt{f}} = -2 \cdot \log_{10}\left( \frac{\varepsilon/D}{3.7} + \frac{2.51}{Re \cdot \sqrt{f}} \right) $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *ε* | Rugosidad absoluta de la pared interna de la tubería | mm |
| *ε/D* | Rugosidad relativa (adimensional) | — |
| *Re* | Número de Reynolds | — |

**Rugosidad absoluta *****ε*** para materiales comunes:

| Material | *ε* (mm) |
|---|---|
| PVC y PEAD (lisos) | 0.0015 – 0.0070 |
| Hierro dúctil con revestimiento | 0.030 – 0.100 |
| Acero comercial nuevo | 0.045 – 0.090 |
| Acero galvanizado | 0.100 – 0.150 |
| Hierro fundido nuevo | 0.250 – 0.800 |
| Hierro fundido con incrustaciones | 1.000 – 3.000 |
| Hormigón armado | 0.300 – 3.000 |
| **Fuente:** *Moody, L.F., "Friction Factors for Pipe Flow", Transactions of the ASME, Vol. 66, 1944.* |   |

## 3.4 Velocidades Recomendadas en Tuberías

**Criterio de velocidad:** La velocidad del flujo en tuberías de impulsión debe mantenerse dentro de los rangos recomendados para evitar sedimentación, erosión y golpe de ariete, según las normas aplicables.

**Velocidades recomendadas por aplicación:**

| Tipo de Sistema | Velocidad Mínima (m/s) | Velocidad Óptima (m/s) | Velocidad Máxima (m/s) | Norma de Referencia |
|---|---|---|---|---|
| Agua potable — Impulsión | 0.60 | 1.20 – 1.80 | 2.50 | AWWA M11 |
| Agua potable — Succión | 0.60 | 0.90 – 1.50 | 2.00 | ANSI/HI 9.8 |
| Aguas residuales — Impulsión | 0.90 | 1.50 – 2.50 | 3.00 | EN 16932 |
| Aguas residuales — Succión | 0.75 | 1.20 – 2.00 | 2.50 | ANSI/HI 9.8 |
| Aguas pluviales | 0.75 | 1.20 – 2.00 | 3.00 | UNE-EN 752 |
| Lodos (2-5% sólidos) | 1.20 | 1.80 – 2.50 | 3.50 | WEF MOP FD-4 |

[nota: Velocidades inferiores a la mínima recomendada pueden causar sedimentación de sólidos en suspensión. Velocidades superiores a la máxima incrementan la erosión, el ruido hidráulico y el riesgo de golpe de ariete.]

## 3.5 Pérdidas Localizadas en Accesorios

Las pérdidas en accesorios (válvulas, codos, tes, reducciones, etc.) se calculan mediante el **método de coeficiente *****K***:

$$ h_{acc} = K \times \frac{v^{2}}{2g} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *h<sub>acc</sub>* | Pérdida de carga en el accesorio | m |
| *K* | Coeficiente de pérdida localizada (adimensional) | — |
| *v* | Velocidad media en el accesorio | m/s |
| *g* | Aceleración de la gravedad | m/s² |

**Coeficientes *****K*** típicos para accesorios comunes:

| Accesorio | *K* (roscado) | *K* (bridado) |
|---|---|---|
| Válvula de compuerta (100% abierta) | 0.15 | 0.10 |
| Válvula de compuerta (75% abierta) | 0.85 | 0.60 |
| Válvula de compuerta (50% abierta) | 4.40 | 3.50 |
| Válvula de mariposa (100% abierta) | — | 0.25 |
| Válvula de retención (check) tipo clapeta | 2.50 | 1.50 |
| Válvula de retención (check) tipo bola | 0.70 | 0.50 |
| Válvula de globo (100% abierta) | 8.00 | 5.00 |
| Válvula de pie con coladera | — | 3.00 |
| Codo 90° radio largo (r/D = 1.5) | 0.60 | 0.30 |
| Codo 90° radio corto (r/D = 1.0) | 0.90 | 0.45 |
| Codo 45° | 0.40 | 0.20 |
| Te — flujo directo | 0.60 | 0.30 |
| Te — flujo derivado | 1.30 | 0.75 |
| Curva 90° (r/D = 2.5) | 0.40 | 0.20 |
| Reducción gradual (expansión, d/D = 0.5) | 0.25 | 0.15 |
| Reducción gradual (contracción, d/D = 0.5) | 0.10 | 0.05 |
| Ampliación brusca (d/D = 0.5) | 0.55 | 0.40 |
| **Fuente:** *Crane Technical Paper No. 410, "Flow of Fluids Through Valves, Fittings, and Pipe", 2018 Edition.* |   |   |

## 3.6 Altura Dinámica Total (ADT)

La **Altura Dinámica Total** del sistema de bombeo se define como la suma de todos los componentes de carga que la bomba debe vencer:

$$ ADT = H_{estática} + \sum hf_{succión} + \sum hf_{impulsión} + \sum h_{acc} + h_{velocidad} $$

**Donde:**

| Componente | Descripción |
|---|---|
| *H<sub>estática</sub>* | Diferencia de nivel entre la superficie libre de succión y el punto de descarga más elevado |
| *∑hf<sub>succión</sub>* | Pérdidas por fricción en la tubería de succión (Darcy-Weisbach o Hazen-Williams) |
| *∑hf<sub>impulsión</sub>* | Pérdidas por fricción en la tubería de impulsión |
| *∑h<sub>acc</sub>* | Pérdidas totales en accesorios (succión + impulsión) |
| *h<sub>velocidad</sub>* | Carga de velocidad en la descarga (usualmente despreciable, *v²/2g*) |

[nota: En la mayoría de los diseños prácticos, la carga de velocidad *h<sub>velocidad</sub>* es inferior a 0.3 m y puede considerarse despreciable frente al resto de componentes.]

---

# 4. ANÁLISIS DE TUBERÍAS

## 4.1 Tubería de Succión

[Imagen: Diagrama esquemático de la tubería de succión con cotas y accesorios]

### 4.1.1 Especificaciones Técnicas

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Material | — | PVC | — |
| Diámetro Nominal (DN) | *DN* | 56.5 | mm |
| Diámetro Interno | *D<sub>s</sub>* | 56.5 | mm |
| Área Transversal | *A<sub>s</sub>* | π × (D<sub>s</sub>/2)² | mm² |
| Longitud Total | *L<sub>s</sub>* | 5.0 | m |
| Coeficiente de Rugosidad C (Hazen-Williams) | *C<sub>s</sub>* | - | — |
| Velocidad Media del Flujo | *v<sub>s</sub>* | 0.80 | m/s |
| Número de Reynolds | *Re<sub>s</sub>* | (calculado) | — |

### 4.1.2 Pérdidas de Carga

| Tipo de Pérdida | Símbolo | Valor | Unidad |
|---|---|---|---|
| Pérdida Primaria (fricción) | *hf<sub>s,prim</sub>* | - | m |
| Pérdida Secundaria (accesorios) | *hf<sub>s,sec</sub>* | - | m |
| **Pérdida Total en Succión** | ***hf<sub>s,total</sub>*** | **-** | **m** |

[nota: Para bombas en configuración de succión positiva (bomba inundada), la pérdida total en la tubería de succión debe ser la menor posible. Se recomienda que no supere **0.5 m** para evitar problemas de cavitación.]

## 4.2 Tubería de Impulsión

[Imagen: Perfil longitudinal de la tubería de impulsión con puntos singulares]

### 4.2.1 Especificaciones Técnicas

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Material | — | PEAD | — |
| Diámetro Nominal (DN) | *DN* | 38.8 | mm |
| Diámetro Interno | *D<sub>i</sub>* | 38.8 | mm |
| Área Transversal | *A<sub>i</sub>* | π × (D<sub>i</sub>/2)² | mm² |
| Longitud Total | *L<sub>i</sub>* | 485.0 | m |
| Coeficiente de Rugosidad C (Hazen-Williams) | *C<sub>i</sub>* | - | — |
| Velocidad Media del Flujo | *v<sub>i</sub>* | 1.69 | m/s |
| Número de Reynolds | *Re<sub>i</sub>* | (calculado) | — |

### 4.2.2 Pérdidas de Carga

| Tipo de Pérdida | Símbolo | Valor | Unidad |
|---|---|---|---|
| Pérdida Primaria (fricción) | *hf<sub>i,prim</sub>* | - | m |
| Pérdida Secundaria (accesorios) | *hf<sub>i,sec</sub>* | - | m |
| **Pérdida Total en Impulsión** | ***hf<sub>i,total</sub>*** | **-** | **m** |
| **Criterio de diseño:** La pérdida de carga total en la tubería de impulsión no debe superar el **15% de la altura dinámica total** para garantizar una operación energéticamente eficiente (ANSI/HI 14.3-2013). |   |   |   |

### 4.2.3 Selección del Diámetro Óptimo

La selección del diámetro óptimo de la tubería de impulsión responde a un equilibrio entre el **costo de inversión** (tubería de mayor diámetro es más costosa) y el **costo operativo** (tubería de menor diámetro genera mayores pérdidas y, por tanto, mayor consumo energético).

$$ D_{óptimo} \approx 1.2 \times Q^{0.5} \quad (\text{Bresse, para Q en m³/s}) $$

| Diámetro Seleccionado | - | mm |
|---|---|---|

---

# 5. ANÁLISIS DE NPSH Y PREVENCIÓN DE CAVITACIÓN

## 5.1 Concepto de NPSH

El **NPSH (Net Positive Suction Head)** es un parámetro crítico que determina si la bomba operará sin cavitación. La cavitación ocurre cuando la presión absoluta del fluido en la brida de succión cae por debajo de la presión de vapor, formando burbujas que colapsan violentamente al pasar a zonas de mayor presión, causando erosión, ruido y pérdida de rendimiento.

## 5.2 NPSH Disponible (NPSH<sub>d</sub>)

El NPSH disponible depende exclusivamente de las condiciones del sistema (no de la bomba) y se calcula como:

$$ NPSH_{d} = \frac{P_{atm}}{\gamma} - h_{s} - hf_{s} - \frac{P_{v}}{\gamma} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *P<sub>atm</sub>* | Presión atmosférica en la superficie libre del pozo de succión | kPa |
| *γ* | Peso específico del fluido (ρ × g) | kN/m³ |
| *h<sub>s</sub>* | Altura geométrica de succión (positiva si el nivel de agua está por encima del eje de la bomba) | m |
| *hf<sub>s</sub>* | Pérdida de carga total en la línea de succión | m |
| *P<sub>v</sub>* | Presión de vapor del líquido a la temperatura de operación | kPa |

## 5.3 Velocidad Específica de Succión (N<sub>ss</sub>)

La **velocidad específica de succión** es un parámetro adimensional que caracteriza el diseño del ojo del impulsor y su capacidad de operar cerca de la cavitación:

$$ N_{ss} = \frac{N \times \sqrt{Q}}{NPSH_{r}^{0.75}} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *N<sub>ss</sub>* | Velocidad específica de succión (adimensional) | — |
| *N* | Velocidad de giro de la bomba | RPM |
| *Q* | Caudal en el punto de máxima eficiencia (BEP) | m³/s |
| *NPSH<sub>r</sub>* | NPSH requerido en el BEP | m |
| **Criterio ANSI/HI 9.6.1:** Para bombas centrifugas, se recomienda *N<sub>ss</sub>* no mayor a 11 000 (en unidades US: 220). Valores superiores indican diseños de impulsor más exigentes y menor tolerancia a la cavitación. |   |   |

## 5.4 Resultados del Análisis

| Parámetro | Símbolo | Valor | Unidad | Estado |
|---|---|---|---|---|
| NPSH Disponible (sistema) | *NPSH<sub>d</sub>* | **9.92** | m | — |
| NPSH Requerido (bomba en BEP) | *NPSH<sub>r</sub>* | **3.20** | m | — |
| **Margen de Seguridad** | **ΔNPSH** | **6.72** | **m** | 6.72 |

[nota: El margen de seguridad ΔNPSH = NPSH<sub>d</sub> – NPSH<sub>r</sub>. La mayoría de fabricantes recomiendan un margen mínimo de **1.0 m** o **10% sobre NPSH<sub>r</sub>**, el valor que sea mayor, según ANSI/HI 9.6.1-2012.]

### Criterio de Aceptación (ANSI/HI 9.6.1-2012)

| Margen ΔNPSH | Clasificación | Acción Recomendada |
|---|---|---|
| **≥ 1.5 m** | ✅ Excelente | Diseño seguro, sin riesgo de cavitación |
| **1.0 – 1.5 m** | ✅ Aceptable | Cumple norma ANSI/HI 9.6.1 |
| **0.5 – 1.0 m** | ⚠️ Crítico | Monitorear operación, revisar caudal |
| **< 0.5 m** | ❌ Riesgo Alto | Alta probabilidad de cavitación — rediseñar |
| **Advertencia:** Si el margen NPSH es inferior a 0.5 m, se recomienda una de las siguientes acciones correctivas: (a) reubicar la bomba a una cota inferior, (b) aumentar el diámetro de la tubería de succión para reducir pérdidas, (c) seleccionar un modelo de bomba con menor NPSH requerido, o (d) instalar una bomba booster en la línea de succión. |   |   |

---

# 6. POTENCIA Y SELECCIÓN DE MOTOR

## 6.1 Potencia Hidráulica

La **potencia hidráulica** requerida para elevar el fluido hasta la altura dinámica total se calcula como:

$$ P_{h} = \frac{\gamma \times Q \times ADT}{\eta} $$

en unidades prácticas:

$$ P_{h} (kW) = \frac{9.81 \times Q (m^3/s) \times ADT (m)}{\eta} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *P<sub>h</sub>* | Potencia hidráulica entregada al fluido | kW |
| *γ* | Peso específico del fluido (9.81 kN/m³ para agua) | kN/m³ |
| *Q* | Caudal de diseño | m³/s |
| *ADT* | Altura Dinámica Total | m |
| *η* | Eficiencia de la bomba en el punto de operación (decimal) | — |

## 6.2 Velocidad Específica de la Bomba (N<sub>s</sub>)

La **velocidad específica** es un número adimensional que clasifica el tipo de impulsor de la bomba según su relación caudal-altura-velocidad:

$$ N_{s} = \frac{N \times \sqrt{Q}}{H^{0.75}} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *N<sub>s</sub>* | Velocidad específica (adimensional) | — |
| *N* | Velocidad de giro de la bomba | RPM |
| *Q* | Caudal en el punto de máxima eficiencia (BEP) | m³/s |
| *H* | Altura por etapa en el BEP | m |

**Clasificación de impulsores según N<sub>s</sub>:**

| Rango de N<sub>s</sub> (Unidades US) | Tipo de Impulsor | Aplicación Típica |
|---|---|---|
| 500 – 1 000 | Centrífugo radial (bajo caudal, alta altura) | Agua potable, sistemas de presión |
| 1 000 – 2 000 | Centrífugo Francis (caudal medio) | Riego, achique |
| 2 000 – 4 000 | Centrífugo mixto (flujo mixto) | Drenaje, aguas residuales |
| 4 000 – 8 000 | Flujo axial (alto caudal, baja altura) | Grandes caudales, estaciones de bombeo |
| **Fuente:** *Karasik, I.J. et al., "Pump Handbook", 4th Ed., McGraw-Hill, 2008.* |   |   |

## 6.3 Resultados de Potencia

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Potencia Hidráulica | *P<sub>h</sub>* | 5.59 | kW |
| Potencia Hidráulica | *P<sub>h</sub>* | 7.50 | HP |
| Potencia del Motor Seleccionado | *P<sub>m</sub>* | **10.00** | **HP** |
| Potencia del Motor Seleccionado | *P<sub>m</sub>* | **7.46** | **kW** |
| Eficiencia en el Punto de Operación | *η* | 75.0 | % |

[Imagen: Curva de rendimiento de la bomba con punto de operación (Q, ADT)]

## 6.4 Criterio de Selección del Motor

La potencia del motor se selecciona aplicando los siguientes **factores de servicio** sobre la potencia hidráulica, según la norma **NEMA MG-1**:

| Potencia Calculada | Factor de Servicio Mínimo | Norma |
|---|---|---|
| Hasta 5 HP | 1.40 | NEMA MG-1 |
| 5 a 10 HP | 1.25 | NEMA MG-1 |
| 10 a 50 HP | 1.15 | NEMA MG-1 |
| 50 a 200 HP | 1.10 | NEMA MG-1 |
| Más de 200 HP | 1.05 | NEMA MG-1 / API 610 |

## 6.5 Clases de Eficiencia de Motores Eléctricos (IEC 60034-30-1)

| Clase IE | Denominación | Eficiencia Típica (10 HP) | Reducción de Pérdidas |
|---|---|---|---|
| **IE1** | Eficiencia Estándar | 85.5% | — (referencia) |
| **IE2** | Alta Eficiencia | 88.5% | −20% pérdidas |
| **IE3** | Eficiencia Premium | 91.0% | −40% pérdidas |
| **IE4** | Súper Premium | 92.5% | −55% pérdidas |
| **Fuente:** *IEC 60034-30-1:2014, Rotating electrical machines — Part 30-1: Efficiency classes of line operated AC motors.* |   |   |   |

[nota: Se recomienda la selección de motores con clase de eficiencia **IE3 o superior** para nuevas instalaciones, en cumplimiento con las regulaciones internacionales de eficiencia energética.]

---

# 7. ANÁLISIS DE VARIADOR DE FRECUENCIA (VFD)

## 7.1 Leyes de Afinidad

Cuando se utiliza un variador de frecuencia para modificar la velocidad de rotación de la bomba, se aplican las **leyes de afinidad** para bombas centrifugas:

$$ \frac{Q_2}{Q_1} = \frac{N_2}{N_1} $$

$$ \frac{H_2}{H_1} = \left( \frac{N_2}{N_1} \right)^2 $$

$$ \frac{P_2}{P_1} = \left( \frac{N_2}{N_1} \right)^3 $$

**Donde:**

| Símbolo | Descripción |
|---|---|
| *Q<sub>1</sub>, H<sub>1</sub>, P<sub>1</sub>* | Caudal, altura y potencia a velocidad nominal *N<sub>1</sub>* |
| *Q<sub>2</sub>, H<sub>2</sub>, P<sub>2</sub>* | Caudal, altura y potencia a velocidad reducida *N<sub>2</sub>* |
| *N<sub>1</sub>* | Velocidad nominal (100 % RPM) |
| *N<sub>2</sub>* | Velocidad ajustada por el VFD |

## 7.2 Configuración Actual

| Parámetro | Símbolo | Valor | Unidad |
|---|---|---|---|
| Velocidad Nominal | *N<sub>1</sub>* | 100 | % |
| Velocidad Ajustada | *N<sub>2</sub>* | 97.8 | % |
| Caudal Reducido | *Q<sub>2</sub>* | (aplicando leyes de afinidad) | — |
| Altura Reducida | *H<sub>2</sub>* | (aplicando leyes de afinidad) | — |
| Potencia Ajustada | *P<sub>vfd</sub>* | - | HP |
| Eficiencia Ajustada | *η<sub>vfd</sub>* | - | % |

[Imagen: Curvas del sistema con VFD — intersección bomba-sistema a velocidad reducida]

## 7.3 Consideraciones Técnicas para el Uso de VFD

1. **Rango de velocidad recomendado:** Entre el 50% y 100% de la velocidad nominal para bombas centrifugas estándar. Por debajo del 30% pueden presentarse problemas de lubricación de rodamientos y refrigeración del motor.
2. **Velocidad mínima para flujo:** La bomba no debe operar por debajo del caudal mínimo continuo recomendado por el fabricante (usualmente el 10-20% del BEP), para evitar recirculación interna y sobrecalentamiento.
3. **Distorsión armónica:** Los VFD generan armónicos en la red eléctrica. Se recomienda la instalación de filtros pasivos o activos cuando la distorsión armónica total (THD) supere el 5% según IEEE 519-2014.
4. **Cableado motor-VFD:** Utilizar cable blindado con longitud máxima de 100 m para evitar fenómenos de reflexión de onda que puedan dañar el aislamiento del motor. **Ahorro Energético:** Reducir la velocidad al 97.8% puede representar un ahorro energético de hasta **1 − (N₂/N₁)³** en la potencia consumida. Sin embargo, debe verificarse que la velocidad mínima no comprometa la lubricación de los rodamientos ni el enfriamiento del motor accionado por VFD.

---

# 8. TABLAS DE RENDIMIENTO DE LA BOMBA

## 8.1 Datos a 100 % RPM

| Caudal (L/s) | Altura (m) | Eficiencia (%) | Potencia (HP) | NPSH (m) |
|---|---|---|---|---|
| --- | --- | --- | --- | --- |
| {% for fila in t_bomba_100 %}{{ fila.c0 }} | {{ fila.c1 }} | {{ fila.c2 }} | {{ fila.c3 }} | {{ fila.c4 }} |
| {% endfor %} |   |   |   |   |

## 8.2 Datos con VFD (97.8 % RPM)

| Caudal (L/s) | Altura (m) | Eficiencia (%) | Potencia (HP) | NPSH (m) |
|---|---|---|---|---|
| --- | --- | --- | --- | --- |
| {% if tiene_vfd %}{% for fila in t_bomba_vfd %}{{ fila.c0 }} | {{ fila.c1 }} | {{ fila.c2 }} | {{ fila.c3 }} | {{ fila.c4 }} |
| {% endfor %}{% else %}No aplica — sin VFD{% endif %} |   |   |   |   |

[nota: Las tablas anteriores se generan automáticamente con los puntos de las curvas características de la bomba seleccionada. Los datos corresponden a la curva H-Q y rendimiento proporcionados por el fabricante.]

---

# 9. GRÁFICOS DE CURVAS CARACTERÍSTICAS

## 9.1 Curvas a Velocidad Nominal (100 % RPM)

[Imagen: Curva H-Q de la bomba vs curva del sistema a 100 % RPM — punto de operación] [Imagen: Curva de eficiencia de la bomba a 100 % RPM — rango de operación recomendado] [Imagen: Curva de potencia de la bomba a 100 % RPM — consumo vs caudal] [Imagen: Curva de NPSH requerido a 100 % RPM — comparación con NPSH disponible]

## 9.2 Curvas con Variador de Frecuencia (97.8 % RPM)

[Imagen: Curva H-Q de la bomba vs curva del sistema con VFD — ajuste de velocidad] [Imagen: Curva de eficiencia de la bomba con VFD — rendimiento a velocidad reducida] [Imagen: Curva de potencia de la bomba con VFD — ahorro energético] [Imagen: Curva de NPSH requerido con VFD — verificación de cavitación]

---

# 10. ANÁLISIS DE TRANSIENTES HIDRÁULICOS (GOLPE DE ARIETE)

## 10.1 Generalidades

El **golpe de ariete** (también conocido como *water hammer* o transiente hidráulico) es un fenómeno que ocurre cuando se modifica bruscamente la velocidad del flujo en una tubería —por ejemplo, por parada de bomba, cierre rápido de válvula o arranque súbito— generando ondas de presión que se propagan a lo largo de la tubería y que pueden causar daños estructurales graves si no se controlan adecuadamente.

## 10.2 Celeridad de la Onda de Presión

La velocidad de propagación de la onda de presión (celeridad) se calcula mediante la **fórmula de Joukowsky**, considerando la elasticidad del fluido y de la pared de la tubería:

$$ a = \sqrt{\frac{K}{\rho}} \times \frac{1}{\sqrt{1 + \frac{K}{E} \cdot \frac{D}{e}}} $$

**Donde:**

| Símbolo | Descripción | Valor Típico | Unidad |
|---|---|---|---|
| *a* | Celeridad de la onda de presión | 300 – 1 200 | m/s |
| *K* | Módulo de elasticidad volumétrica del agua | 2.1 × 10⁹ | Pa |
| *ρ* | Densidad del agua | 1 000 | kg/m³ |
| *E* | Módulo de elasticidad del material de la tubería | (variable) | Pa |
| *D* | Diámetro interno de la tubería | (variable) | m |
| *e* | Espesor de pared de la tubería | (variable) | m |

**Módulos de elasticidad *****E*** para materiales comunes:

| Material | *E* (GPa) |
|---|---|
| Acero al carbono | 207 |
| Hierro dúctil | 165 |
| Hierro fundido | 100 |
| PVC | 2.8 – 3.5 |
| PEAD | 0.8 – 1.2 |
| Hormigón armado | 25 – 40 |

## 10.3 Sobrepresión por Golpe de Ariete (Joukowsky)

Cuando el cierre o la parada ocurre en un tiempo menor al tiempo de reflexión de la tubería (cierre rápido), la sobrepresión máxima se calcula mediante la **ecuación de Joukowsky**:

$$ \Delta H = \frac{a \cdot \Delta v}{g} $$

**Donde:**

| Símbolo | Descripción | Unidad |
|---|---|---|
| *ΔH* | Sobrepresión máxima por golpe de ariete | m |
| *a* | Celeridad de la onda | m/s |
| *Δv* | Cambio brusco de velocidad del flujo | m/s |
| *g* | Aceleración de la gravedad | m/s² |

**Tiempo crítico de cierre:** La tubería se considera de cierre rápido si el tiempo de maniobra *t<sub>c</sub>* es menor al tiempo de reflexión *t<sub>r</sub>*:

$$ t_r = \frac{2L}{a} $$

Si *t<sub>c</sub>* < *t<sub>r</sub>*, se produce el golpe de ariete completo (Joukowsky directo). Si *t<sub>c</sub>* > *t<sub>r</sub>*, la sobrepresión se reduce por el amortiguamiento de la onda reflejada.

## 10.4 Resultados de la Simulación

| Parámetro | Valor | Unidad |
|---|---|---|
| Evento Simulado | - | — |
| Presión Máxima (Pico de Sobre presión) | **-** | **m** |
| Presión Mínima (Depresión) | **-** | **m** |
| Presión de Prueba de la Tubería (1.5 × PN) | (depende de PN) | m |
| Celeridad en Tubería de Succión | - | m/s |
| Celeridad en Tubería de Impulsión | - | m/s |
| Tiempo de Reflexión (2L/a) | (calculado) | s |
| Paso de Tiempo (dt) de la Simulación | - | s |

[Imagen: Perfil de presiones máximas y mínimas a lo largo de la tubería — envolvente de transientes] [Imagen: Evolución temporal de la presión en el punto crítico del sistema]

## 10.5 Medidas de Mitigación

| Medida | Descripción | Eficacia |
|---|---|---|
| Válvula de alivio rápido | Libera presión cuando se supera un umbral | Alta |
| Tanque de compensación / hidroneumático | Absorbe la onda de presión mediante un colchón de aire | Muy alta |
| Aumento del tiempo de cierre de válvulas | Reduce *Δv/dt* y evita el golpe directo | Alta |
| Volante de inercia en la bomba | Aumenta la inercia del conjunto, reduce *Δv* en parada | Moderada |
| By-pass check valve (válvula de retención con by-pass) | Permite flujo inverso controlado | Moderada |
| **Recomendación:** Si la sobrepresión máxima supera la presión nominal de la tubería (PN) o la presión de prueba (1.5 × PN), se deben instalar dispositivos de protección contra transientes. La simulación computacional detallada (método de las características) es recomendable para sistemas complejos. |   |   |

---

# 11. PRESIONES DE SERVICIO Y PRUEBA DE LA TUBERÍA

## 11.1 Presiones Nominales (PN) Estándar por Material

**Clases de presión normalizadas (PN en bar, 1 bar ≈ 10.2 m.c.a.):**

| PN (bar) | PN (m.c.a.) | Aplicación Típica | Material Común |
|---|---|---|---|
| PN 6 | 61 | Baja presión, gravedad | PEAD, PVC |
| PN 10 | 102 | Agua potable, riego | PVC, Hierro dúctil |
| PN 16 | 163 | Media presión, sistemas urbanos | Hierro dúctil, Acero |
| PN 25 | 255 | Alta presión, industrias | Acero, Hierro dúctil |
| PN 40 | 408 | Muy alta presión | Acero sin costura |

## 11.2 Presión de Prueba

Según las normas **AWWA C600** y **UNE-EN 805**, la presión de prueba en campo debe ser:

$$ P_{prueba} = 1.5 \times PN $$

La presión máxima del transiente (*P<sub>máx</sub> = ADT + ΔH*) no debe superar la presión de prueba de la tubería.

---

# 12. CONCLUSIONES Y RECOMENDACIONES

## 12.1 Resumen de Resultados

| Concepto | Valor | Observación |
|---|---|---|
| Caudal de Diseño | 2.00 L/s | — |
| ADT del Sistema | 180.04 m | — |
| Diámetro de Impulsión | 38.8 mm | Seleccionado |
| Velocidad en Succión | 0.80 m/s | {{ 'Adecuada' if velocidad_succion else 'Verificar' }} |
| Velocidad en Impulsión | 1.69 m/s | {{ 'Adecuada' if velocidad_impulsion else 'Verificar' }} |
| NPSH Disponible | 9.92 m | {{ 'Cumple' if npsh_margen else 'Verificar' }} |
| Potencia del Motor | 10.00 HP | IE3 o superior |
| Transiente Máximo | - m | {{ 'Verificar' if transiente_max_head else '—' }} |

## 12.2 Recomendaciones Técnicas

1. **Mantenimiento preventivo:** Realizar inspecciones periódicas de sellos mecánicos, rodamientos y sistema de lubricación según las recomendaciones del fabricante y la norma ISO 9906.
2. **Protección contra golpe de ariete:** Si el pico de presión transitorio supera la presión nominal de la tubería (PN), instalar **válvulas de alivio rápido** o **tanques hidroneumáticos** de compensación. Modelar el transiente mediante el método de las características (MOC).
3. **Eficiencia energética:** Evaluar la implementación de **variadores de frecuencia (VFD)** con motor IE3/IE4 para ajustar la velocidad de la bomba a la demanda variable del sistema. El ahorro sigue la relación cúbica de las leyes de afinidad.
4. **Instrumentación y monitoreo:** Instalar sensores de presión a la entrada y salida de la bomba, caudalímetro (ultrasónico o electromagnético) y termocupias en los rodamientos del motor para monitoreo en tiempo real y detección temprana de fallos.
5. **Sumergencia en succión:** Verificar que la sumergencia mínima en el pozo de succión cumpla con ANSI/HI 9.8 para evitar la formación de vórtices que puedan introducir aire al sistema, causando pérdida de caudal y vibración.
6. **Protección catódica:** Para tuberías metálicas enterradas, evaluar la necesidad de protección catódica según AWWA M11 para prevenir la corrosión externa.

---

# BIBLIOGRAFÍA

[1] **ANSI/HI 9.6.1-2012**, *Rotodynamic Pumps — Guideline for NPSH Margin*, Hydraulic Institute, 2012.

[2] **ANSI/HI 9.6.3-2012**, *Rotodynamic Pumps — Guideline for Vibration Measurement and Allowable Values*, Hydraulic Institute, 2012.

[3] **ANSI/HI 9.8-2012**, *Rotodynamic Pumps — Pump Intake Design*, Hydraulic Institute, 2012.

[4] **ANSI/HI 14.3-2013**, *Rotodynamic Pumps for Hydraulic Performance*, Hydraulic Institute, 2013.

[5] **NFPA 20**, *Standard for the Installation of Stationary Pumps for Fire Protection*, National Fire Protection Association, 2019.

[6] **AWWA M11**, *Steel Pipe — A Guide for Design and Installation*, American Water Works Association, 5th Edition, 2017.

[7] **AWWA M51**, *Air Release, Air/Vacuum and Combination Air Valves*, American Water Works Association, 2nd Edition, 2016.

[8] **AWWA C600**, *Installation of Ductile-Iron Water Mains and Their Appurtenances*, American Water Works Association, 2017.

[9] **ISO 9906:2012**, *Rotodynamic pumps — Hydraulic performance acceptance tests — Grades 1, 2 and 3*.

[10] **ISO 13709:2009** (API 610), *Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries*.

[11] **ISO 5199:2002**, *Technical specifications for centrifugal pumps — Class II*.

[12] **NEMA MG-1-2018**, *Motors and Generators*, National Electrical Manufacturers Association.

[13] **IEC 60034-30-1:2014**, *Rotating electrical machines — Part 30-1: Efficiency classes of line operated AC motors (IE code)*.

[14] **IEEE 519-2014**, *Recommended Practice and Requirements for Harmonic Control in Electric Power Systems*.

[15] **UNE-EN 752:2017**, *External drainage and sewerage systems*, European Committee for Standardization.

[16] **UNE-EN 805:2000**, *Water supply — Requirements for systems and components outside buildings*.

[17] **UNE-EN 16932:2018**, *Pumping systems for drainage and sewerage*.

[18] **Wylie, E.B., Streeter, V.L., Suo, L.**, *Fluid Transients in Systems*, Prentice Hall, 1993.

[19] **Larock, B.E., Jeppson, R.W., Watters, G.Z.**, *Hydraulics of Pipeline Systems*, CRC Press, 2000.

[20] **Karasik, I.J., Messina, J.P., Cooper, P., Heald, C.C.**, *Pump Handbook*, 4th Edition, McGraw-Hill, 2008.

[21] **Moody, L.F.**, "Friction Factors for Pipe Flow", *Transactions of the ASME*, Vol. 66, 1944.

[22] **Colebrook, C.F.**, "Turbulent Flow in Pipes, with Particular Reference to the Transition Region Between Smooth and Rough Pipe Laws", *Journal of the Institution of Civil Engineers*, Vol. 11, 1939.

[23] **Crane Co.**, *Flow of Fluids Through Valves, Fittings, and Pipe*, Technical Paper No. 410, 2018 Edition.

[24] **McGhee, T.J.**, *Water Supply and Sewerage*, 6th Edition, McGraw-Hill, 1991.

---

# ANEXOS

## Anexo A: Ficha Técnica de la Bomba Seleccionada

| Campo | Detalle |
|---|---|
| **Modelo** | - |
| **Tipo** | - |
| **Velocidad Nominal** | 1 750 / 3 450 RPM (según modelo) |
| **Conexiones** | Bridas ANSI / ISO 7005 |
| **Material del Impulsor** | Acero inoxidable / Hierro dúctil (según modelo) |
| **Material del Cuerpo** | Hierro fundido GG25 / Acero inoxidable |
| **Sello Mecánico** | Tipo cartridge, carburo de silicio / carbón |
| **Peso** | - kg |
| **Enlace / Ficha Técnica** | - |

## Anexo B: Especificaciones Eléctricas del Motor

| Parámetro | Valor |
|---|---|
| Potencia Nominal | 10.00 HP / 7.46 kW |
| Velocidad Síncrona | (según selección) RPM |
| Tensión Nominal | 460 V / 380 V (según selección) |
| Frecuencia | 60 Hz / 50 Hz |
| Clase de Eficiencia | IE3 (Premium) |
| Factor de Servicio | (según tabla NEMA MG-1) |
| Protección | IP55 / IP65 |
| Aislamiento | Clase F |

---

*Documento generado automáticamente por ****Bombeo Pro v3.3.0**** el 29/10/2026 08:07.* *Los datos contenidos en este informe deben ser verificados por un ingeniero hidráulico responsable antes de su uso para construcción o adquisición de equipos.*

[img-1]: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKoAAACjCAYAAAAaeYVKAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAADVzSURBVHhe7X1ptFzXVeZ3qt486D1ZkiVZgzVYHmPHiQw4xEnjtg0hEBYJJE2yWEnAMXTMmAQSYHWnCRCGBb3AIQ4BVnoxJKwkDasZGppAOhMhDpAQO45jy7YUSx4kW5Klpye9ue7pH3s4+5x7bw33VUl6q2vXuu/eOuc7+9vn3H2+2lV6r+S89x5969tFbrW0oW99uxitn6h9WxPWT9S+rQnrJ2rf1oT1E7Vva8L6idq3NWH9RO3bmrB+ovZtTVg/Ufu2JqyfqH1bE9ZP1L6tCesnat/WhPUTtW9rwvqJ2rc1Yf1E7duasH6i9m1NmFtLvzjtPXB81uPUWY8z8x7zS8DSikcjyyEBOD43Me4uRZV0+Mi/o8BWY8nwUm8lHbUaMDToMDYETI3VsGGyhk1TDs6lyLVrF3Winpn3ePxYhkPPZThyIsPR0x4+y98v7yVtShI0N0BOxfjSFSlp1+aU1if+41OBMT4JoCweDw8HxzxRB2o1h8s21LDr0jr2bqnjqu11TI2t3cy96BL1zLzH/YczPHikgW8cZ6n0wOIKcG6BVHRuyWNlxWOpAWQZHdbCjOIbXzbRfKIxPh2QJlqKz7Xz05yfFJA8LcQ7TswCHgfUa8Bg3WFoABgdAsaGaxgfAYYHgpu9W+u4cfcA9u8bXHNJe9Ek6sFnM3zxsRV85TBJZuaB589mOHXOY2YOmF/yBTdQTnQj5Ya2TjSLixPZFYxrlvht4QOxPUXPyU+H+CQehZmno0MO0+MOGyZruGTSoVYjBzddMYBbrhvCldvqduhFaxc8UR8/5vHpr6/gwNEGAOD0OY/nZjxOzBbUnkZZ6HnSXXhR/NJoTh3hY0UL8ZQlbJECluHFcu1mY8QX/LRNfM0Bm6Zr2DxVwyXrHOCBa3cO4PYbh3D19os7YS9Yop6Y9fjEA8ukoACem/F45vkMswuwd7RIMKIbXgRYNZ6tXYXTp2lHihcz7UFJTXc6oA18tCG0Q0480iTwujGHbZfUsWU9ffBz0xUDeNXNw7h06uL8IOiCJOo/PdLA33xlBVnmcfKsx5HjHucWQxjxDS+oMZOIczNI8doenXIXeT/RybRTXKXKng4w+CIlTZ/n8NoeTrEfbknn3QoPj4kRh8svrWPTVA21GvCabx3GbS8cEuBFY+c1UWfnPf7iX1fwtacaWFgCnjie4cSsJ4VwFWrMtvG2oUKN2QaeoojjyfGb50EZW+NzT5MA0njyflrjN03VsGdrHWPDDjfsGsAbbh25qN5wnbdEffyYx0e/uIyZcx5HT9NHTuXv1m2DUS5tj07JRRs1Zqf4XHuxMpbFFeEjh9yf88Nx5Rya7lxDE3zhRX7eNQD7ttVx2YY6pscd3nT76EVTu56XRP3SoQY+et8yAODxoxmOzmTm878misLmU8VKQs7NQP20iWdrGU8yriVerNN4DL7oc9JCPLsN6xTH03xjxXFtvaSGa3YMwHvgTbeP4CXXXPhSoOeJ+vkDDfzll5axvAI8cjTDzJzP3ckQAS2Y98W1mT5N8NKQm4i5UUUXuZm3wufa+WnOTxV885o0f1G+TtRbsE4yj4J4Yj8e0xM1XLezjuFBh9e+bAT/8QLXrT1NVEnS+UXg609nmF+ShYoXTiwXiS4845NxLfHRuKIbyHh9XhFvMyScoufkp0N8Eo/Cknjyfirg82FhbMjhht0DGBt2eN3LL2yy9uyziC8dauCvvrSMhSWHh55uYH45rJZz8u/QLjrCz9ictDpHUEE68mWAgDN49WU9F/mXVstj8PQ04PW59WmPmEWjSOdteKJmHVfsP7DEFrE7gy9dJ8YbbPDvMLfo8cChFcwtevz55xZx38NLwcd5tp4o6uPHPD74fxextAw8+GSGuSV5MxG0AgjSkYtAu4sBq8azFcYTKY1c8NO0I8WLmfYwb9OdDmgDb6I0HXLikTwu+InhZfikOyJyAMaHHF50xQBGBhx+8tXjuGrH+X+D1XVFnZ33+Oh9y3AADhzLML9MSQoUKQpdy15OrW1FUXexIio+UcQwLPEfKZyVHMYbJS3EJ3GF6xCLICO8uFO4YwVkpOO2xH+weB5ynZu38qTrxHgzWuA1OMwveTxypAHnHD78yXl6n3GereuJ+hf/uoLTcxkeO5ph5hy9cfKe9rD38u/1nva17QvN8Lzn83g+Urwc8n6XGwQp/WKleD0Tt/VP5ziewEO+tEl52sNrN19qLIIUbu1vE5/61/h45kk8Mg4hpwF4OA+cPutx4MgyTs96fOxTCzzD82ddTdR/eqSBh57KcOy0x7EzNGGAlZSupKVwBxfveIN35CuPF8/FypJaDq/KGBxGNNoc+489CThc519BEgUOw2Voof/wMzbFqzIyso11aubfsZI6ONTgUHMONQDPnvI49nwDDx1awWfuP7/1atcS9cSsx9/8+zLmlzwOPtvgHWx3t9nBcpid3BZednwTfMDGCgEYvFGUGC9+hDr2nzvUD+MjNWt22JjbxNt1kofBdLJOEd7EDEldkmk4xnEAgAcOPtXA/JLHX39+ESdm0t8a6p11LVE/8dUVZB544kQG73nf5hQFKlVmv+t1XrGkNcYHd4wvVBQ7QIal/hkv/hOifPxWEfPW3H/oUXfipTD+BB9xClPsOTdvgSTrFOFzcGqvgerkmh6ULB7AE8804DPg7+47f6ralUR9/JjHV55o4OSsx4kz8a6mncraaXYub1qjEGHnp3jxkFMIHie7XpAiAmJBFFrg1b8ccTxhXBKP8jTDE9BypfHIOOEWT5ZH8EXrWjYPiiEfj/abnHZck4IV1bEvx588OA+cnMlwcibD/Y8u47En6dcze21dSdRPf30FAHDkBM06p0Rm56uKGFMl0i3OyNJaK9KnyH9oCyYRKCZRFiRKFJTJ+rRHzKJRpPM2PFGzjiv2H1hii9idwZeuE+MNNvgPeFdYk9KZ1JXnpmeHI89mcAA+8+/0T+O9tlUn6sFnMxw42sBzMx5nFzKzu8P2lueyk4NCcJvFC1YVwuBNW1M8m7YJU4SN/Rt3kf8Ir34YF/E0O4LvMI/4iLhYFMvWKT+XMI+m6yQPwUvqMllRTUp9IHXVs8fcvMdzz2c4cHgZB5/qvaquOlG/+BgFefSUL1AUutadnVjbiqLuGK+Sx/hEEcOwxH+kcFZyGG+UtBCfxBWuQyyCjPDiTuFU/ynecVviP1g8D7nOzVt50nVivBktcKpF6Rzq0VCTOn7HTz7Dowbg2MkMNQD/8rXeq+qqEvXMvMdXDjfoz5cXwu6W7ai7uqlCWHyJougmpz6rEIEnxFWK1zMrivFP5ziewEO+tEl52sNrN19qLIIUbu1vE5/61/h45kk8Mg4hpwGtSYknX5OykoKUlNoIfvacx6lZj/sfXcZsj/8RYFWJej//GcnxM/KvT2H3Fu3g4h1v8I52cB4vnoOaxNex5fCqjMFhRKPNsf/Yk4DDdf4VJFHgMFyGFvoPP2NTvCojI9tYp2b+XWFNioKalJRfcHSmv72iccDJUx41ODxwgN6n9MpWlagPHm4gy4DjZ7K4FoqUkVUnUoGgbhFednwTfMDGCgEYvFGUGC9+hDr2nzvUD+MjNWt22JjbxNt1kofBdLJOEd7EDEldD1ZSmVjwFdek8s6fx/KZsDTmxKkGsszjoYMXaaKemff4xgn6c+bM2y0d9rSYXOcVS1pjvDQovlBR7AAZlvpnvPhPiJorYt6a+w896k68FMaf4CNOYYo95+YtkGSdInwOHmpSV1iT8tk+pE5V5SX1rfGcTp/xOPxMo6cv/5UT9fFj9Pf3z5/NtEiyO5c3rVGIsPNTPMMC3qoMZPeqFxUBsSAKLfDqX444njAuiUd5muEJaLnSeGSccIsnyyN46o/xZfOgGPLxaL/J6XY+J1VcUpOGWpbVlcfPzNJHVQeP9O7df+VE/cZxinpmDmav6t6OTPQhbHFGltZaQRVsR9wWjIcFTKIsSJQoKJP1aY+YRaNopcDSrOOK/QeW2CJ2Vis0XSfGG2zwH/CusCZt/jmpPKzKhtpUVJbGnzlLPEeeuQgT9fDxBhaXPX+DidRDtJODQnCbKITseD1YWVQhrHo0wbNpmzBF2Ni/cRf5j/Dqh3ERT7Mj+A7ziI+Ii0WxbJ3ycwnzaLpO8hC8pC6Tta5JTW3K19QXYg1KKjUssLjosbwMPPXsRZao3gPHTnucW4TZwXlrW1G4QfEqeYxPFDEMS/xHCmclh/FGSQvxSVzhOsQiyAgv7hROiqN4x22J/2DxPOQ6N2/lSdeJ8Wa0wFfzOWlRTRqUVJDEMz/v8dwJ2iS9sEqJenzWI/PA3GI7ChE6ShVFNzn1WYWgcdQkVorXMyuK8U/nOJ7AQ760SXnaw2s3X2osghRu7W8Tn/rX+HjmSTwyDiGngVV8TlpWk4qSCocDsLDokXmPk6dlUHetUqKeOkvBLCzHO1iijnd86CABKMIzTL0xXq9jy+FVGYPDiEabY/+xJwGH6+Y1aRS4DC30H37GpnhVRka2sU7N/LvCmrTa56RRTcrjZR0tz+IiXZ8+05tf/auUqGfmafcurfDe1h1v1cDseD14xzfBB2ysEIDBG0WJ8eJHqGP/uUP9MD5Ss2aHjblNvF0neRhMJ+sU4U3MkNT1YCWViQVfcU3a+nNSGR8rap5neZn6z567iBR1fokCXebaWfay7DS798OON8YNii9UFDtAhqX+GS/+E6Lmipi35v5Dj7oTL4XxJ/iIU5hiz7l5CyRZpwifg4eaVFQwrkn5bB9SpxbUpKTGhKNzMU/WoPEL5jvEummVEpWUFMgaViHCzpftqyrALTmF4HGyawUpIiAWRKEFXv3LEccTxiXxKE8zPAEtVxqPjBNu8WR5BE/9Mb5sHhRDPh7tNzndi89JFVfIQ1jJhWXzZ/HdtEqJKt9bmuki2R1PLeAdV1xrBVWwHXFbMFkcxSTKgkSJgjJZn/aIWTSKVgoszTqu2H9giS1idwZfuk6MN9jgP+BdYU0aaspQk8o5PKzK5mpSic3MKc9D6ithpt8n1i2rlKgiD6pppm4StQgKEaTEtjXFC4u0CVOEjf0bd5H/CK9+GBfxNDuC7zCP+Ii4WBR13sk65ecS5tF0neQheEldJmtdk5ralK+pL8QalDR8Tmq3SVMeWdAeWMVEJZOdFk8l7D4DBKySquQxPlHEMCzxHymclRzGGyUtxCdxhesQiyAjvLhTOCmO4h23Jf6DxfOQ69y8lSddJ8ab0QIX1VOFy9WkrJrJo6wmDUoqSMOjfEU8fNboumuVEzUohD4rVxTdfNRnFYLGUZP6LsPrmbitfzrH8QQe8qVNytMeXrv5UmMRpHBrf5v41L/GxzNP4pFxCDkNmFoRhTVpdz4nBY+lcUU83MeYblvlRHXgbUQXAO/sprWW6gHjg6fIcnhVxuAwotHm2H/sScDhunlNGgUuQwv9h5+xKV6VkZFtrFMz/65JrajKJorI54Cv9jlpTQ/Dw/Nwhq9XVjlRox2vB+94VQirHik2VgjA4I2ixHjxI9Sx/9yhfhgfqVmzw8bcJp59Ex0/DKaTdYrwJmZI6nq6A6W1Ikwt2qXPSWMeq6hx7dsrq5yosvfDjk+6rMIVKoodIMNkTwas+L92O//HCGZcc0XMWzP/tkfdiZfC+BM8n3ZtrmP/FYPYubEe+Q/jCKsD2AGdQvyKz8FFNVvViuYhdWpBTUpqTDipQ1vzFCg3P3pllb7N7xMPLOMTD6zgywcb0X8SIRvKw/N0+cwU2powhucx/vrL6/jp7x7Bi/eE/9Xr3ILHZ7++gl/++DzmFjPDkztFz4nXxpU75fFJPAqLnwIe+KE7RvCalwxj79bwTXez8x5/+Il5/MH/mY/geV6WsVy7XEjy8OE5pz0lDVhxIoweLsKHcWSUnF7TLM/j4Dz9uYnwFPGNj9Zw3VUDeNm3DOCWm7v/PaqrUlSrLNwEWCXln2HJbFswmaxinMPd3zmCP/nJiShJAWB8xOGVLx7En71tApddUjc+7RGzaBStFFiadZyNORyBBRgbdrj3rZP42deMRUkKAJOjDm//3jH80dvWlayT8Bb5D3iX1oqsgvmaNK9wVmVzNSlEtcOc8jz5mtQqqeBpbO+suu82ai2pa3K1mbrgNq0lCfeSK+u46/bhiC613Ztr+MjbJrB+PPDla1KywF92aKhmHvERzYPFrgbgg3dP4tYbBpPoYrv56kH8/GvHWq+T1rZhnRya1YppTWpqU76mPg44endf7XPSlEe4eajZXt216olqjWcpO0uUShUirc10GOPVgcO6sRre+4axFFpol0w43HPXBOo18gVdbLJwbW+FqIfBa/wCJ8VRvOO2xP/bvncMN+2LFb/M3njbCNZPEkl+nZCLi1pY4YwS5mtSVrjkYfu6+jlpoWIH5e6VVUtUkSq+DpuP1MYqBFQhzJAyvPe45eo61k+0P+MbLq/jna8ebaKkCHKicRG3NGm3TE2ULoo/KCk8cMeNQ7jz20dsKC3tm/YNmnnn4xEe6BYBcBF9ThrOwhl4HPP0yqolqs0jW2vxrpSWcB1bDs/K4uAwPtJ5SK9/2TC+az8X8LbGbFqTRoHL0Ch+OcJPsj1b6viNN4+HgW3a/isG2/LvWtWKMMqW1IqqoAjv0FVJeTwhC3h0fFyTOsNX4/E1Th7hoVjieXTTOs8K2tisQPlay9Z1ViFoHLcZRYnxHoMVvx7+F39gFFdtq0XxlB825jbxPNexIYcP3D2BkaHOb8j2jTXDy76LlJRlu7RWRKgRSf14rKy155uk5y5+TirqnPCQD2nsvlVKVIBmKjsz1FqsDbb0iobIfgtY2YPkRy46t+FBh/fdNYHpsdh38B+YpUt3f2H8CZ6V6r+/ZQI7N1XcTSAu8UwKZLo4TlLNFrWifWiNmK9JSY0JJ3Voa54C5VYfRTyhjRi6b5UTlTYQ1VeyG7Xa4s0ZYdvBy1HRtq6v4XfeMo6ayIHyELdpouskHgmAnlIg1E/HW185iv/wgubv8FuaiceuU0ggqUlFLYk7Vyt2WpNGHJaH1dLwiC/ybXjYfZ4n4HnFum6VE5WC0tAB3UvSFixMkjGsYIovUeAqtn/vAH7qVWPsN/AQr9KBntqYwxHiDfay6wbx4989mrRWMfEfGFxaK7IK5mvSMoXjejGtSdGiJlVljGtSq6QBzxxck0Y8PD7MpvtWOVFJoVixbC0nEgG6pg3H2lVU+/GOtOqyWvvh24dx2w0DCY9R0lwcSWyJku7YVMNv3TmR0nRs5C5eJwdRqKJa0SpcXCvKNfWFWIOSSg0bb8OmPDze8gi3TgA0JlJsU/vykK5b5USNFKhEEWUnKzZSOJY2M67IR1X79TeOY/dm/pcroZdOVgIbf6S8xkaGHH7v7klMjqY9nZvO2zwP9aCtE0W1jMIlj+Ja0SqpIA2P8hXxWOVuwtNCsbt5D62tIlELakzp0c0a14BBuVhReBd7PXdvO44MOXzgP09gdMgFHhUFjiWKP6+kHsBvvHkce7as4s2TMY8wx7ApQq0oCgVT86nCdVqTFikpw0UBYx57ztekTnjoRuXHMZYWsPu2ikSlXWRCND3SyhhVUu5JFFjETTx2y3ZsrOG3fnhcuWxc9gg/Y/vhO0Zwx4u6/wsWrlWtCKNsRbWiKltxrWhWOubR8XFN6gxfjcfXkpqU+gQjPOxLcLC1anetWqKmNaY2c1tpTSqqKiJr1Mwobjft5dcN4kdfMZKLIT44ZlVSj/37BvCOV7f3T7mdmIMoYZNaEaKkXGuKCsvakDSbc/AVKWkpj1XUpCYVdU54rH/LAx6vE+ju7VOrlqglO0d2slUr0SpnmwXPO1M7WHm7bT/2ylG85OqhEA8rCWxcJrRLp+p4/49OotblUGQ1SDVb1Ir2IXVqQU1KasxKZ9a6OU+BcquPIh5pMz6ZR64lhh7cPqB6orL6yDPdrElNyrtM+nXT6SF+ko4um3PAb79lHDs2OhMP8UT0AAYHgN+7ewJT471Z8bX+OWmIT/Ch9tVF7IFVTNT4JoagaXeJMkobCmpSUVLFJNPvtk2O0rv3kaFaKYsD8N43TuDane39RlQVo5ov1KaxspUpHGFyNSkrGCEpfquuxJOvSa2SBjxzcE0a8TSpScNBbYUL2wWrlKism3F9x4qYq/14RwYVlXEF+KDJPbHdm+v49TeNiYAaJSXWH3j5ML77m7r/5klM6jtetETh4lpRrsO4VEmlhk23eFFNGnykPMLNQ1UVI8Uuq0m9LCDzqI/uW6VEFZOdrMtklNTJ7jI7zCppIT6G98TuuHEIP3R7+ut5DjfuHsAvvK7z34jqyKLaMihpTdcyPIprRaukgqQ1I2Xks3JYHqvcTXjaUuyAC/jc7e6qVU9Uo0Sye4NKkmrKbg4br7gmpWeE79GGjOwdrx7DTVcMSBTYMOHw/rdOYKA7H5eWW6RsfGNF4TqtSYuUlOFpTSo+wzlfkzrh4fuSG1fAo+pqeHpl1RMVAHh3BWXk6RTUpNTM+GjqoeV8Wc0Bv/ujk9g8VcNADbj37klsmFzlUrRh8ooSKVtRrajKliicKleqcEmtyDipSZ3hq/H4Gt984aE+wbRZk0of82g+9MCq3R3d6WlNKqoqYhnUtfDQ2lbKnPOhp2RT4w733j2Bd79+DC/c3bs3T5GJokKUVN75U2NUK+orkihconQQX0U1qVXUpCYVdU54rH/Lo6opNyncrDAf5end/auWqGphF7nwNPTyztSOqCbNW+/2Y7Fdt3MAr70lrVfbt4UOv2LRwSiqfZh34qqots40qqlJClZNGR/VpNJnlFt9FPFIm/HJPHItyq5no9iWp/jOrt5WlahaXZrNphvOo0VNaprFn+Lbt9l5j/d+fC5t7rn9w78v4fMd/me1Hrbm67Am1QQ143VcXJOKL/JteNh9nsfiYx40q0lVSdkPz6kXtqpEpQkU16SipIpJpm/gek11Tuf2Z59dxN/+21La3DM7dKyBd37obDyJNszxHPMKx/ViWpOywlmtsupKCpevSa3CBTxzIKiu8lSsSXWsUduOF6VNq5yonjZYUpNaJWX1bFqTsi+DqbIjvff4L396Fo/28D/kEptb9PiRe87wt7R0bpHC8cuHqGGspIwrUrhosY2SJgonaxnVpLz+kWJXrUnFB/sEUOn+tWOVE9XJD7OBrJICaU1KQLvfwrW9FRbRnjkHLDUc7v7ALGZ69J8dgDfm2/7gLI4cpw3RaaSyDqJw+VrRKqkgaZytFUXJQk0aVLlYsQ1PW4odcHpuQ7Hzd7h7VjlRZbPFG69ZTUq7Lq+kCb7CjiQaj2eez/ATvz+rX9nebbv3f8/h0w8sAqu4HQ6sSuYsCqUKV6ak4iOpScVnOOdrUic8vM65cQU8qq7CI0oqMfC9UnwPrXKipjUpzM6Mpx5a5EKuqc4xeHHUodEoGvelx1fwO3/Z/TdXX3h4Gb/71+TXseJUsVjZymrFVOEKakWjcE7Wkn2KwtFh2kw92a2aNOKpdPfas8qJKioWzgVHriZtgecxnZr1DQ/84T/M4x+/0r03V0eON/ATHzgDb1QI5l13u6Y30WvQspCJoqY8soBhTFDUROG4LeWx/i0PVlWTGh5t641VTlSUKaLs8BTMqkfteiu4VX4Wj2tpPCiMdXjXH53DoWOrf3M1v0Rvnmbn5eWU1QzmpaEDU0W1daZRTbsqwpOvSaWvjZqUx9ia1PLINSkvq2SbNWlQ3hBThSVpyyonalBGyNbVXc/PQrOOaYYnoIhBR2Z4yL3H/GKGt947i7MLVRwGe9eHzuLQsYZJIFHSVShIonC2pszziJrJOGljHCucjJO+mMfiYx6ssiYN+M5fYTqxyokqSkpB26mHFsXKuZUCh+GVLGJ3DkeOZ/iZD52tlvwAPvSJefz9lxfhVHmM4rCCdGLih2rE4IM8h/6YJ1+Tliuc+E94elqTBh5cnIrKati0Jg3Y5oeKayWVkso2qnP5+jNfXcLv/V3yjc9t2L89uozf/PNzlECsoPlaMR3V2oKSshIWKVwBT1Qrsp8L8Tlpcx6D6bJVTlRRraCINH27o8K1vRUFeO6yYzsz6y1cc3j43b+Zwxcebv+fO587neHue+nNk6ieKpypFTuN18EqKSmVrAopo/DFPKSgcpZx9JA2Wyu2VmwzH53XKhSbb16n69GJrSJRw66nTUg7TDYnIArH2CZ47Y4J2jdWT3FENEapM+CnPjiLw8+1fnO1sOTxlnvO4My5oDyh5svXip2ZqUmLlJRRWu9JnYj0nK9JHbno+eek+skCK7/l6aWtIlHj6etkzM6iOsdgUwUOw2VoNRPpFM+sDKEfmF3weO2vzuDfHi1X1jNzHj/yvjM48OSKURJRHlMr8tw6tzKFk/ov4eF5OFlLVrMihaM+wfSqJjX+IfjAU1vNPWxh1RKVFQu5mtSqWbMjYMSXfd6p0bi8fxZYbZs5l+EHf3MG7/wfs/jsg/Q568Kyx8GjDXzk0wu47eefx788sszq0KRWBNdmHVuipKU8VlETheM2dqdjbK1oFVVVU25SuFlhPsIjPpiHf4Rri9HrwNNLq5aoJfUI7TO6skf4yeO4S9piRezcxLO6sR1MSCcC/NV9i/iR983iqrtO4IV3n8R3/tdTeM9HzvLLfahJm9aKIfq2TcbIepTzxMptH9JGishKxooYxgUeuSblZZUUHh1nFNvwBOUN4wMP40RRNcLeWLVEtRtOrhGUK3TQQc8IKMJBT6kvaqxgNFyUNEfPMeTj0X6T0/Zz0qa1YsVY8zyiZoGH2oSPFE7GSR8geFrXfHyCX21NGngkTltjQ86y6D2yaolaNBlInSMtLG9SY9lmHSc7UBDWa/tGNGas4SFe61/iCXhnFCFVnljZYoWrYnmefE1arnCibInC8XgnvlQN7VGlJqV1Eh65v9QW+CxP1XvYyiolqhEtep6rQdMjUdJcPysdq12nJooqQQXO4FtU1dbRkNT1IOWxgeYULlaeKreE8E14yhSOY6WnNEZ8qCqqwq2mJmVriyfwRTyRo+5ZpUSVGxRulNw2OsJPxnCX4nl3Kt5xW+SzgikPs7OiS6eNS+A15leF0yMoqSiLfVRaOOUr4rHKHfNIDDkl5dgJaeajystKJzxVFdvw2JpUD8VIJN23Suste0aUS7cr7y56RjtSN1nY1IQxHTRMxlWwmF6VM41HeBByGjC1oigHWHkcjMLBKGmlIIOJMsU89pyvSR0Yz/PKjbPzESJRV+ERVdR5hbUQ008WTI1ueaiPL4RLfRpHXbZKiSomNYsuEysYPbNFIuP1qVwpcnU7Uejb9O9UeawimFoRRtmKlMe8s+7EiDdfkzrDR4qVVzjqE4woXLdrUuOf5x7Xovma1MYAxvbCqidqQZ0ZDlFbUdW0Pz2C4lWR1JSTePm6SEk9WEkjGVblAYLiaC3HbURI869kPDYoqsf0Oofd22u4Zl8dG9fX8jyMC+O6VZMaHh4XeOQ68BA25qG+oNi9suqJSrc8p1iys2h38f7SWpGRvMMjfDhVMNnRQdGVJ0IRUmpSURg6REn5bB+mrlNFZdXpxJyMhcNLbxrET985hj+5Zwq//xvr8Gu/MIF3v30c97x3Ah/+4BTe+wsTeP33jeCyzXVTW5rYxR9fk/I6bLikhpd/2xBuu2MI11xbj2J3VjVVRctqX8aJolq1FlWNFHs196+1VUtUswPh8zWpbjhqjRsThdONHUSgc2PlTONRWk1SmM8vQw2migBzLqhJVTFE4SpEu2m6hl96xwR++s4xvPSmQQyXfHngzh01fOcdQ/i194zj594+jpd+C/33lCE+SYxQk37f9w/hl351HK97/TC+9/uH8NafGsW73j2KDRtJpYtr0jAfWQ9ZI+0DXxTUpHo2cfXCqiWq4x9RTRpWT4INmiMIOsomVNbe0oxaB//Bk1PlKVCEqCYNyiMPq7Kp8nQa7boJh9/+b5O45or2v43NAbhqXx13vnkE975vEne+eRQ3XD8QKdzUZA0/+64x3Hp7Puu3XFbDG+8aKalJaZ1kPnRIG69bk5pUsFLLdroenVi1RGVFjGrMqHRJa1BWOq0bWYtUSblNlLFTUyXlh1FsB1HCdmpSOYdr6guxRjVch7FetXcAI8Npa/s2PATcfPMAfvzHRnHP+ybw1rtH8IYfHMZ7fmUcu3aX38qdu2q46lqzOWTxo/mIqnK66Tm6saFPD1vLBnXvtpXProWJYulGsjVKpDi0SyPlzZn1VoxobeI/jHeipEYJ8zVpUBb7sH1Sk6Y1XPVYW1sr70NDwPU3DOCltwxiqEnyi4+9++pBSQtrUlqD9mtSHqOvQPHad9sqJ6qtSUVt5FLUU1pE4UJ/c3ynxix5JeXeUFsW1aSsnu3UpEkNd7GbTRtellV/TqpnVWH2GZjMdfescqI68NYzqxGeyhUd4WdsiudaN+ewTUv9u8KalGurqCY1724Vb2vRRHlMDdd5lO1ZtRXIW+rj2FNZmKOZe1yLdlKTiq9Q77JcJMzdsUqJGhRMVDVfk8ZHUDza0FJLhkNU9ex8Z9/pNDtfoKQerKQs+RynKCkgSiqqwmNFdjxLkJ6DL1UVAHPzHd6UDuFVLU3Spw9nePDLK8k8bG1pJFfWi24s94mKipJKH68RPDLvkflM70O3rVKiykKoriSKKLWLYgXG43hfBry0OeCxDr/o7OEjK3ot3qQmlZ0f16R8tg+pUwtqUlEYZxRGeJ54qrNYsyZ78PRpjyefagJo08Iak50+6fGRDy7Erww8Z1FE125NymsU1kKUFPDIkCG7+BSVzhyW3YVJrcgbjjaoPmcVTfDeAw8/udLRd0c9dJgSNSSQ1I+hBlNFgDl3WpNGHNR28EiHiVqiNn/+vxbxMz93Fr/0K+fwtnecxR/98QIe+npnvlGQpM+f8Pj935zH6ZNBQXU+qqQyjhaK2kpqUm2jeTi6e2hkDTR84+JT1DqPkh2X3kK5Si20lyvw8grwp59aSEYW25k5j499bgGusCYNNWWoSe271KAIgsnVpBKbmZPlefCRFRxqM1nPzflCRf3Ixxbx9/+wxDzA3Bxw333LeP/75vEzbz+HP/3jRRx4pDVHut6f/+QK3v8r8zhzSmpzOWg+nX9OyvNOatKGb6CBBjwyeJ/BVcqo1uZ8hS3wqa8u4S++sIj7D63g9DlSQidqaY0bSHed1kH8TMsiNYP/2M9N48Y9zb9b/657zuBzDy7RLndWLUNyybrRy33S7z3dPDMujw9JqofBb9lYxz3vnsTUpDORxTZzxuOdv3gWV+6p4/rrBnDJtMOhQw3c96/LeO5ZUfYSHp7X+HgNL94/gP03DeDyPXUMDgb/wry4CHzpCyv4539cxqmTGZy383Ft8dQc/W/c+fWSg/x4rkkbIDUdGQe2XVnDi28dxTU3Vf+6+TKrlKhfPLCMD39mEV873MDxmSyknn25Nxf5xNQWepZG4Em133T7KH7iVaMYHZZbQfbVb6zgZz80iyeONVBjP6IG+RvACZn0N03IgsS3PPE4YHLM4c7/NIrbbxmiFwo274FP/dMS/uRjC5ifk/KhfR7FRQfNZ8fldezeU8foqMPsTIbZGY8nHm1geakgIaNEpPUt9294xE+U8CQkDR9e7hu+gbFpYOueOl7yijFccf1FkqgPP9nA+/92Do8908DTJ7PCRDOnXCa2xJuGkUGHF+wewPW7BvD0iQxfP7KCJ4/b74KKE7IokXI3wCaI3EBmbqo8Or6YZ3Lc4eq9A9i5rYYjT2V4/FAD585RPagJIudS/wlPWwoXntd43Wq6AZrz1EACU5NXlsJXprAekJqUlVQSdd1Gh0t31HH769Zh2+78P+Wu1iol6nOnPd7z0XN46kSGx482OPNceMeXeAwJay9cvvBOh5fgdYHLElITtygRi29Abnw7POLHlBAhEdvjoURspqDWT1Eixv3pEfDFpU7+KOcpUtIMdN64rYbpS2t4zV0bMHVJ+7/L0K7J/evINk1RUT06FN6tt/s5qeJpEOFNWw6ffIrgQAsHflfPneqL+sAv9+bzQm4DDTVj5N29fZffisd+miDvholP2lIe69/ygMfzQoSznY/wiA/m4R/hOpqHXAcewsY81MfJ2IQn85m+u7fHSraClayBgREP7zKsW9/9JEXVRHUO2LahholR2n280nIy+1L2KLc5GmtgPEj8ECDC5+Dn73PScp7004TwKOaRNuOTeeS6lnxaQWODL+EJsfIY4cl9WsE4XkPCGv+C5/GEL+YBQMoJUlJ6E0Wfm9KjgaERYHpTPb6/XbRKiQoAl19ax/AAMDJENZRsPtqArIrcQhtUztpsnvMnstzAo0K/Jg9YJQGoWhpFgDmDFZXbYM6EF+URrOWwPKIygUd8kW/Dw+7zPEXxCV4UldbB6TijcIYHhkevjRLqfJgHcuZVpbawLnqO2gKP/Zw0OjI+fAP1IY/aoMemrc0/pVmNVU7UvVtI4qcnwrKFxRfppIOE0iwvdyneYKFqE/sNOzxRhB5+Tko8XN+1pXDiP+Hh8U58pQon41OFk7F2zpaH10l46JC2wGd5bAw694gn+Ib5nFSU1KpoA9Q2OgFk8Ni8o8mvca3SKifqVdspUTdM1LgiFdUM6thuTRqUdLU1aVAeuaY+FRSjpIwrUrgynjKFYx56KgoqPIxVhRMFZf9yLuIRH+xTrS2ewGd5tE+PIp5mNSkd9HwFDd/A2DqHzDew/fKLMFGnxhz2bq1jw2SodeR2yzUpqRnE2UB7V7a0AHiX82iBi+qpwukRlFSUxT5sn61Jg5IK0vAoXxFP4GvKYxROYi/jUbUTnqqKbXg6qknlnPCgaU3aoEMU1mUYn65hy/YhjE305o0UVpOoAHDj7gG4GnDplHx0RAdt0PKaVJRTGniUjkPIacDUiqIcqggwCtdpTSrjLQ/DRZliHnsWzsDjhEeUKx1XwFOqcDqvsBZiono0hzwP9fFFq5pUOA1POzWpPSam6RV191WjJsru26oSdf8++oOzzevrrIx0yE5V4y5BhCvG688ADztcFMHUijDKVqAIQXES5REVUc6ER8czjyqOUR5RrkThqE8wwtPtmtT457mrgpo1sjw2Bp17xCO+AbRTk3JdKtdTG2rwaODKayf0/vXCVpWoU2MO+/cOYP2Ew+SoqGjrmlTqUi91aaqkHqQGKsHBF/UFxdEai9tAQ80YUbhE6ZryWEVNFI7bUh7r3/JAVJMWIpztfFTh2Afz8I9wHc1DrgMPYWMe6hMVLecpr0npc1KtSeU6W8HQKDC+zmHvNWM9fdnHahMVAG65bggOwLYN9BmaFVLNCN7ZAiBIUJ0YLqoZdj4doqR8tg9T16mi2rGME4VpzVOg3OqjiEfajE/mUVWzKik8Os4otuERpcu9MnDMjhVR/ctheJxV7BIeNK1JuS417dK3/tI6Mu9x/YunzF3sja06Ua/cVsc1OwawZbqG8WGnm1mFgxWmvCYlPyGBWJVMDaaKAHPutCaNOCyPqEzgEV/k2/Cw+zxPUXyCF0WldXA6ziic4YHh0WujhDof5oGceVWpLayLnqO2wNNpTSrtQ6PA9IY6duwZwfbLe1ufohuJCgB3vIh+a2jXZpZ/vkt6s5xc0RF+BnjY4YkiRMpWpnCEKVYe4hL2PE++Ji1XOPGf8PB4J75ShZPxqcLJWDtny8PrJDx0SFvgszw2Bp17xBN8o52aNKewpKmbtg4i8x77X7Je72MvrSuJevX2OvbvHcCmqRo2ravlatKgpKutSYPyyDX1qaAYJWVckcKV8ZQpnMg+xxnzMFYVThRUXi6a8IgP9qnWFk/gszzap0cRT7OaNP85qdSk0j4xXcPkdB37rh3Hzl1jJvDeWVcSFQC+5+Zh1GrA3svqqPOOpi1Nt000lHu4hRXOKFQ4gpKKstiH7bM1aVBSQRoe5SviCXxNeYzCSexlPKp2wlNVsQ1PRzWp1qYxD5rWpPHnpLYmzfg3+bdsHwZqHi+9daPey15b1xJ101QNr/nWYYwOOVyxrd6kJmWV4gOmVhTlUEVgNSOsVVKCh3GJ8pQpKcNFmWIeexbOwOOER5QrHVfAU6pwOq+wFmKiejSHPI8qKa8qtYV10bOqMPtknqo1qTzfunMYg8PAy27biOn13f+90zLrWqICwG0vHMINuwawbUMdl11S19sXfpI5VR6rCKZWhFG2AkUIipMoj6iIciY8Op55VHGM8ohyJQpHfYIRnm7XpMY/z10V1KyR5bExdKUmRbnCrt84gPWbBrFn3zj2f8sl5s733rqaqADwhltHMD1OdevUeImScp0kKkhHUB4gKI7WWNwGGmrGiMIlSteUxypqonDclvJY/5ZHVRPsX852Pqpw7IN5+Ee4juYh14GHsDEP9YmKlvOU16Tln5OG9gZGJhy27RrB+GQNd7xyC8VyHq3riTo15vCm28cAOLzg8gGMm793ogQS1WxRK9qHqetUUe1YxonCtOYpUG71UcQjbcYn86iqWZUUnpY1qeERJVUexnVSk5bwoGlNyqpZUpNmPsPQMLBz7ygyeLzie7ZifLJ3v85XZl1PVPCnAG+8bRhDAw7X7xrA6FC4sVI/wtRgqggw505rUvWf8ojKGIWzPKw8Mq6Ypyg+wYuikto5HWcUzvDA8Oi1UUKdD/OoooImQG1hXfQctQWe1dak9SGPy68YRX0A+I5XbcHlu8dN9OfPKv3NVLv2qQeW8PHPLWBu0eOhbzQwt+hZLZPDsxL4/N/0yE4K40zSe67LIrxL8OmR/I1ToX8f8xi+muvm3zg145FxvfkbJzoyZHINc834wWGPy/eNYXDE4dZvvxT7v/n81qXWepqo4GT9n59dwNKKx8OHVzBzVtTLLHBhYlVIXDlyCVE0roSHb3TAN0+osFHa4CkY1ykPbZQi/5aHPr+ml/I4URuasGk7Jy63j07UsGPPCAYGHW79jk3Y/80bONILYz1PVAC47+ElfPiTi3AAHn1yBceez8wN4ERJblD+hhff6IB3QMnf3Uf4ThK/BY/ioqOCYkeJyMpY6r/AT8JTpKRFiint9Dy0T2+sY9uuUWTI8IpXbcELXjjN3i+cnZdEBYADTzbw4U/O4/Ssx9GTDRx6ugEfKZ+90TaxOlAeHV+SsOkNlrbopbaDRFlDf3evL/MF7Q1W2AwNXLZzBOs3DWB8so5XfM/WC1aTpnbeEhUAZuY8Pv7pBXzt4AoWloBvPNPAyTPpV88U34DoyClci0SxCuckEdvj6W5Nmo6x+OJSJ3+U8xQpaa4mBb9ZShR2crqOzduHMDjssGffGO74ri0Ynzj/7+7L7LwmqthnvrKEv/7nRfgMODmT4cixBuYW0PRGxYrK7U0UpjyBixPC+i99aY/4TMKU8ZiX5vwrg8WV87Sn2M1qUpOgBe3DY8DGrQNYNz0AOI+X3b7xvH+Y345dkEQFgBMzGf7uviXc/+gyHIDjpzIcPZHhXNl3NJXcoMKEtAlVmpCxnzShAt6VJ66Mb1qTWp58fJ2WGkU8RUqaKmZak46M0d/hT28YQOYz7LtuHC/9tvP7z6Kd2AVLVLHHnmzgM19ewoEjK3AATs96nHg+w/OnM2R6A8tfmuXNmE1YOedudDQuVbgC/+n41dSkUX/JfGRj9KgmzdDAxPo6pi6pYXzKIfMZduwZxf6b12Pn7vPzW1BV7YInqtjBpxv4lweX8cCjlLDeA6dmMszMepw567G4SEpbqKDRUa48RTc6OrpekzbjsbVp6jv1U8xTpKRpTTowlGFkAhibqmFiysE7j8w3cMW143jBi9adl1967oZdNIkqNjvn8cCBZTx0sIHDz6yobiwvA/PzHguLHgsLHisrQGPFI8uCwqEwgSnxuvE5qfgv4ykaZ3nQBk8rxQafvffwXJNmaNDgegNuwKM+7DE4Qkd9EKymGTZvG8Keq0dx5bUTPf8bp27bRZeo1mbnPA4daeDwMw089WwDz52gX3BBevPMjUaBQuXwcs3jkChhUUIFH/n+1H/aZuMTPnllKMQzj2wguxFpOH9jvqdveaZEDG2ZzwDnMbWphk1bB7F5+xC27xpec8lp7aJO1NS8B06e9jh9JsPZc6Suy8vhK8ftjRazSVDabhI812esqD3fRldpe/Mx9jklaJkf8P9AAn6n7zmLBwaBwWFgdKKGiak61q3v3ReWXQhbU4nat/9/TV5R+ta3i9r6idq3NWH9RO3bmrB+ovZtTVg/Ufu2JqyfqH1bE9ZP1L6tCesnat/WhPUTtW9rwv4fCI1pxMIGoQEAAAAASUVORK5CYII=
