import streamlit as st
import pandas as pd
import numpy_financial as npf
from datetime import datetime, timedelta

st.set_page_config(page_title="Calculadora de Amortización de Deuda", layout="centered")
st.title("📊 Calculadora de Amortización de Deuda")

st.markdown("""
Esta calculadora te permite comparar amortizaciones puntuales y periódicas de un préstamo 
con el coste de oportunidad de invertir ese dinero. Incluye cuota, TAE, fechas y recomendaciones.
""")

# --- Entradas de usuario
col1, col2 = st.columns(2)
with col1:
    principal = st.number_input("Capital inicial (€)", value=10000, step=100)
    months = st.number_input("Plazo (meses)", value=64, step=1)
    tae = st.number_input("TAE (%)", value=5.0, step=0.1) / 100
    start_date = st.date_input("Fecha de inicio del préstamo", value=datetime.today())
    extra_once = st.number_input("Amortización puntual (€)", value=0, step=100)
    month_once = st.number_input("Mes de amortización puntual (1 = primer mes)", value=1, min_value=1, max_value=int(months), step=1)
with col2:
    extra_monthly = st.number_input("Amortización extra mensual (€)", value=0, step=50)
    start_monthly = st.number_input("Mes de inicio de amortización periódica", value=1, min_value=1, max_value=int(months), step=1)
    alt_return = st.number_input("Rentabilidad alternativa anual (%)", value=5.0, step=0.1) / 100

# --- Cálculo de la cuota mensual
monthly_rate = tae / 12
monthly_payment = -npf.pmt(monthly_rate, months, principal)

# --- Tabla de amortización
schedule = []
balance = principal
# calculo intereses sin amortizar para comparación
total_interest_no_extra = 0

for m in range(1, int(months) + 1):
    interest = balance * monthly_rate
    total_interest_no_extra += interest
    principal_payment = monthly_payment - interest

    # amortizaciones extra
    extra = 0
    if m == month_once:
        extra += extra_once
    if m >= start_monthly:
        extra += extra_monthly

    # aplicar pagos\ n    total_principal = principal_payment + extra
    new_balance = max(balance - total_principal, 0)

    # coste de oportunidad del extra
    opp_cost = extra * ((1 + alt_return / 12) ** (months - m + 1) - 1) if extra > 0 else 0

    schedule.append({
        "Mes": m,
        "Fecha": (start_date + timedelta(days=30*m)).strftime("%Y-%m-%d"),
        "Saldo inicial": round(balance, 2),
        "Interés": round(interest, 2),
        "Cuota": round(monthly_payment, 2),
        "Amortiz. anticipada": round(extra, 2),
        "Principal": round(principal_payment, 2),
        "Saldo final": round(new_balance, 2),
        "Coste oportunidad": round(opp_cost, 2)
    })

    balance = new_balance
    if balance <= 0:
        break

# --- Mostrar resultados
df = pd.DataFrame(schedule)
st.subheader("Cuadro de amortización")
st.dataframe(df, use_container_width=True)

# calcular totales
total_interest_with_extra = df["Interés"].sum()
interests_saved = total_interest_no_extra - total_interest_with_extra
total_extra = df["Amortiz. anticipada"].sum()
total_opp_cost = df["Coste oportunidad"].sum()

st.markdown(f"""
### Resultados:
- **Intereses sin amortizar:** €{total_interest_no_extra:,.2f}  
- **Intereses con amortización:** €{total_interest_with_extra:,.2f}  
- **Intereses ahorrados:** €{interests_saved:,.2f}  
- **Total amortizado anticipadamente:** €{total_extra:,.2f}  
- **Coste de oportunidad:** €{total_opp_cost:,.2f}  
"""
)

# recomendación final
if interests_saved > total_opp_cost:
    st.success("✅ Te conviene amortizar: ahorras más intereses que el coste de oportunidad.")
else:
    st.info("💡 No conviene amortizar: podrías ganar más invirtiendo ese dinero.")
