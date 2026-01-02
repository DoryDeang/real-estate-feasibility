"""
Custom Number Input Component with Thousand Separators
"""
import streamlit as st
import streamlit.components.v1 as components


def number_input_with_commas(label, value=0, min_value=None, max_value=None, step=1, key=None, help=None):
    """
    Custom number input that displays thousand separators
    """
    
    # Create unique key
    input_key = key or f"num_input_{label}"
    
    # HTML/JavaScript for formatted input
    html_code = f"""
    <div style="margin-bottom: 1rem;">
        <label style="font-size: 0.875rem; font-weight: 600; color: rgba(255, 255, 255, 0.87);">
            {label}
        </label>
        <input 
            type="text" 
            id="{input_key}"
            value="{value:,.0f}" 
            style="
                width: 100%;
                padding: 0.5rem 0.75rem;
                font-size: 1rem;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
                border-radius: 0.25rem;
                margin-top: 0.25rem;
            "
            onkeyup="formatNumber(this)"
            onchange="updateStreamlit('{input_key}', this.value)"
        />
        <small style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem;">
            {help or ''}
        </small>
    </div>
    
    <script>
    function formatNumber(input) {{
        // Remove all non-digit characters
        let value = input.value.replace(/[^0-9]/g, '');
        
        // Add thousand separators
        if (value) {{
            value = parseInt(value).toLocaleString('en-US');
        }}
        
        input.value = value;
    }}
    
    function updateStreamlit(key, value) {{
        // Remove commas and send to Streamlit
        let numValue = value.replace(/,/g, '');
        window.parent.postMessage({{
            type: 'streamlit:setComponentValue',
            key: key,
            value: parseInt(numValue) || 0
        }}, '*');
    }}
    </script>
    """
    
    # Display component
    result = components.html(html_code, height=100)
    
    # Return the value (from session state if available)
    if input_key in st.session_state:
        return st.session_state[input_key]
    else:
        return value
