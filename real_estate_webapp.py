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
    st.set_page_config(
        page_title="Real Estate Pro Calculator",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
        <style>
        /* Main Container */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-color: #6366f1;
            transition: all 0.2s ease;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1f2937;
            font-family: 'Inter', sans-serif;
        }
        
        /* Custom Button */
        .stButton>button {
            background: linear-gradient(to right, #4f46e5, #7c3aed);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(to right, #4338ca, #6d28d9);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            transform: translateY(-1px);
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #f9fafb;
            border-right: 1px solid #e5e7eb;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px;
            color: #4b5563;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #eef2ff;
            color: #4f46e5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header Section
    st.title("🏢 Real Estate Feasibility Pro")
    st.markdown("Professional Financial Analysis Tool for Real Estate Investors")
    
    st.divider()
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # JavaScript for auto-formatting numbers
        st.markdown("""
        <script>
        function autoFormatNumber() {
            // Find all text inputs that should be formatted
            const priceInput = document.querySelector('[data-testid="stTextInput"] input');
            
            if (priceInput && !priceInput.dataset.formatted) {
                priceInput.dataset.formatted = 'true';
                
                priceInput.addEventListener('blur', function() {
                    let value = this.value.replace(/,/g, '');
                    
                    if (!isNaN(value) && value !== '') {
                        // Format with thousand separators and 2 decimals
                        let num = parseFloat(value);
                        this.value = num.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                    }
                });
                
                priceInput.addEventListener('focus', function() {
                    // Remove commas when editing
                    this.value = this.value.replace(/,/g, '');
                });
            }
        }
        
        // Run on load and after updates
        setInterval(autoFormatNumber, 500);
        </script>
        """, unsafe_allow_html=True)
        
        with st.expander("🏠 Property Details", expanded=True):
            property_price_str = st.text_input(
                "ราคาทรัพย์สิน (Property Price)",
                value="5000000",
                help="กรอกตัวเลขอย่างเดียว - จะ format อัตโนมัติเป็น 5,000,000.00",
                key="property_price_input",
                placeholder="เช่น: 5000000"
            )
            
            # Convert to number
            try:
                property_price = float(property_price_str.replace(',', ''))
            except:
                property_price = 5000000.0
            
            down_payment = st.number_input(
                "เงินดาวน์ (Down Payment)",  
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                help="สัดส่วนเงินดาวน์ต่อราคาทรัพย์สิน"
            )
            st.caption(f"📊 **{down_payment}%** = ฿{property_price * down_payment / 100:,.0f}")
        
        with st.expander("💳 Financing", expanded=True):
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
            monthly_rent_str = st.text_input(
                "ค่าเช่ารายเดือน (Monthly Rent)", 
                value="15000",
                help="กรอกตัวเลขอย่างเดียว - จะ format อัตโนมัติเป็น 15,000.00",
                key="monthly_rent_input",
                placeholder="เช่น: 15000"
            )
            
            try:
                monthly_rent = float(monthly_rent_str.replace(',', ''))
            except:
                monthly_rent = 15000.0
            
            monthly_expenses_str = st.text_input(
                "ค่าใช้จ่ายรายเดือน (Monthly Expenses)", 
                value="3000",
                help="กรอกตัวเลขอย่างเดียว - จะ format อัตโนมัติเป็น 3,000.00",
                key="monthly_expenses_input",
                placeholder="เช่น: 3000"
            )
            
            try:
                monthly_expenses = float(monthly_expenses_str.replace(',', ''))
            except:
                monthly_expenses = 3000.0
            
            vacancy_rate = st.number_input(
                "อัตราห้องว่าง (Vacancy Rate)", 
                min_value=0,
                max_value=100,
                value=5,
                step=1,
                help="เปอร์เซ็นต์ของเวลาที่ไม่มีผู้เช่า"
            )
            st.caption("🏚️ หน่วย: **เปอร์เซ็นต์ (%)** | ตัวอย่าง: 5% = ว่าง 0.6 เดือน/ปี")
        
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
            st.caption("📈 หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)**")
            
            appreciation = st.number_input(
                "การเพิ่มมูลค่า (Annual Appreciation)", 
                min_value=0.0,
                max_value=20.0,
                value=3.0,
                step=0.5,
                help="เปอร์เซ็นต์การเพิ่มมูลค่าทรัพย์สินต่อปี",
                format="%.1f"
            )
            st.caption("🏠 หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)**")
        
        with st.expander("⏱️ Timeline & Exit", expanded=False):
            holding_period = st.number_input(
                "ระยะเวลาถือครอง (Holding Period)", 
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                help="จำนวนปีที่ถือครองก่อนขาย"
            )
            st.caption("⏳ หน่วย: **ปี (Years)**")
            
            selling_costs = st.number_input(
                "ค่าใช้จ่ายในการขาย (Selling Costs)", 
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="เปอร์เซ็นต์ของราคาขาย (ค่านายหน้า, ภาษี, ฯลฯ)",
                format="%.1f"
            )
            st.caption("💼 หน่วย: **เปอร์เซ็นต์ของราคาขาย (%)** | รวม: นายหน้า, ภาษี, โอน")
            
            discount_rate = st.number_input(
                "อัตราคิดลด (Discount Rate)", 
                min_value=0.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="อัตราผลตอบแทนที่ต้องการ (สำหรับคำนวณ NPV)",
                format="%.1f"
            )
            st.caption("🎯 หน่วย: **เปอร์เซ็นต์ต่อปี (%/year)** | อัตราผลตอบแทนที่คาดหวัง")
        
        st.markdown("---")
        calculate_btn = st.button("🚀 Run Analysis", use_container_width=True)

    # Main Dashboard
    if calculate_btn:
        calculator = RealEstateFeasibilityCalculator()
        
        with st.spinner('Crunching numbers...'):
            results = calculator.comprehensive_analysis(
                property_price, down_payment, loan_term, interest_rate,
                monthly_rent, monthly_expenses, vacancy_rate, rent_increase,
                holding_period, appreciation, selling_costs, discount_rate
            )
        
        # 1. Executive Summary Cards
        st.markdown("### 🎯 Executive Summary")
        
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Dashboard", 
            "📋 Detailed Data", 
            "📈 Sensitivity", 
            "🎯 Scenarios",
            "⚠️ Risk",
            "💡 Recommendation"
        ])
        
        with tab1:
            # Interactive Chart
            st.plotly_chart(create_interactive_chart(results['cash_flow_table']), use_container_width=True)
            
            # Secondary Metrics
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
            # Sensitivity Analysis Tab
            st.markdown("#### 📈 Sensitivity Analysis")
            st.caption("ดูว่าตัวแปรไหนมีผลต่อ NPV มากที่สุด (Tornado Chart)")
            
            if not ADVANCED_ANALYSIS_AVAILABLE:
                st.warning("โมดูล Analysis ยังไม่พร้อม - กำลังพัฒนา")
            else:
                # Convert to DCF parameters
                dcf_params = {
                    'initial_investment': results['initial_investment'],
                    'timeline_years': holding_period,
                    'discount_rate': discount_rate / 100,
                    'rental_rate_per_unit': monthly_rent,
                    'number_of_units': 1,  # Single unit
                    'vacancy_rate_early': vacancy_rate / 100,
                    'vacancy_rate_normal': vacancy_rate / 100,
                    'revenue_growth_rate': rent_increase / 100,
                    'other_income_pct': 0,
                    'operating_expense_pct': monthly_expenses / monthly_rent if monthly_rent > 0 else 0,
                    'cap_rate': 0.05
                }
                
                # Key variables to analyze
                test_vars = ['rental_rate_per_unit', 'vacancy_rate_normal', 'revenue_growth_rate']
                
                if st.button("🔍 Run Sensitivity Analysis"):
                    with st.spinner("Analyzing impact..."):
                        try:
                            analyzer = SensitivityAnalyzer(dcf_params)
                            results_dict = analyzer.analyze_multiple(test_vars, range_pct=0.2)
                            impact_df = analyzer.calculate_impact(results_dict)
                            
                            # Tornado Chart
                            fig = go.Figure()
                            impact_df = impact_df.sort_values('npv_range', ascending=True)
                            
                            for _, row in impact_df.iterrows():
                                low = (row['npv_min'] - row['base_npv']) / 1e6
                                high = (row['npv_max'] - row['base_npv']) / 1e6
                                
                                fig.add_trace(go.Bar(
                                    name=row['variable'],
                                    y=[row['variable']],
                                    x=[abs(high - low)],
                                    orientation='h',
                                    marker_color='#4f46e5',
                                    text=[f"{abs(high - low):.1f}M"],
                                    textposition='auto'
                                ))
                            
                            fig.update_layout(
                                title="<b>Tornado Chart - Variable Impact on NPV</b>",
                                xaxis_title="NPV Impact Range (Million THB)",
                                yaxis_title="Variable",
                                height=400,
                                showlegend=False,
                                template="plotly_white"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Impact table
                            st.caption("**การแปลผล:** ตัวแปรที่อยู่บนสุด = มีผลต่อ NPV มากที่สุด")
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with tab4:
            # Scenario Comparison Tab
            st.markdown("#### 🎯 Scenario Comparison")
            st.caption("เปรียบเทียบ Base / Best / Worst case")
            
            if not ADVANCED_ANALYSIS_AVAILABLE:
                st.info("Coming soon - Scenario analysis")
            else:
                if st.button("📊 Generate Scenarios"):
                    with st.spinner("Creating scenarios..."):
                        try:
                            manager = ScenarioManager(dcf_params)
                            manager.create_best_case()
                            manager.create_worst_case()
                            comparison = manager.compare_scenarios()
                            
                            # Show table
                            st.dataframe(comparison, use_container_width=True, hide_index=True)
                            
                            # Charts
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig_npv = go.Figure()
                                colors = ['#3b82f6', '#10b981', '#ef4444']
                                fig_npv.add_trace(go.Bar(
                                    x=comparison['Scenario'],
                                    y=comparison['NPV (M)'],
                                    marker_color=colors,
                                    text=comparison['NPV (M)'].apply(lambda x: f"{x:.1f}M"),
                                    textposition='auto'
                                ))
                                fig_npv.update_layout(
                                    title="NPV เปรียบเทียบ",
                                    height=300,
                                    template="plotly_white"
                                )
                                st.plotly_chart(fig_npv, use_container_width=True)
                            
                            with col2:
                                fig_irr = go.Figure()
                                fig_irr.add_trace(go.Bar(
                                    x=comparison['Scenario'],
                                    y=comparison['IRR (%)'],
                                    marker_color=colors,
                                    text=comparison['IRR (%)'].apply(lambda x: f"{x:.1f}%"),
                                    textposition='auto'
                                ))
                                fig_irr.update_layout(
                                    title="IRR เปรียบเทียบ",
                                    height=300,
                                    template="plotly_white"
                                )
                                st.plotly_chart(fig_irr, use_container_width=True)
                        
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with tab5:
            # Risk Assessment Tab
            st.markdown("#### ⚠️ Risk Assessment")
            st.caption("ประเมินความเสี่ยงของการลงทุน")
            
            if not ADVANCED_ANALYSIS_AVAILABLE:
                st.info("Coming soon - Risk analysis")
            else:
                if st.button("🎲 Assess Risk"):
                    with st.spinner("Calculating risk metrics..."):
                        try:
                            assessor = RiskAssessment(dcf_params)
                            risk = assessor.risk_score()
                            
                            # Risk score display
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                score = risk['total_score']
                                if score >= 80:
                                    emoji = "🟢"
                                elif score >= 50:
                                    emoji = "🟡"
                                else:
                                    emoji = "🔴"
                                
                                st.metric("Risk Score", f"{score:.0f}/100 {emoji}")
                                st.caption(f"Grade: {risk['grade']}")
                            
                            with col2:
                                be_rate = assessor.break_even_irr()
                                st.metric("Break-Even Rate", f"{be_rate:.2%}")
                                st.caption(f"Margin: {(be_rate - discount_rate/100)*100:.1f}%")
                            
                            with col3:
                                st.caption(risk['interpretation'])
                            
                            # Factor breakdown
                            st.markdown("**Risk Factors:**")
                            factor_df = pd.DataFrame(risk['factors'])
                            
                            fig = go.Figure()
                            fig.add_trace(go.Bar(
                                x=factor_df['factor'],
                                y=factor_df['score'],
                                marker_color='#6366f1',
                                text=factor_df['score'].apply(lambda x: f"{x:.0f}"),
                                textposition='auto'
                            ))
                            fig.update_layout(
                                yaxis_title="Score",
                                height=300,
                                template="plotly_white",
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        except Exception as e:
                            st.error(f"Error: {e}")
            
        with tab6:
            st.markdown("#### Investment Verdict")
            
            if results['irr'] > discount_rate and results['npv'] > 0:
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
        st.info("👈 กรุณากรอกข้อมูลทรัพย์สินใน sidebar และกด 'Run Analysis' เพื่อเริ่มการวิเคราะห์")
        
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
                <div class="feature-icon">📊</div>
                <div class="feature-title">Professional Analysis</div>
                <div class="feature-desc">วิเคราะห์ด้วยสูตรมาตรฐาน IRR, NPV, Cap Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="feature-icon">📈</div>
                <div class="feature-title">Interactive Charts</div>
                <div class="feature-desc">กราฟแบบ interactive พร้อม breakdown รายปี</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">Real-time Results</div>
                <div class="feature-desc">คำนวณทันที พร้อม sensitivity analysis</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
