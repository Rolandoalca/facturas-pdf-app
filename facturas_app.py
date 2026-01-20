import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

# -------------------------------------------------
# Configuración Streamlit
# -------------------------------------------------
st.set_page_config(
    page_title="Extractor XML Facturas CR",
    layout="wide"
)

st.title("📄 Extractor de Facturas XML de Hacienda (CR)")
st.markdown(
    "Suba uno o más archivos XML de facturas electrónicas "
    "de Costa Rica (v4.3 / v4.4 – TRIBU-CR) para extraer la información principal."
)

# -------------------------------------------------
# Utilidades XML
# -------------------------------------------------
def get_namespace(root):
    """
    Detecta automáticamente el namespace del XML
    (v4.3, v4.4 o futuras versiones).
    """
    if root.tag.startswith("{"):
        return root.tag.split("}")[0].strip("{")
    return ""


def extract_invoice_data(xml_content):
    """
    Extrae los datos principales de una Factura Electrónica CR
    compatible con v4.3 y v4.4.
    """
    root = ET.fromstring(xml_content)

    ns_uri = get_namespace(root)
    NS = {"h": ns_uri} if ns_uri else {}

    def xt(path):
        return root.findtext(path, namespaces=NS)

    return {
        "Emisor": xt(".//h:Emisor/h:Nombre"),
        "Receptor": xt(".//h:Receptor/h:Nombre"),
        "Identificación Receptor": xt(".//h:Receptor/h:Identificacion/h:Numero"),
        "Fecha Emisión": xt(".//h:FechaEmision"),
        "Consecutivo": xt(".//h:NumeroConsecutivo"),
        "Moneda": xt(".//h:ResumenFactura/h:CodigoTipoMoneda/h:CodigoMoneda"),
        "Venta Neta": xt(".//h:ResumenFactura/h:TotalVentaNeta"),
        "Impuesto": xt(".//h:ResumenFactura/h:TotalImpuesto") or "0",
        "Total Comprobante": xt(".//h:ResumenFactura/h:TotalComprobante"),
        "Namespace Detectado": ns_uri,
    }


# -------------------------------------------------
# Carga de archivos
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "📁 Seleccione uno o más archivos XML",
    type="xml",
    accept_multiple_files=True
)

# -------------------------------------------------
# Procesamiento
# -------------------------------------------------
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

            # -------------------------------------------------
            # Exportar a Excel
            # -------------------------------------------------
            def to_excel_bytes(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    dataframe.to_excel(
                        writer,
                        index=False,
                        sheet_name="Facturas"
                    )
                return output.getvalue()

            excel_bytes = to_excel_bytes(df)

            st.download_button(
                label="📥 Descargar Excel",
                data=excel_bytes,
                file_name="facturas_extraidas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
