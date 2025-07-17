import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

st.set_page_config(page_title="Extractor XML Facturas CR", layout="wide")
st.title("📄 Extractor de Facturas XML de Hacienda (v4.3)")
st.markdown("Subí uno o más archivos XML de facturas electrónicas de Costa Rica para extraer los datos clave.")

NS = {'h': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3/facturaElectronica'}

def extract_invoice_data(xml_content):
    root = ET.fromstring(xml_content)
    return {
        "Emisor": root.findtext(".//h:Emisor/h:Nombre", namespaces=NS),
        "Receptor": root.findtext(".//h:Receptor/h:Nombre", namespaces=NS),
        "Identificación Receptor": root.findtext(".//h:Receptor/h:Identificacion/h:Numero", namespaces=NS),
        "Fecha Emisión": root.findtext(".//h:FechaEmision", namespaces=NS),
        "Consecutivo": root.findtext(".//h:NumeroConsecutivo", namespaces=NS),
        "Moneda": root.findtext(".//h:ResumenFactura/h:CodigoTipoMoneda/h:CodigoMoneda", namespaces=NS),
        "Venta Neta": root.findtext(".//h:ResumenFactura/h:TotalVentaNeta", namespaces=NS),
        "Impuesto": root.findtext(".//h:ResumenFactura/h:TotalImpuesto", namespaces=NS),
        "Total Comprobante": root.findtext(".//h:ResumenFactura/h:TotalComprobante", namespaces=NS),
    }

uploaded_files = st.file_uploader("📁 Selecciona uno o más archivos XML", type="xml", accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)} archivo(s) cargado(s).")

    if st.button("🚀 Procesar Facturas"):
        resultados = []
        for archivo in uploaded_files:
            try:
                contenido = archivo.read()
                data = extract_invoice_data(contenido)
                data["Archivo"] = archivo.name
                resultados.append(data)
            except Exception as e:
                st.error(f"❌ Error procesando {archivo.name}: {e}")

        if resultados:
            df = pd.DataFrame(resultados)
            st.markdown("### 📊 Resultados")
            st.dataframe(df, use_container_width=True)

            def to_excel_bytes(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Facturas")
                return output.getvalue()

            excel_bytes = to_excel_bytes(df)
            st.download_button(
                label="📥 Descargar Excel",
                data=excel_bytes,
                file_name="facturas_extraidas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
