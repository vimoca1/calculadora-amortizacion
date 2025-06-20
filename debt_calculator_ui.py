import streamlit as st
import pandas as pd
import numpy_financial as npf
from datetime import datetime, timedelta

st.set_page_config(page_title="Calculadora de Amortización de Deuda", layout="centered")
st.title("📊 Calculadora de Amortización de Deuda")

st.markdown("""
Esta calculadora te permite comparar amortización anticipada de un préstamo 
con el coste de oportunidad de invertir ese dinero. Incluye cuota, TAE, y fechas automáticas.
""")

# --- Inputs
col1, col2 = st.columns(2)

with col1:
    principal = st.number_input("Capital inicial (€)", value=10000, step=100)
    months = st.number_input("Plazo (meses)", value=64, step=1)
    tae = st.number_input("TAE (%)", value=5.0, step=0.1) / 100
    start_date = st.date_input("Fecha de inicio del préstamo", value=datetime.today())

with col2:
    extra_once = st.number_input("Amortización puntual (€)", value=0, step=100)
    extra_monthly = st.number_input("Amortización mensual extra (€)", value=0, step=50)
    extra_start_month = st.number_input("Mes desde el que se amortiza mensualmente", value=1, step=1)
    alt_return = st.number_input("Rentabilidad alternativa (%)", value=5.0, step=0.1) / 100

# --- Cuota
monthly_rate = tae / 12
monthly_payment = -npf.pmt(monthly_rate, months, principal)

# --- Amortization Table
schedule = []
balance = principal

for m in range(1, months + 1):
    interest = balance * monthly_rate
    principal_payment = monthly_payment - interest
    extra = 0
    if m == 12:  # mes de amortización puntual
        extra += extra_once
    if m >= extra_start_month:
        extra += extra_monthly
    total_principal = principal_payment + extra
    new_balance = max(balance - total_principal, 0)
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

# --- Display Table
df = pd.DataFrame(schedule)
st.subheader("Cuadro de amortización")
st.dataframe(df, use_container_width=True)

# --- Total Summary
total_interest = df["Interés"].sum()
total_opp_cost = df["Coste oportunidad"].sum()
total_extra = df["Amortiz. anticipada"].sum()

st.markdown("""
### Resultados:
- **Intereses totales pagados:** €{:.2f}  
- **Total amortizado anticipadamente:** €{:.2f}  
- **Coste de oportunidad estimado:** €{:.2f}  
""".format(total_interest, total_extra, total_opp_cost))

if total_opp_cost > 0 and total_opp_cost > total_interest * 0.2:
    st.info("💡 Podrías estar mejor invirtiendo ese dinero que amortizando.")
elif total_extra > 0:
    st.success("✅ Amortizar anticipadamente tiene sentido en este caso.")
