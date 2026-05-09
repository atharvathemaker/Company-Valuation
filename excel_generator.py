import pandas as pd
import io

def create_excel_model(df_historical, metric_choice, tax_rate, 
                       rfr, beta, erp, size_premium, csrp, ke, total_debt, total_equity, kd, wacc, 
                       term_growth, df_growth_rates, liquidity_discount):
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        fmt_bold = workbook.add_format({'bold': True})
        fmt_pct = workbook.add_format({'num_format': '0.00%'})
        fmt_currency = workbook.add_format({'num_format': '$#,##0.00'})
        fmt_header = workbook.add_format({'bold': True, 'bottom': 1})
        
        # Sheet 1: Dashboard & Valuation
        ws = workbook.add_worksheet("Valuation Model")
        
        # Section 1: WACC Inputs
        ws.write("A1", "1. WACC Assumptions", fmt_bold)
        
        ws.write("A3", "Risk Free Rate")
        ws.write("B3", rfr, fmt_pct)
        ws.write("A4", "Beta")
        ws.write("B4", beta)
        ws.write("A5", "Equity Risk Premium")
        ws.write("B5", erp, fmt_pct)
        ws.write("A6", "Size Premium")
        ws.write("B6", size_premium, fmt_pct)
        ws.write("A7", "Company Specific Risk Premium")
        ws.write("B7", csrp, fmt_pct)
        ws.write("A8", "Cost of Equity (Ke)")
        ws.write_formula("B8", "=B3+(B4*B5)+B6+B7", fmt_pct)
        
        ws.write("A10", "Total Debt")
        ws.write("B10", total_debt, fmt_currency)
        ws.write("A11", "Total Equity")
        ws.write("B11", total_equity, fmt_currency)
        ws.write("A12", "Total Capital")
        ws.write_formula("B12", "=B10+B11", fmt_currency)
        
        ws.write("A13", "Cost of Debt (Kd)")
        ws.write("B13", kd, fmt_pct)
        ws.write("A14", "Tax Rate")
        ws.write("B14", tax_rate, fmt_pct)
        
        ws.write("A16", "WACC")
        # WACC = (E/V)*Ke + (D/V)*Kd*(1-T)
        ws.write_formula("B16", "=(B11/B12)*B8 + (B10/B12)*B13*(1-B14)", fmt_pct)
        
        # Section 2: Historical Financials
        ws.write("D1", "2. Historical Financials", fmt_bold)
        
        headers = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
        for col_idx, h in enumerate(headers):
            ws.write(2, 4 + col_idx, h, fmt_header)
            
        row_idx = 3
        for item in df_historical.index:
            ws.write(row_idx, 3, item)
            for col_idx, yr in enumerate(headers):
                ws.write(row_idx, 4 + col_idx, df_historical.loc[item, yr], fmt_currency)
            row_idx += 1
            
        # Add FCFF Calculation
        ws.write(row_idx, 3, "FCFF", fmt_bold)
        
        # For simplicity in this advanced model, we will write the static calculated values 
        # for FCFF instead of complex excel NWC tracking to avoid formula breaks, 
        # but we provide the raw data in the rows above.
        cols = ['E', 'F', 'G', 'H', 'I']
        # We can calculate the NWC dynamically if we want, but since it depends on the previous year's column
        # it requires specific row index knowledge.
        
        # We will map the Python-calculated historical FCFF directly to the cells to ensure exact match.
        # But for projections we use excel formulas.
        for col_idx, yr in enumerate(df_historical.columns):
            # In a robust model, you'd write the exact `=E4+...-(E7-D7)` here, 
            # For brevity, we pass the python calculated FCFF into historical.
            # In production, this can be expanded to full Excel logic mapping.
            pass
            
        # Write the python calculated historical FCFF into the row
        from app import historical_fcff
        for i, val in enumerate(historical_fcff):
            ws.write(row_idx, 4+i, val, fmt_currency)
            
        fcff_row = row_idx + 1
        
        # Section 3: Projections
        ws.write("A18", "3. Valuation", fmt_bold)
        ws.write("A20", "Terminal Growth Rate")
        ws.write("B20", term_growth, fmt_pct)
        ws.write("A21", "Liquidity Discount")
        ws.write("B21", liquidity_discount, fmt_pct)
        
        # Write growth rate headers and values
        ws.write("D18", "Proj Y1", fmt_header)
        ws.write("E18", "Proj Y2", fmt_header)
        ws.write("F18", "Proj Y3", fmt_header)
        ws.write("G18", "Proj Y4", fmt_header)
        ws.write("H18", "Proj Y5", fmt_header)
        
        ws.write("C19", "Projection Growth Rate")
        for i, val in enumerate(df_growth_rates.iloc[0]):
            ws.write(18, 3+i, val/100.0, fmt_pct) # write as decimal
            
        ws.write("C20", "Projected FCFF")
        
        # Proj Y1 = Year 5 * (1 + g) -> I{fcff_row} * (1 + D19)
        ws.write_formula("D20", f"=I{fcff_row}*(1+D19)", fmt_currency)
        ws.write_formula("E20", f"=D20*(1+E19)", fmt_currency)
        ws.write_formula("F20", f"=E20*(1+F19)", fmt_currency)
        ws.write_formula("G20", f"=F20*(1+G19)", fmt_currency)
        ws.write_formula("H20", f"=G20*(1+H19)", fmt_currency)
        
        # Discount Factors
        ws.write("C21", "Discount Factor")
        ws.write_formula("D21", "=1/((1+$B$16)^1)", fmt_pct)
        ws.write_formula("E21", "=1/((1+$B$16)^2)", fmt_pct)
        ws.write_formula("F21", "=1/((1+$B$16)^3)", fmt_pct)
        ws.write_formula("G21", "=1/((1+$B$16)^4)", fmt_pct)
        ws.write_formula("H21", "=1/((1+$B$16)^5)", fmt_pct)
        
        ws.write("C22", "PV of FCFF")
        ws.write_formula("D22", "=D20*D21", fmt_currency)
        ws.write_formula("E22", "=E20*E21", fmt_currency)
        ws.write_formula("F22", "=F20*F21", fmt_currency)
        ws.write_formula("G22", "=G20*G21", fmt_currency)
        ws.write_formula("H22", "=H20*H21", fmt_currency)
        
        ws.write("C24", "Terminal Value")
        # TV = (ProjY5 * (1+g_term)) / (WACC - g_term)
        ws.write_formula("D24", "=(H20*(1+$B$20))/($B$16-$B$20)", fmt_currency)
        ws.write("C25", "PV of Terminal Value")
        ws.write_formula("D25", "=D24*H21", fmt_currency)
        
        ws.write("C27", "Enterprise Value", fmt_bold)
        ws.write_formula("D27", "=SUM(D22:H22)+D25", fmt_currency)
        ws.write("C28", "Implied Equity Value (Pre-Discount)", fmt_bold)
        ws.write_formula("D28", "=D27-$B$10", fmt_currency)
        ws.write("C29", "Final Equity Value", fmt_bold)
        ws.write_formula("D29", "=D28*(1-$B$21)", fmt_currency)
        
        # Set column widths
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 20)
        ws.set_column('D:I', 15)

    return output.getvalue()
