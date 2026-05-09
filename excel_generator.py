import pandas as pd
import io

def generate_excel(df, growth, wacc):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Valuation')
    
    workbook = writer.book
    worksheet = writer.sheets['Valuation']
    
    # Example of adding a dynamic formula to a cell
    worksheet.write('A10', 'Terminal Value')
    worksheet.write_formula('B10', '=B5*(1+0.02)/(0.10-0.02)') # Simplified example
    
    writer.close()
    return output.getvalue()
