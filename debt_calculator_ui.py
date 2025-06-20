import streamlit as st
import pandas as pd
import numpy_financial as npf
from datetime import datetime, timedelta

st.set_page_config(page_title="Calculadora de Amortización de Deuda", layout="centered")
st.title("📊 Calculadora de Amortización de Deuda")

st.markdown("""
Esta calculadora permite comparar amortizaciones puntuales y periódicas de un préstamo 
frente al coste de oportunidad de invertir ese dinero. Incluye cálculo de cuota, TAE,
fechas automáticas, ahorro de intereses, ahorro de gastos fijos, comisiones, meses ahorrados y recomendación.
""" )

# --- Entradas de usuario
col1, col2 = st.columns(2)
with col1:
    principal = st.number_input("Capital inicial (€)", value=10000, step=100)
    months = st.number_input("Plazo (meses)", min_value=1, value=64, step=1)
    tae = st.number_input("TAE anual (%)", value=5.0, step=0.1) / 100
    start_date = st.date_input("Fecha de inicio del préstamo", value=datetime.today())
    extra_once = st.number_input("Amortización puntual (€)", value=0, step=100)
    month_once = st.number_input(
        "Mes de amortización puntual (1 = primer mes)",
        value=1,
        min_value=1,
        max_value=int(months),
        step=1
    )
with col2:
    extra_monthly = st.number_input("Amortización extra mensual (€)", value=0, step=50)
    start_monthly = st.number_input(
        "Mes de inicio de amortización periódica", 
        value=1,
        min_value=1,
        max_value=int(months),
        step=1
    )
    monthly_fee = st.number_input("Gastos fijos mensuales (€) (seguros, comisiones)", value=0, step=10)
    commission_rate = st.number_input("Comisión de amortización anticipada (% del extra)", value=0.0, step=0.1) / 100
    alt_return = st.number_input("Rentabilidad alternativa anual (%)", value=5.0, step=0.1) / 100

# --- Cálculo de la cuota mensual
type_months = int(months)
monthly_rate = tae / 12
monthly_payment = -npf.pmt(monthly_rate, type_months, principal)

# --- Simular intereses sin amortizaciones extras
balance_no_extra = principal
total_interest_no_extra = 0.0
total_fee_no_extra = monthly_fee * type_months
for m in range(1, type_months + 1):
    interest_no_extra = balance_no_extra * monthly_rate
    total_interest_no_extra += interest_no_extra
    principal_payment_no_extra = monthly_payment - interest_no_extra
    balance_no_extra = max(balance_no_extra - principal_payment_no_extra, 0)

# --- Tabla de amortización con extras
schedule = []
balance = principal
total_fee_with_extra = 0.0
commission_cost = 0.0
for m in range(1, type_months + 1):
    interest = balance * monthly_rate
    principal_payment = monthly_payment - interest

    # calcular amortizaciones extra y comisión
    extra = 0.0
    if m == month_once:
        extra += extra_once
        commission_cost += extra_once * commission_rate
    if m >= start_monthly:
        extra += extra_monthly
        commission_cost += extra_monthly * commission_rate

    total_principal = principal_payment + extra
    new_balance = max(balance - total_principal, 0)

    # coste de oportunidad del extra adelantado
    opp_cost = 0.0
    if extra > 0:
        opp_cost = extra * ((1 + alt_return / 12) ** (type_months - m + 1) - 1)

    # gastos fijos mensuales evitados si termina antes
    if balance > 0:
        total_fee_with_extra += monthly_fee

    schedule.append({
        "Mes": m,
        "Fecha": (start_date + timedelta(days=30 * m)).strftime("%Y-%m-%d"),
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
        months_with_extra = m
        break
else:
    months_with_extra = type_months

# --- Mostrar resultados y tabla
df = pd.DataFrame(schedule)
st.subheader("Cuadro de amortización")
st.dataframe(df, use_container_width=True)

# --- Cálculos de totales
total_interest_with_extra = df["Interés"].sum()
interests_saved = total_interest_no_extra - total_interest_with_extra
total_extra = df["Amortiz. anticipada"].sum()
total_opp_cost = df["Coste oportunidad"].sum()
fees_saved = total_fee_no_extra - total_fee_with_extra
net_saving = interests_saved + fees_saved - commission_cost
months_saved = type_months - months_with_extra

# --- Resumen
st.markdown(f"""
### Resultados:
- **Intereses sin amortizar:** €{total_interest_no_extra:,.2f}  
- **Intereses con amortización:** €{total_interest_with_extra:,.2f}  
- **Intereses ahorrados:** €{interests_saved:,.2f}  
- **Total amortizado anticipadamente:** €{total_extra:,.2f}  
- **Ahorro en gastos fijos:** €{fees_saved:,.2f}  
- **Coste de comisiones:** €{commission_cost:,.2f}  
- **Ahorro neto (intereses + gastos - comisiones):** €{net_saving:,.2f}  
- **Meses ahorrados:** {months_saved}  
- **Coste de oportunidad:** €{total_opp_cost:,.2f}  
"""
)

# --- Recomendación final
if net_saving > total_opp_cost:
    st.success("✅ Te conviene amortizar: ahorras más (intereses + gastos) que el coste de oportunidad.")
else:
    st.info("💡 No conviene amortizar: podrías ganar más invirtiendo ese dinero.")
