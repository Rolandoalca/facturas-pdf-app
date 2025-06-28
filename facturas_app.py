import streamlit as st
import pandas as pd
import fitz  # PyMuPDF para leer PDFs
import re
import io

def extract_data_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    # Buscar número de factura
    num_factura = re.search(r'FACTURA ELECTRÓNICA ?[:#]?\s*(\d+)', text)
    if not num_factura:
        num_factura = re.search(r'Numero Consecutivo[:#]?\s*(\d+)', text)
    numero = num_factura.group(1) if num_factura else "No encontrado"

    # Buscar monto sin impuesto
    monto_sin_iva = re.search(r'(?:SUBTOTAL|MONTO GRAVADO|MERCADERIA GRAVADA)\s*[:₡]*\s*([\d.,]+)', text)
    monto = monto_sin_iva.group(1).replace(",", "") if monto_sin_iva else "0"

    # Buscar IVA
    iva_match = re.search(r'IVA\s*[:₡]*\s*([\d.,]+)', text)
    iva = iva_match.group(1).replace(",", "") if iva_match else "0"

    try:
        monto_float = float(monto)
        iva_float = float(iva)
    except:
        monto_float = 0.0
        iva_float = 0.0

    return numero, monto_float, iva_float

st.title("Extractor de Facturas PDF")

uploaded_files = st.file_uploader("Cargar archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    data = []
    for pdf_file in uploaded_files:
        numero, monto, iva = extract_data_from_pdf(pdf_file)
        data.append({
            "Archivo": pdf_file.name,
            "Número de factura": numero,
            "Monto sin IVA": monto,
            "IVA": iva
        })

    df = pd.DataFrame(data)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("Descargar CSV", csv, "facturas.csv", "text/csv")

    # Crear buffer para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturas')
    excel_data = output.getvalue()

    st.download_button(
        "Descargar Excel",
        excel_data,
        "facturas.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )