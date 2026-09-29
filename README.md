#  subcontracting-make-or-buy

**Modelo "make or buy" para decidir qué perfiles subcontratados conviene internalizar.** Combina SQL, Python y análisis de sensibilidad.

> ⚠️ **Nota:** inspirado en mi práctica profesional en una consultora ambiental. **Todos los datos son simulados.** No se usa información de la empresa.

## Contexto real (práctica profesional)
- Elaboré una propuesta de optimización de subcontrataciones que permitió **internalizar 4 perfiles** antes subcontratados (en torno a $4.200.000 c/u).
- Resultado: una reducción de **aprox. $1.200.000 mensuales por persona**.
- Consolidé información histórica y actual de subcontrataciones para **mejorar la trazabilidad** de los registros.

## Qué hace el modelo
1. **Genera un historial** de órdenes de subcontratación por especialista (2024–2025) en una base SQLite.
2. **Consolida con SQL**: meses activos, continuidad de la demanda, costo promedio y gasto total por perfil.
3. **Compara costos**: subcontrato vs contratación interna (sueldo bruto + cargas del empleador + costos indirectos).
4. **Recomienda**: internalizar solo perfiles con demanda continua (≥ 80% de los meses) y ahorro anual positivo.
5. **Sensibilidad**: cómo cambia la decisión si suben los costos indirectos.

## Ejecutar
```bash
pip install -r requirements.txt
python make_or_buy.py --seed 3
```

## Resultado de ejemplo (simulado)
| Perfil | Continuidad | Ahorro mensual | Recomendación |
|---|---:|---:|---|
| Especialista SIG | 100% | $1.255.958 | **Internalizar** |
| Especialista en fauna | 92% | $1.241.636 | **Internalizar** |
| Ingeniero ambiental senior | 88% | $1.198.286 | **Internalizar** |
| Hidrogeólogo | 83% | $1.186.050 | **Internalizar** |
| Arqueólogo | 13% | — | Mantener subcontrato |

**4 perfiles a internalizar · ahorro promedio ≈ $1,2 M mensuales por persona.**

 *Aprendizaje clave:* un ahorro mensual alto no basta. Si la demanda es esporádica, el costo fijo de contratar supera al subcontrato. Por eso el modelo mira la **continuidad**.

## Conceptos aplicados
Análisis make-or-buy · costeo · SQL (JOIN, GROUP BY, agregaciones) · análisis de sensibilidad · trazabilidad de registros · Python (pandas)

---
Autor: **Liam Esquivel González** · [LinkedIn](https://www.linkedin.com/in/liamesquivelg)
