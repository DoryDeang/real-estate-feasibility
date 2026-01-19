"""
Real Estate Feasibility Study Calculator - Web App Version
โปรแกรมคำนวณความเป็นไปได้ทางการเงินสำหรับอสังหาริมทรัพย์ (เวอร์ชันเว็บ)

Features:
- IRR (Internal Rate of Return) calculation
- NPV (Net Present Value) calculation
- Cash Flow Projections
- Multiple financial metrics
- Modern Web UI with Streamlit & Plotly
"""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple
import sys
import os

# Add path for analysis modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../Desktop/RealEstateFeasibility/src'))

# Import advanced analysis (optional - will work without if files not found)
try:
    from sensitivity_analysis import SensitivityAnalyzer
    from scenario_manager import ScenarioManager
    from risk_assessment import RiskAssessment
    from dcf_calculator import DCFCalculator
    ADVANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ADVANCED_ANALYSIS_AVAILABLE = False


class RealEstateFeasibilityCalculator:
    """คลาสสำหรับคำนวณความเป็นไปได้ของโปรเจกต์อสังหาริมทรัพย์"""
    
    def __init__(self):
        self.cash_flows = []
        self.results = {}
    
    def calculate_irr(self, cash_flows: List[float]) -> float:
        """คำนวณ Internal Rate of Return (IRR)"""
        try:
            try:
                irr = np.irr(cash_flows)
            except AttributeError:
                irr = self._calculate_irr_manual(cash_flows)
            return irr * 100
        except:
            return 0.0
    
    def _calculate_irr_manual(self, cash_flows: List[float], iterations: int = 1000) -> float:
        """คำนวณ IRR แบบ manual ด้วย Newton-Raphson method"""
        rate = 0.1
        
        for _ in range(iterations):
            npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
            npv_derivative = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
            
            if abs(npv) < 0.01:
                return rate
            
            if npv_derivative == 0:
                break
                
            rate = rate - npv / npv_derivative
        
        return rate
    
    def calculate_npv(self, discount_rate: float, cash_flows: List[float]) -> float:
        """คำนวณ Net Present Value (NPV)"""
        rate = discount_rate / 100
        try:
            npv = np.npv(rate, cash_flows)
        except AttributeError:
            npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        return npv
    
    def calculate_gross_yield(self, property_price: float, annual_rent: float) -> float:
        """คำนวณ Gross Rental Yield"""
        if property_price > 0:
            return (annual_rent / property_price) * 100
        return 0.0
    
    def calculate_net_yield(self, property_price: float, annual_rent: float, 
                           annual_costs: float) -> float:
        """คำนวณ Net Rental Yield"""
        if property_price > 0:
            net_income = annual_rent - annual_costs
            return (net_income / property_price) * 100
        return 0.0
    
    def calculate_cap_rate(self, property_price: float, noi: float) -> float:
        """คำนวณ Capitalization Rate (Cap Rate)"""
        if property_price > 0:
            return (noi / property_price) * 100
        return 0.0
    
    def calculate_cash_on_cash(self, annual_cash_flow: float, 
                               initial_investment: float) -> float:
        """คำนวณ Cash-on-Cash Return"""
        if initial_investment > 0:
            return (annual_cash_flow / initial_investment) * 100
        return 0.0
    
    def generate_cash_flow_projection(self, 
                                      property_price: float,
                                      down_payment_pct: float,
                                      loan_term_years: int,
                                      interest_rate: float,
                                      monthly_rent: float,
                                      monthly_expenses: float,
                                      vacancy_rate: float,
                                      rent_increase_rate: float,
                                      holding_period: int,
                                      appreciation_rate: float,
                                      selling_costs_pct: float) -> Tuple[List[float], pd.DataFrame]:
        """สร้างการคาดการณ์กระแสเงินสด"""
        down_payment = property_price * (down_payment_pct / 100)
        loan_amount = property_price - down_payment
        
        if loan_amount > 0 and loan_term_years > 0:
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term_years * 12
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                                ((1 + monthly_rate)**num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments
        else:
            monthly_payment = 0
        
        cash_flows = [-down_payment]
        years_data = []
        current_rent = monthly_rent
        
        for year in range(1, holding_period + 1):
            effective_rent = current_rent * (1 - vacancy_rate / 100) * 12
            annual_expenses = monthly_expenses * 12
            annual_mortgage = monthly_payment * 12
            operating_cash_flow = effective_rent - annual_expenses - annual_mortgage
            
            if year == holding_period:
                current_value = property_price * ((1 + appreciation_rate / 100) ** year)
                selling_costs = current_value * (selling_costs_pct / 100)
                
                if loan_amount > 0 and loan_term_years > 0:
                    payments_made = year * 12
                    remaining_payments = (loan_term_years * 12) - payments_made
                    if remaining_payments > 0 and monthly_rate > 0:
                        loan_balance = monthly_payment * ((1 - (1 + monthly_rate)**(-remaining_payments)) / monthly_rate)
                    else:
                        loan_balance = 0
                else:
                    loan_balance = 0
                
                net_sale_proceeds = current_value - selling_costs - loan_balance
                total_cash_flow = operating_cash_flow + net_sale_proceeds
            else:
                total_cash_flow = operating_cash_flow
            
            cash_flows.append(total_cash_flow)
            
            years_data.append({
                'Year': year,
                'Rental Income': effective_rent,
                'Expenses': annual_expenses,
                'Mortgage': annual_mortgage,
                'Cash Flow': total_cash_flow,
                'Cumulative Cash Flow': sum(cash_flows)
            })
            
            current_rent *= (1 + rent_increase_rate / 100)
        
        df = pd.DataFrame(years_data)
        return cash_flows, df
    
    def comprehensive_analysis(self, 
                              property_price: float,
                              down_payment_pct: float,
                              loan_term_years: int,
                              interest_rate: float,
                              monthly_rent: float,
                              monthly_expenses: float,
                              vacancy_rate: float,
                              rent_increase_rate: float,
                              holding_period: int,
                              appreciation_rate: float,
                              selling_costs_pct: float,
                              discount_rate: float) -> Dict:
        """วิเคราะห์ครบถ้วนทั้งหมด"""
        cash_flows, df = self.generate_cash_flow_projection(
            property_price, down_payment_pct, loan_term_years, interest_rate,
            monthly_rent, monthly_expenses, vacancy_rate, rent_increase_rate,
            holding_period, appreciation_rate, selling_costs_pct
        )
        
        irr = self.calculate_irr(cash_flows)
        npv = self.calculate_npv(discount_rate, cash_flows)
        
        annual_rent = monthly_rent * 12
        annual_costs = monthly_expenses * 12
        
        gross_yield = self.calculate_gross_yield(property_price, annual_rent)
        net_yield = self.calculate_net_yield(property_price, annual_rent, annual_costs)
        
        noi = annual_rent * (1 - vacancy_rate / 100) - annual_costs
        cap_rate = self.calculate_cap_rate(property_price, noi)
        
        initial_investment = property_price * (down_payment_pct / 100)
        first_year_cash_flow = cash_flows[1] if len(cash_flows) > 1 else 0
        cash_on_cash = self.calculate_cash_on_cash(first_year_cash_flow, initial_investment)
        
        return {
            'irr': irr,
            'npv': npv,
            'gross_yield': gross_yield,
            'net_yield': net_yield,
            'cap_rate': cap_rate,
            'cash_on_cash': cash_on_cash,
            'cash_flows': cash_flows,
            'cash_flow_table': df,
            'initial_investment': initial_investment,
            'total_return': sum(cash_flows)
        }


def create_interactive_chart(df: pd.DataFrame) -> go.Figure:
    """สร้างกราฟ Interactive ด้วย Plotly"""
    
    # สีสำหรับกราฟ
    colors = ['#ef4444' if x < 0 else '#10b981' for x in df['Cash Flow']]
    
    fig = go.Figure()
    
    # Add Cash Flow Bar
    fig.add_trace(go.Bar(
        x=df['Year'],
        y=df['Cash Flow'],
        name='Annual Cash Flow',
        marker_color=colors,
        hovertemplate='<b>Year %{x}</b><br>Cash Flow: ฿%{y:,.0f}<extra></extra>'
    ))
    
    # Add Cumulative Line
    fig.add_trace(go.Scatter(
        x=df['Year'],
        y=df['Cumulative Cash Flow'],
        name='Cumulative Return',
        mode='lines+markers',
        line=dict(color='#6366f1', width=3),
        yaxis='y2',
        hovertemplate='<b>Cumulative</b>: ฿%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Financial Projection Analysis</b>',
            font=dict(size=20)
        ),
        xaxis=dict(title='Year'),
        yaxis=dict(
            title='Annual Cash Flow (THB)',
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis2=dict(
            title='Cumulative Return (THB)',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


# Streamlit App
def main():
    # MUST be first - Streamlit requirement
    st.set_page_config(
        page_title="Real Estate Pro Calculator",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state immediately after (prevents AttributeError)
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'analysis_params' not in st.session_state:
        st.session_state.analysis_params = None
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'color_theme' not in st.session_state:
        st.session_state.color_theme = 'blue'  # default theme
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0  # Default to Dashboard (index 0)
    if 'scenario_npvs' not in st.session_state:
        st.session_state.scenario_npvs = None
    
    # Theme Color Function - Simplified (only dark/light mode)
    def get_theme_colors(dark_mode=False):
        """Return color palette based on mode (fixed blue theme)"""
        # Fixed blue color scheme
        colors = {
            'primary': '#3b82f6',
            'secondary': '#60a5fa',
            'accent': '#2563eb',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
        
        if dark_mode:
            colors['bg_primary'] = '#1e293b'
            colors['bg_secondary'] = '#0f172a'
            colors['text_primary'] = '#f1f5f9'
            colors['text_secondary'] = '#cbd5e1'
            colors['card_bg'] = '#334155'
            colors['border'] = '#475569'
            colors['sidebar_bg'] = '#1e293b'
            colors['metric_bg'] = '#334155'
        else:
            colors['bg_primary'] = '#ffffff'
            colors['bg_secondary'] = '#f8fafc'
            colors['text_primary'] = '#1e293b'
            colors['text_secondary'] = '#64748b'
            colors['card_bg'] = '#ffffff'
            colors['border'] = '#e2e8f0'
            colors['sidebar_bg'] = '#f9fafb'
            colors['metric_bg'] = '#ffffff'
        
        return colors
    
    # Get current theme colors (only dark mode parameter)
    colors = get_theme_colors(dark_mode=st.session_state.dark_mode)
    
    # Dynamic CSS based on theme
    st.markdown(f"""
        <style>
        /* Main App Background */
        .stApp {{
            background-color: {colors['bg_secondary']};
        }}
        
        /* Main Container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}
        
        /* Metric Cards with gradient */
        div[data-testid="stMetric"] {{
            background: linear-gradient(135deg, {colors['gradient_start']} 0%, {colors['gradient_end']} 100%);
            border: 1px solid {colors['border']};
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            color: white !important;
        }}
        div[data-testid="stMetric"] label {{
            color: rgba(255,255,255,0.9) !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: white !important;
        }}
        div[data-testid="stMetric"]:hover {{
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {colors['text_primary']} !important;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Paragraphs and text */
        p, div, span {{
            color: {colors['text_primary']};
        }}
        
        /* Custom Button */
        .stButton>button {{
            background: linear-gradient(to right, {colors['primary']}, {colors['secondary']});
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            background: linear-gradient(to right, {colors['accent']}, {colors['primary']});
            box-shadow: 0 4px 12px rgba({colors['primary']}, 0.3);
            transform: translateY(-1px);
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {colors['sidebar_bg']};
            border-right: 1px solid {colors['border']};
        }}
        section[data-testid="stSidebar"] * {{
            color: {colors['text_primary']};
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border']};
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px;
            color: {colors['text_secondary']};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {colors['primary']}22;
            color: {colors['primary']};
        }}
        
        /* Input fields */
        .stNumberInput input, .stSelectbox select {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
        }}
        
        /* Checkbox */
        .stCheckbox label {{
            color: {colors['text_primary']} !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Header Section with Dark Mode Toggle
    col_header1, col_header2 = st.columns([4, 1])
    
    with col_header1:
        st.title("Real Estate Feasibility Pro")
        st.markdown("Professional Financial Analysis Tool for Real Estate Investors")
    
    with col_header2:
        # Dark/Light Mode Toggle in top-right
        st.markdown("<br>", unsafe_allow_html=True)  # spacing
        mode_icon = "🌙" if not st.session_state.dark_mode else "☀️"
        mode_label = "Dark" if not st.session_state.dark_mode else "Light"
        if st.button(f"{mode_icon}", help=f"Switch to {mode_label} Mode", key="dark_mode_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    st.divider()
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("## Configuration")
        
        
        with st.expander("🏠 Property Details", expanded=True):
            property_price = st.number_input(
                "ราคาทรัพย์สิน (Property Price)",
                min_value=0.0,
                value=5000000.0,
                step=100000.0,
                help="ราคาซื้อขายทรัพย์สิน (บาท)"
            )
            st.caption(f"**฿{property_price:,.2f}**")
            
            down_payment = st.number_input(
                "เงินดาวน์ (Down Payment)",  
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                help="สัดส่วนเงินดาวน์ต่อราคาทรัพย์สิน"
            )
            st.caption(f"**{down_payment}%** = ฿{property_price * down_payment / 100:,.0f}")
        
        with st.expander("Financing", expanded=True):
            loan_term = st.number_input(
                "ระยเวลาผ่อน (Loan Term)", 
                min_value=1, 
                max_value=40, 
                value=20,
                help="จำนวนปีที่ผ่อนชำระ"
            )
            
            interest_rate = st.number_input(
                "ดอกเบี้ย (Interest Rate)", 
                min_value=0.0,
                max_value=20.0,
                value=3.5,
                step=0.1,
                help="อัตราดอกเบี้ยต่อปี"
            )
        
        with st.expander("💵 Income & Expenses", expanded=True):
            monthly_rent = st.number_input(
                "ค่าเช่ารายเดือน (Monthly Rent)",
                min_value=0.0,
                value=15000.0,
                step=1000.0,
                help="รายได้จากค่าเช่าต่อเดือน"
            )
            st.caption(f"**฿{monthly_rent:,.2f}**")
            
            monthly_expenses = st.number_input(
                "ค่าใช้จ่ายรายเดือน (Monthly Expenses)",
                min_value=0.0,
                value=3000.0,
                step=500.0,
                help="ค่าใช้จ่ายในการดูแลรักษาต่อเดือน (ไม่รวมผ่อน)"
            )
            st.caption(f"**฿{monthly_expenses:,.2f}**")
            
            vacancy_rate = st.number_input(
                "อัตราห้องว่าง (Vacancy Rate)", 
                min_value=0,
                max_value=100,
                value=5,
                step=1,
                help="เปอร์เซ็นต์ของเวลาที่ไม่มีผู้เช่า"
            )
            st.caption("หน่วย: **เปอร์เซ็นต์ (%)** | ตัวอย่าง: 5% = ว่าง 0.6 เดือน/ปี")
        
        with st.expander("📈 Growth Assumptions", expanded=False):
            rent_increase = st.number_input(
                "การเพิ่มค่าเช่า (Annual Rent Increase)", 
                min_value=0.0,
                max_value=20.0,
                value=2.0,
                step=0.5,
                help="เปอร์เซ็นต์การเพิ่มค่าเช่าต่อปี",
                format="%.1f"
            )
            st.caption("หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)**")
            
            appreciation = st.number_input(
                "การเพิ่มมูลค่า (Annual Appreciation)", 
                min_value=0.0,
                max_value=20.0,
                value=3.0,
                step=0.5,
                help="เปอร์เซ็นต์การเพิ่มมูลค่าทรัพย์สินต่อปี",
                format="%.1f"
            )
            st.caption("หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)**")
        
        with st.expander("⏱️ Timeline & Exit", expanded=False):
            holding_period = st.number_input(
                "ระยะเวลาถือครอง (Holding Period)", 
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                help="จำนวนปีที่ถือครองก่อนขาย"
            )
            st.caption("หน่วย: **ปี (Years)**")
            
            selling_costs = st.number_input(
                "ค่าใช้จ่ายในการขาย (Selling Costs)", 
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="เปอร์เซ็นต์ของราคาขาย (ค่านายหน้า, ภาษี, ฯลฯ)",
                format="%.1f"
            )
            st.caption("หน่วย: **เปอร์เซ็นต์ของราคาขาย (%)** | รวม: นายหน้า, ภาษี, โอน")
            
            discount_rate = st.number_input(
                "อัตราคิดลด (Discount Rate)", 
                min_value=0.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="อัตราผลตอบแทนที่ต้องการ (สำหรับคำนวณ NPV)",
                format="%.1f"
            )
            st.caption("หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)** | อัตราผลตอบแทนที่คาดหวัง")
        
        st.markdown("---")
        calculate_btn = st.button("Run Analysis", use_container_width=True)

    # Main Dashboard
    # When calculate button is clicked, run analysis and save to session
    if calculate_btn:
        calculator = RealEstateFeasibilityCalculator()
        
        with st.spinner('Crunching numbers...'):
            results = calculator.comprehensive_analysis(
                property_price, down_payment, loan_term, interest_rate,
                monthly_rent, monthly_expenses, vacancy_rate, rent_increase,
                holding_period, appreciation, selling_costs, discount_rate
            )
            # Store in session state
            st.session_state.results = results
            st.session_state.analysis_params = {
                'property_price': property_price,
                'down_payment': down_payment,
                'loan_term': loan_term,
                'interest_rate': interest_rate,
                'monthly_rent': monthly_rent,
                'monthly_expenses': monthly_expenses,
                'vacancy_rate': vacancy_rate,
                'rent_increase': rent_increase,
                'holding_period': holding_period,
                'appreciation': appreciation,
                'selling_costs': selling_costs,
                'discount_rate': discount_rate
            }
    
    # ALWAYS show results if they exist in session (even after reruns)
    if st.session_state.results is not None:
        results = st.session_state.results
        # Restore parameters
        property_price = st.session_state.analysis_params['property_price']
        down_payment = st.session_state.analysis_params['down_payment']
        loan_term = st.session_state.analysis_params['loan_term']
        interest_rate = st.session_state.analysis_params['interest_rate']
        monthly_rent = st.session_state.analysis_params['monthly_rent']
        monthly_expenses = st.session_state.analysis_params['monthly_expenses']
        vacancy_rate = st.session_state.analysis_params['vacancy_rate']
        rent_increase = st.session_state.analysis_params['rent_increase']
        holding_period = st.session_state.analysis_params['holding_period']
        appreciation = st.session_state.analysis_params['appreciation']
        selling_costs = st.session_state.analysis_params['selling_costs']
        discount_rate = st.session_state.analysis_params['discount_rate']
        
        
        # 1. Executive Summary Cards
        st.markdown("### Executive Summary")
        
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric("IRR", f"{results['irr']:.2f}%", 
                     delta="Target Met" if results['irr'] > discount_rate else "Below Target")
        with m2:
            st.metric("NPV", f"฿{results['npv']:,.0f}",
                     delta_color="normal" if results['npv'] > 0 else "inverse")
        with m3:
            st.metric("Cash-on-Cash", f"{results['cash_on_cash']:.2f}%",
                     help="First Year Cash-on-Cash Return")
        with m4:
            st.metric("Net Yield", f"{results['net_yield']:.2f}%",
                     help="Net Rental Yield")

        # 2. Detailed Analysis Tabs
        # Callback to track which tab is selected
        def set_active_tab():
            # This will be called when user clicks a tab
            pass  # Streamlit handles this automatically with key
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["📊 Dashboard", 
             "📋 Detailed Data", 
             "📈 Sensitivity", 
             "🎯 Scenarios",
             "⚠️ Risk",
             "💡 Recommendation"]
        )
        
        with tab1:
            # Secondary Metrics (removed confusing chart)
            st.markdown("#### Key Performance Indicators")
            k1, k2, k3, k4 = st.columns(4)
            k1.info(f"**Initial Investment**\n\n฿{results['initial_investment']:,.0f}")
            k2.info(f"**Total Profit**\n\n฿{results['total_return'] - results['initial_investment']:,.0f}")
            k3.info(f"**Gross Yield**\n\n{results['gross_yield']:.2f}%")
            k4.info(f"**Cap Rate**\n\n{results['cap_rate']:.2f}%")
            
        with tab2:
            st.markdown("#### 📊 Year-by-Year Breakdown (รายละเอียดรายปี)")
            
            # Format dataframe for display with Thai headers
            display_df = results['cash_flow_table'].copy()
            
            # Rename columns to English with Thai
            display_df = display_df.rename(columns={
                'Year': 'Year (ปี)',
                'Rental Income': 'Rental Income (รายได้ค่าเช่า)',
                'Expenses': 'Expenses (ค่าใช้จ่าย)',
                'Mortgage': 'Mortgage (ผ่อนบ้าน)',
                'Cash Flow': 'Cash Flow (กระแสเงินสด)',
                'Cumulative Cash Flow': 'Cumulative (กระแสเงินสดสะสม)'
            })
            
            # Apply Excel-like styling
            def style_dataframe(df):
                # Create styler object
                styled = df.style
                
                # Format currency columns (updated names)
                currency_cols = [
                    'Rental Income (รายได้ค่าเช่า)',
                    'Expenses (ค่าใช้จ่าย)',
                    'Mortgage (ผ่อนบ้าน)',
                    'Cash Flow (กระแสเงินสด)',
                    'Cumulative (กระแสเงินสดสะสม)'
                ]
                
                # Apply number formatting
                format_dict = {col: '฿{:,.0f}' for col in currency_cols}
                styled = styled.format(format_dict)
                
                # Apply styles
                styled = styled.set_properties(**{
                    'background-color': '#1E1E1E',
                    'color': '#FFFFFF',
                    'border': '1px solid #3E3E3E',
                    'text-align': 'right',
                    'padding': '8px',
                    'font-size': '14px'
                })
                
                # Header styles
                styled = styled.set_table_styles([
                    {'selector': 'th',
                     'props': [
                         ('background-color', '#2D2D2D'),
                         ('color', '#FFFFFF'),
                         ('font-weight', 'bold'),
                         ('text-align', 'center'),
                         ('border', '1px solid #3E3E3E'),
                         ('padding', '10px'),
                         ('font-size', '14px')
                     ]},
                    {'selector': 'td:first-child',
                     'props': [
                         ('text-align', 'center'),
                         ('font-weight', 'bold'),
                         ('background-color', '#252525')
                     ]},
                    {'selector': 'tr:nth-child(even)',
                     'props': [('background-color', '#242424')]},
                    {'selector': 'tr:hover',
                     'props': [('background-color', '#2A2A2A')]}
                ])
                
                # Highlight negative values in red
                def highlight_negative(val):
                    if isinstance(val, (int, float)) and val < 0:
                        return 'color: #FF4444; font-weight: bold'
                    elif isinstance(val, (int, float)) and val > 0:
                        return 'color: #4CAF50'
                    return ''
                
                styled = styled.applymap(
                    highlight_negative, 
                    subset=['Cash Flow (กระแสเงินสด)', 'Cumulative (กระแสเงินสดสะสม)']
                )
                
                return styled
            
            # Display styled table
            st.dataframe(
                style_dataframe(display_df),
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Download Button
            csv = results['cash_flow_table'].to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 ดาวน์โหลดรายงาน (Download Report CSV)",
                csv,
                "feasibility_report.csv",
                "text/csv",
                key='download-csv'
            )
            
        with tab3:
            # Sensitivity Analysis Tab - SIMPLIFIED (Table Only)
            st.markdown("#### 📊 Sensitivity Analysis")
            st.caption("วิเคราะห์ว่าตัวแปรไหนมีผลต่อ NPV มากที่สุด")
            
            # Use form to prevent page bounce
            with st.form("sensitivity_form"):
                st.markdown("**เลือกตัวแปรที่ต้องการวิเคราะห์:**")
                
                # Use columns for checkboxes
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    check_rent = st.checkbox("ค่าเช่า", value=True, key="form_sens_rent")
                    check_interest = st.checkbox("ดอกเบี้ย", value=True, key="form_sens_interest")
                
                with col2:
                    check_vacancy = st.checkbox("อัตราห้องว่าง", value=True, key="form_sens_vacancy")
                    check_rent_inc = st.checkbox("การเพิ่มค่าเช่า", value=True, key="form_sens_rent_inc")
                
                with col3:
                    check_appreciation = st.checkbox("มูลค่าเพิ่ม", value=True, key="form_sens_appr")
                
                # Submit button (inside form - won't cause rerun until clicked)
                submitted = st.form_submit_button("🔍 วิเคราะห์ทันที", type="primary", use_container_width=True)
            
            # Process when form is submitted
            if submitted:
                # Build selected variables list
                selected_vars = []
                var_map = {
                    'monthly_rent': check_rent,
                    'interest_rate': check_interest,
                    'vacancy_rate': check_vacancy,
                    'rent_increase': check_rent_inc,
                    'appreciation': check_appreciation
                }
                
                var_display = {
                    'monthly_rent': 'ค่าเช่า',
                    'interest_rate': 'ดอกเบี้ย',
                    'vacancy_rate': 'อัตราห้องว่าง',
                    'rent_increase': 'การเพิ่มค่าเช่า',
                    'appreciation': 'มูลค่าเพิ่ม'
                }
                
                for var_key, is_checked in var_map.items():
                    if is_checked:
                        selected_vars.append(var_key)
                
                if not selected_vars:
                    st.warning("⚠️ กรุณาเลือกตัวแปรอย่างน้อย 1 ตัว")
                else:
                    with st.spinner('กำลังคำนวณ...'):
                        # Base NPV
                        base_npv = results['npv']
                        
                        # Calculate sensitivity for each variable
                        impacts = []
                        
                        calc = RealEstateFeasibilityCalculator()
                        
                        for var in selected_vars:
                            var_results = []
                            
                            # Test ±20% range
                            for pct in [-20, -10, 0, 10, 20]:
                                # Make copy of parameters
                                test_rent = monthly_rent
                                test_interest = interest_rate
                                test_vacancy = vacancy_rate
                                test_rent_inc = rent_increase
                                test_appr = appreciation
                                
                                # Modify the variable
                                if var == 'monthly_rent':
                                    test_rent = monthly_rent * (1 + pct/100)
                                elif var == 'interest_rate':
                                    test_interest = interest_rate * (1 + pct/100)
                                elif var == 'vacancy_rate':
                                    test_vacancy = vacancy_rate * (1 + pct/100)
                                elif var == 'rent_increase':
                                    test_rent_inc = rent_increase * (1 + pct/100)
                                elif var == 'appreciation':
                                    test_appr = appreciation * (1 + pct/100)
                                
                                # Calculate NPV
                                test_cf, _ = calc.generate_cash_flow_projection(
                                    property_price, down_payment, loan_term, test_interest,
                                    test_rent, monthly_expenses, test_vacancy, test_rent_inc,
                                    holding_period, test_appr, selling_costs
                                )
                                test_npv = calc.calculate_npv(discount_rate, test_cf)
                                
                                var_results.append({
                                    'pct': pct,
                                    'npv': test_npv
                                })
                            
                            # Calculate impact
                            npvs = [r['npv'] for r in var_results]
                            impacts.append({
                                'var': var,
                                'var_name': var_display[var],
                                'range': max(npvs) - min(npvs),
                                'min': min(npvs),
                                'max': max(npvs),
                                'base_npv': base_npv
                            })
                        
                        # Sort by impact (descending)
                        impacts.sort(key=lambda x: x['range'], reverse=True)
                        
                        st.success("✅ วิเคราะห์เสร็จสมบูรณ์!")
                        
                        # Display as TABLE ONLY (no charts)
                        st.markdown("### ตารางผลกระทบ")
                        st.caption("แสดงช่วงผลกระทบของแต่ละตัวแปรเมื่อเปลี่ยนแปลง ±20%")
                        
                        # Build table data
                        table_data = []
                        for imp in impacts:
                            table_data.append({
                                'ตัวแปร': imp['var_name'],
                                'ช่วง NPV (M฿)': f"{imp['range']/1e6:.2f}",
                                'NPV ต่ำสุด (M฿)': f"{imp['min']/1e6:.2f}",
                                'NPV สูงสุด (M฿)': f"{imp['max']/1e6:.2f}",
                                '% เปลี่ยน (ต่ำ)': f"{((imp['min']/imp['base_npv'] - 1)*100):.1f}%",
                                '% เปลี่ยน (สูง)': f"{((imp['max']/imp['base_npv'] - 1)*100):.1f}%"
                            })
                        
                        # Display table
                        result_df = pd.DataFrame(table_data)
                        st.dataframe(
                            result_df,
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                        
                        # Summary metrics
                        st.markdown("### สรุป")
                        col_s1, col_s2 = st.columns(2)
                        
                        with col_s1:
                            most_impact = impacts[0]
                            st.info(f"""
                                **ตัวแปรที่มีผลมากที่สุด:** {most_impact['var_name']}
                                
                                ช่วงผลกระทบ: ฿{most_impact['range']/1e6:.2f}M
                            """)
                        
                        with col_s2:
                            least_impact = impacts[-1]
                            st.info(f"""
                                **ตัวแปรที่มีผลน้อยที่สุด:** {least_impact['var_name']}
                                
                                ช่วงผลกระทบ: ฿{least_impact['range']/1e6:.2f}M
                            """)
        
        with tab4:
            # Scenario Comparison Tab - DETAILED TABLE
            st.markdown("#### 🎯 Scenario Analysis")
            st.caption("เปรียบเทียบผลตอบแทนในสถานการณ์ต่างๆ (Worst, Base, Best)")
            
            st.markdown("""
            **คำอธิบาย:**  
            ปรับค่าสมมติฐานด้านล่างเพื่อสร้างสถานการณ์ต่างๆ
            - **Worst Case**: สถานการณ์แย่ที่สุด
            - **Base Case**: ใช้ค่าปกติที่กรอก (เปลี่ยน 0%)
            - **Best Case**: สถานการณ์ดีที่สุด
            """)
            
            # Use form to prevent page bounce
            with st.form("scenario_comparison_form"):
                st.markdown("**📝 กำหนดค่าสมมติฐาน:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Worst Case")
                    worst_interest = st.number_input(
                        "ดอกเบี้ยเปลี่ยน (% points)", 
                        value=5.0, 
                        min_value=-10.0, 
                        max_value=10.0, 
                        step=0.5,
                        key="worst_int",
                        help="เช่น +5 = ดอกเบี้ยเพิ่ม 5%"
                    )
                    worst_occupancy = st.number_input(
                        "อัตราห้องว่างเปลี่ยน (%)", 
                        value=10.0, 
                        min_value=-50.0, 
                        max_value=50.0, 
                        step=5.0,
                        key="worst_occ",
                        help="เช่น +10 = ห้องว่างเพิ่ม 10%"
                    )
                    worst_rent = st.number_input(
                        "ค่าเช่าเปลี่ยน (%)", 
                        value=-10.0, 
                        min_value=-50.0, 
                        max_value=50.0, 
                        step=5.0,
                        key="worst_rent",
                        help="เช่น -10 = ค่าเช่าลด 10%"
                    )
                
                with col2:
                    st.markdown("##### Best Case")
                    best_interest = st.number_input(
                        "ดอกเบี้ยเปลี่ยน (% points)", 
                        value=-5.0, 
                        min_value=-10.0, 
                        max_value=10.0, 
                        step=0.5,
                        key="best_int",
                        help="เช่น -5 = ดอกเบี้ยลด 5%"
                    )
                    best_occupancy = st.number_input(
                        "อัตราห้องว่างเปลี่ยน (%)", 
                        value=-10.0, 
                        min_value=-50.0, 
                        max_value=50.0, 
                        step=5.0,
                        key="best_occ",
                        help="เช่น -10 = ห้องว่างลด 10%"
                    )
                    best_rent = st.number_input(
                        "ค่าเช่าเปลี่ยน (%)", 
                        value=10.0, 
                        min_value=-50.0, 
                        max_value=50.0, 
                        step=5.0,
                        key="best_rent",
                        help="เช่น +10 = ค่าเช่าเพิ่ม 10%"
                    )
                
                st.divider()
                
                # Submit button (inside form - won't cause rerun until clicked)
                submitted = st.form_submit_button("📊 สร้างตารางเปรียบเทียบ", type="primary", use_container_width=True)
            
            # Process when form is submitted
            if submitted:
                with st.spinner('กำลังคำนวณสถานการณ์ทั้ง 3...'):
                    calc = RealEstateFeasibilityCalculator()
                    
                    # Scenario definitions (use user inputs)
                    scenarios = {
                        'Worst': {
                            'interest_pct': worst_interest,
                            'occupancy_pct': worst_occupancy,
                            'rent_pct': worst_rent
                        },
                        'Base': {
                            'interest_pct': 0,
                            'occupancy_pct': 0,
                            'rent_pct': 0
                        },
                        'Best': {
                            'interest_pct': best_interest,
                            'occupancy_pct': best_occupancy,
                            'rent_pct': best_rent
                        }
                    }
                    
                    results = {}
                    
                    # Calculate each scenario
                    for scenario_name, changes in scenarios.items():
                        # Apply changes
                        test_interest = interest_rate + changes['interest_pct']
                        test_vacancy = vacancy_rate * (1 + changes['occupancy_pct']/100)
                        test_rent = monthly_rent * (1 + changes['rent_pct']/100)
                        
                        # Run calculation
                        test_cf, _ = calc.generate_cash_flow_projection(
                            property_price, down_payment, loan_term, 
                            test_interest,  # Changed interest
                            test_rent,      # Changed rent
                            monthly_expenses, 
                            test_vacancy,   # Changed vacancy
                            rent_increase,
                            holding_period, 
                            appreciation,
                            selling_costs
                        )
                        
                        test_npv = calc.calculate_npv(discount_rate, test_cf)
                        test_irr = calc.calculate_irr(test_cf)
                        
                        results[scenario_name] = {
                            'npv': test_npv,
                            'irr': test_irr,
                            'interest_change': changes['interest_pct'],
                            'occupancy_change': changes['occupancy_pct'],
                            'rent_change': changes['rent_pct']
                        }
                    
                    # Store NPVs in session state for Risk Assessment tab
                    st.session_state.scenario_npvs = {
                        'worst': results['Worst']['npv'],
                        'base': results['Base']['npv'],
                        'best': results['Best']['npv']
                    }
                    
                    st.success("✅ คำนวณเสร็จสมบูรณ์!")
                    
                    # Build detailed table (like the Excel screenshot)
                    st.markdown("### ตารางรายละเอียดสถานการณ์")
                    
                    # Create comparison table
                    table_data = []
                    
                    # Row 1: Interest Rate
                    table_data.append({
                        'Variable': 'Interest rate',
                        'Worst': f"{results['Worst']['interest_change']:+.0f}%",
                        'Base': f"{results['Base']['interest_change']:+.0f}%",
                        'Best': f"{results['Best']['interest_change']:+.0f}%"
                    })
                    
                    # Row 2: Occupancy rate (inverse of vacancy)
                    table_data.append({
                        'Variable': 'Occupancy rate',
                        'Worst': f"{results['Worst']['occupancy_change']:+.0f}%",
                        'Base': f"{results['Base']['occupancy_change']:+.0f}%",
                        'Best': f"{results['Best']['occupancy_change']:+.0f}%"
                    })
                    
                    # Row 3: Rent
                    table_data.append({
                        'Variable': 'Rent',
                        'Worst': f"{results['Worst']['rent_change']:+.0f}%",
                        'Base': f"{results['Base']['rent_change']:+.0f}%",
                        'Best': f"{results['Best']['rent_change']:+.0f}%"
                    })
                    
                    # Row 4: NPV (absolute values)
                    base_npv = results['Base']['npv']
                    table_data.append({
                        'Variable': 'NPV (฿)',
                        'Worst': f"{results['Worst']['npv']:,.2f}",
                        'Base': f"{base_npv:,.2f}",
                        'Best': f"{results['Best']['npv']:,.2f}"
                    })
                    
                    # Row 5: NPV % Change from Base
                    worst_npv_pct = ((results['Worst']['npv'] / base_npv - 1) * 100) if base_npv != 0 else 0
                    best_npv_pct = ((results['Best']['npv'] / base_npv - 1) * 100) if base_npv != 0 else 0
                    table_data.append({
                        'Variable': 'NPV % Change',
                        'Worst': f"{worst_npv_pct:.2f}%",
                        'Base': "0%",
                        'Best': f"{best_npv_pct:.2f}%"
                    })
                    
                    # Row 6: IRR (absolute values)
                    base_irr = results['Base']['irr']
                    table_data.append({
                        'Variable': 'IRR (%)',
                        'Worst': f"{results['Worst']['irr']:.2f}%",
                        'Base': f"{base_irr:.2f}%",
                        'Best': f"{results['Best']['irr']:.2f}%"
                    })
                    
                    # Row 7: IRR % Change from Base
                    worst_irr_pct = ((results['Worst']['irr'] / base_irr - 1) * 100) if base_irr != 0 else 0
                    best_irr_pct = ((results['Best']['irr'] / base_irr - 1) * 100) if base_irr != 0 else 0
                    table_data.append({
                        'Variable': 'IRR % Change',
                        'Worst': f"{worst_irr_pct:.2f}%",
                        'Base': "0%",
                        'Best': f"{best_irr_pct:.2f}%"
                    })
                    
                    # Display table
                    df_scenarios = pd.DataFrame(table_data)
                    st.dataframe(
                        df_scenarios,
                        use_container_width=True,
                        hide_index=True,
                        height=350
                    )
                    
                    # Summary interpretation
                    st.markdown("### สรุปผล")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Worst Case NPV",
                            f"฿{results['Worst']['npv']/1e6:.2f}M",
                            delta=f"{worst_npv_pct:.1f}%"
                        )
                    
                    with col2:
                        st.metric(
                            "Base Case NPV",
                            f"฿{base_npv/1e6:.2f}M"
                        )
                    
                    with col3:
                        st.metric(
                            "Best Case NPV",
                            f"฿{results['Best']['npv']/1e6:.2f}M",
                            delta=f"{best_npv_pct:.1f}%"
                        )
                    
                    # Risk assessment
                    st.markdown("### ประเมินความเสี่ยง")
                    
                    if results['Worst']['npv'] > 0:
                        st.success("""
                        ✅ **ความเสี่ยงต่ำ**  
                        NPV เป็นบวกแม้ในสถานการณ์แย่ที่สุด → การลงทุนมีความมั่นคงสูง
                        """)
                    elif base_npv > 0 and results['Worst']['npv'] < 0:
                        st.warning("""
                        ⚠️ **ความเสี่ยงปานกลาง**  
                        NPV เป็นบวกในกรณีปกติ แต่ติดลบในกรณีแย่  
                        → ควรมี safety margin หรือเจรจาราคาให้ดีกว่านี้
                        """)
                    else:
                        st.error("""
                        ❌ **ความเสี่ยงสูง**  
                        NPV ติดลบในหลายสถานการณ์  
                        → ไม่แนะนำให้ลงทุน พิจารณาทรัพย์สินอื่น
                        """)
        
        with tab5:
            # Risk Assessment Tab - PROBABILITY & DEVIATION ANALYSIS
            st.markdown("#### ⚠️ Risk Assessment")
            st.caption("ประเมินความเสี่ยงด้วย Probability-Weighted Scenarios และ Standard Deviation")
            
            st.markdown("""
            **วิธีการ:**
            - ใช้ผลลัพธ์จาก **Scenarios Analysis** (Worst/Base/Best)
            - คำนวณ Expected NPV ด้วย Probability Weighting
            - วัดความเสี่ยงด้วย Standard Deviation
            - ประเมิน Breakeven Occupancy Rate
            """)
            
            # Check if we have scenario results (need to run Scenarios first)
            if 'scenario_npvs' not in st.session_state or st.session_state.scenario_npvs is None:
                st.warning("⚠️ กรุณาไปที่แท็บ **Scenarios** และกด 'สร้างตารางเปรียบเทียบ' ก่อน")
                st.info("""
                Risk Assessment ต้องการข้อมูล NPV จาก 3 สถานการณ์:
                - Worst Case NPV
                - Base Case NPV
                - Best Case NPV
                
                หลังจากรัน Scenarios แล้ว กลับมาที่แท็บนี้ได้เลย
                """)
            else:
                # Get NPV values from session state
                scenario_data = st.session_state.scenario_npvs
                worst_npv = scenario_data['worst']
                base_npv = scenario_data['base']
                best_npv = scenario_data['best']
                
                st.success("✅ ใช้ข้อมูลจาก Scenarios Analysis แล้ว")
                
                # Use form for probability inputs
                with st.form("risk_assessment_form"):
                    st.markdown("**🎲 กำหนด Probability สำหรับแต่ละสถานการณ์:**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        prob_worst = st.number_input(
                            "Worst Case (%)", 
                            value=25.0,
                            min_value=0.0,
                            max_value=100.0,
                            step=5.0,
                            key="prob_worst"
                        )
                    
                    with col2:
                        prob_base = st.number_input(
                            "Base Case (%)", 
                            value=50.0,
                            min_value=0.0,
                            max_value=100.0,
                            step=5.0,
                            key="prob_base"
                        )
                    
                    with col3:
                        prob_best = st.number_input(
                            "Best Case (%)", 
                            value=25.0,
                            min_value=0.0,
                            max_value=100.0,
                            step=5.0,
                            key="prob_best"
                        )
                    
                    # Validate probabilities sum to 100
                    total_prob = prob_worst + prob_base + prob_best
                    if abs(total_prob - 100.0) > 0.01:
                        st.error(f"⚠️ Probability ต้องรวมเป็น 100% (ตอนนี้: {total_prob:.1f}%)")
                    
                    st.divider()
                    
                    # Submit button
                    submitted = st.form_submit_button("📊 คำนวณความเสี่ยง", type="primary", use_container_width=True)
                
                # Process when submitted
                if submitted and abs(total_prob - 100.0) <= 0.01:
                    with st.spinner('กำลังคำนวณความเสี่ยง...'):
                        import math
                        
                        # Convert probabilities to decimals
                        p_worst = prob_worst / 100
                        p_base = prob_base / 100
                        p_best = prob_best / 100
                        
                        # 1. Probability-Weighted Expected NPV
                        expected_npv = (worst_npv * p_worst) + (base_npv * p_base) + (best_npv * p_best)
                        
                        # 2. Standard Deviation
                        mean_npv = (worst_npv + base_npv + best_npv) / 3
                        variance = ((worst_npv - mean_npv)**2 + 
                                   (base_npv - mean_npv)**2 + 
                                   (best_npv - mean_npv)**2) / 3
                        std_dev = math.sqrt(variance)
                        
                        # Coefficient of Variation
                        cv = (std_dev / abs(base_npv)) * 100 if base_npv != 0 else 0
                        
                        # 3. Risk Score (0-100)
                        # Component A: Worst-case resilience (40%)
                        worst_score = min(100, max(0, (worst_npv / base_npv) * 100)) if base_npv > 0 else 0
                        
                        # Component B: Volatility (30%)
                        volatility_score = max(0, 100 - cv) if cv < 100 else 0
                        
                        # Component C: Expected value (30%)
                        expected_score = min(100, max(0, (expected_npv / base_npv) * 100)) if base_npv > 0 else 0
                        
                        risk_score = (worst_score * 0.4) + (volatility_score * 0.3) + (expected_score * 0.3)
                        
                        # 4. Breakeven Occupancy Rate
                        annual_expenses = monthly_expenses * 12
                        if loan_term > 0 and interest_rate > 0:
                            monthly_rate = (interest_rate / 100) / 12
                            num_payments = loan_term * 12
                            loan_amount = property_price * (1 - down_payment/100)
                            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
                            annual_debt_service = monthly_payment * 12
                        else:
                            annual_debt_service = 0
                        
                        total_annual_costs = annual_expenses + annual_debt_service
                        annual_rent_potential = monthly_rent * 12
                        
                        breakeven_occupancy = (total_annual_costs / annual_rent_potential * 100) if annual_rent_potential > 0 else 100
                        margin_of_safety = max(0, 100 - vacancy_rate - breakeven_occupancy)
                        
                        st.success("✅ คำนวณความเสี่ยงเสร็จสมบูรณ์!")
                        
                        # Display Results
                        st.markdown("### 📊 Probability-Weighted Scenarios")
                        
                        # Probability table
                        prob_table = pd.DataFrame([
                            {
                                'Scenario': 'Worst',
                                'NPV (M฿)': f"{worst_npv/1e6:.2f}",
                                'Probability': f"{prob_worst:.0f}%",
                                'Weighted NPV (M฿)': f"{(worst_npv * p_worst)/1e6:.2f}"
                            },
                            {
                                'Scenario': 'Base',
                                'NPV (M฿)': f"{base_npv/1e6:.2f}",
                                'Probability': f"{prob_base:.0f}%",
                                'Weighted NPV (M฿)': f"{(base_npv * p_base)/1e6:.2f}"
                            },
                            {
                                'Scenario': 'Best',
                                'NPV (M฿)': f"{best_npv/1e6:.2f}",
                                'Probability': f"{prob_best:.0f}%",
                                'Weighted NPV (M฿)': f"{(best_npv * p_best)/1e6:.2f}"
                            },
                            {
                                'Scenario': '**Expected**',
                                'NPV (M฿)': '',
                                'Probability': '**100%**',
                                'Weighted NPV (M฿)': f"**{expected_npv/1e6:.2f}**"
                            }
                        ])
                        
                        st.dataframe(prob_table, use_container_width=True, hide_index=True, height=200)
                        
                        # Risk Metrics
                        st.markdown("### 🎯 Risk Metrics")
                        
                        col_r1, col_r2, col_r3 = st.columns(3)
                        
                        with col_r1:
                            st.metric(
                                "Standard Deviation",
                                f"฿{std_dev/1e6:.2f}M",
                                delta=f"{cv:.1f}% of Base"
                            )
                            if cv < 20:
                                st.caption("🟢 ความผันผวนต่ำ")
                            elif cv < 40:
                                st.caption("🟡 ความผันผวนปานกลาง")
                            else:
                                st.caption("🔴 ความผันผวนสูง")
                        
                        with col_r2:
                            npv_diff = expected_npv - base_npv
                            st.metric(
                                "Expected NPV",
                                f"฿{expected_npv/1e6:.2f}M",
                                delta=f"{npv_diff/1e6:+.2f}M"
                            )
                        
                        with col_r3:
                            if risk_score >= 80:
                                emoji = "🟢"
                                grade = "A"
                            elif risk_score >= 60:
                                emoji = "🟡"
                                grade = "B"
                            elif risk_score >= 40:
                                emoji = "🟠"
                                grade = "C"
                            else:
                                emoji = "🔴"
                                grade = "D"
                            
                            st.metric(
                                "Risk Score",
                                f"{risk_score:.0f}/100 {emoji}",
                                delta=f"Grade: {grade}"
                            )
                        
                        # Breakeven Analysis
                        st.markdown("### 💰 Breakeven Analysis")
                        
                        col_b1, col_b2 = st.columns(2)
                        
                        with col_b1:
                            st.metric(
                                "Breakeven Occupancy",
                                f"{breakeven_occupancy:.1f}%",
                                help="อัตราห้องว่างสูงสุดที่ยังคุ้มทุน"
                            )
                            current_occupancy = 100 - vacancy_rate
                            if breakeven_occupancy < current_occupancy:
                                st.caption(f"🟢 ปลอดภัย (ปัจจุบัน {current_occupancy:.1f}%)")
                            else:
                                st.caption(f"⚠️ เสี่ยง (ปัจจุบัน {current_occupancy:.1f}%)")
                        
                        with col_b2:
                            st.metric(
                                "Margin of Safety",
                                f"{margin_of_safety:.1f}%",
                                help="ระยะห่างจากจุดคุ้มทุน"
                            )
                            if margin_of_safety > 20:
                                st.caption("🟢 มีระยะปลอดภัยดี")
                            elif margin_of_safety > 10:
                                st.caption("🟡 ระยะปลอดภัยพอใช้")
                            else:
                                st.caption("🔴 ระยะปลอดภัยน้อย")
                        
                        # Overall Risk Interpretation
                        st.markdown("### 📋 Risk Interpretation")
                        
                        if risk_score >= 80:
                            st.success("""
                            **🟢 ความเสี่ยงต่ำ (Low Risk)**
                            
                            - NPV มีความมั่นคงสูง แม้ในสถานการณ์แย่
                            - ความผันผวนต่ำ ผลตอบแทนคาดการณ์ได้
                            - Breakeven occupancy ต่ำ มี margin of safety ดี
                            - **แนะนำ:** เหมาะสำหรับการลงทุน
                            """)
                        elif risk_score >= 50:
                            st.warning("""
                            **🟡 ความเสี่ยงปานกลาง (Moderate Risk)**
                            
                            - NPV มีความผันผวนปานกลาง
                            - ควรติดตามตัวแปรสำคัญ (ค่าเช่า, อัตราห้องว่าง)
                            - พิจารณาเจรจาราคาให้ต่ำลง
                            - **แนะนำ:** ระมัดระวัง มี safety margin เพียงพอ
                            """)
                        else:
                            st.error("""
                            **🔴 ความเสี่ยงสูง (High Risk)**
                            
                            - NPV ผันผวนมาก มีโอกาสขาดทุนสูง
                            - Breakeven occupancy ใกล้เคียงหรือสูงกว่าอัตราปัจจุบัน
                            - Expected NPV อาจต่ำกว่าที่คาดหวัง
                            - **แนะนำ:** พิจารณาทรัพย์สินอื่น หรือปรับโครงสร้างการเงิน
                            """)
                    
        with tab6:
            st.markdown("#### Investment Verdict")
            
            # Safety check: make sure results has 'irr' and 'npv' keys
            if 'irr' not in results or 'npv' not in results:
                st.warning("กรุณา Run Analysis ก่อนเพื่อดูคำแนะนำการลงทุน")
            elif results['irr'] > discount_rate and results['npv'] > 0:
                st.success("""
                    ### ✅ Strong Buy Signal
                    This investment looks promising based on your criteria.
                    
                    *   **IRR** exceeds your discount rate.
                    *   **NPV** is positive, indicating value creation.
                    *   **Cash Flow** is positive.
                """)
            elif results['irr'] > discount_rate:
                st.warning("""
                    ### ⚠️ Moderate Potential
                    The project has good returns but check the NPV.
                    
                    *   **IRR** is healthy.
                    *   **NPV** is marginal.
                    *   Consider negotiating a lower price.
                """)
            else:
                st.error("""
                    ### ❌ High Risk / Low Return
                    This investment does not meet your financial targets.
                    
                    *   **IRR** is below your required rate.
                    *   **NPV** is negative.
                    *   Consider looking for other properties.
                """)
                
            st.markdown("#### Sensitivity Analysis Tips")
            st.info("""
                Try adjusting these variables to see if the deal works:
                1.  **Offer Price**: Can you buy it cheaper?
                2.  **Rent**: Is the market rent higher?
                3.  **Financing**: Can you get a better interest rate?
            """)

    else:
        # Welcome State
        st.info("กรุณากรอกข้อมูลทรัพย์สินใน sidebar และกด 'Run Analysis' เพื่อเริ่มการวิเคราะห์")
        
        # Modern Feature Cards with custom CSS
        st.markdown("""
        <style>
        .feature-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin: 0.5rem 0;
            transition: transform 0.2s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
        }
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .feature-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #FFFFFF;
            margin: 0.5rem 0;
        }
        .feature-desc {
            font-size: 0.9rem;
            color: #E0E0E0;
            line-height: 1.4;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Feature Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon"></div>
                <div class="feature-title">Professional Analysis</div>
                <div class="feature-desc">วิเคราะห์ด้วยสูตรมาตรฐาน IRR, NPV, Cap Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="feature-icon"></div>
                <div class="feature-title">Interactive Charts</div>
                <div class="feature-desc">กราฟแบบ interactive พร้อม breakdown รายปี</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="feature-icon"></div>
                <div class="feature-title">Real-time Results</div>
                <div class="feature-desc">คำนวณทันที พร้อม sensitivity analysis</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
