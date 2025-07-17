import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
from email.message import EmailMessage
import smtplib

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class PurchaseOrderManager:
    def __init__(self, excel_file="purchase_orders.xlsx"):
        self.excel_file = excel_file
        self.columns = [
            "PO Number", "Date", "Vendor Name", "Items Ordered",
            "Total Amount", "Status", "Expected Delivery",
            "Payment Terms", "Mode of Payment", "Contact Person", "Remarks",
            "Attachment"
        ]
        self.initialize_excel()

    def initialize_excel(self):
        if not os.path.exists(self.excel_file):
            df = pd.DataFrame(columns=self.columns)
            df.to_excel(self.excel_file, index=False)
        else:
            df = pd.read_excel(self.excel_file)
            for col in self.columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[self.columns]
            df.to_excel(self.excel_file, index=False)

    def get_data(self):
        df = pd.read_excel(self.excel_file)
        for col in self.columns:
            if col not in df.columns:
                df[col] = ""
        return df[self.columns]

    def save_data(self, df):
        df.to_excel(self.excel_file, index=False)

    def add_po(self, **kwargs):
        df = self.get_data()
        df = pd.concat([df, pd.DataFrame([kwargs])], ignore_index=True)
        self.save_data(df)
        st.success("✅ Purchase Order added successfully!")

    def update_po(self, index, updated_entry):
        df = self.get_data()
        df.loc[index] = updated_entry
        self.save_data(df)
        st.success("✅ Purchase Order updated successfully!")

    def delete_po(self, index):
        df = self.get_data()
        df = df.drop(index)
        self.save_data(df)
        st.success("🗑️ Purchase Order deleted successfully!")

    def generate_pdf(self, po_data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Purchase Order", ln=True, align='C')
        for key, value in po_data.items():
            if key != "Attachment":
                pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
        path = f"PO_{po_data['PO Number']}.pdf"
        pdf.output(path)
        return path

    def send_email_with_attachment(self, receiver, subject, body, filepath):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = "you@example.com"
        msg["To"] = receiver
        msg.set_content(body)

        with open(filepath, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(filepath))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("you@example.com", "yourpassword")
            server.send_message(msg)

def main():
    st.set_page_config(page_title="📜 Purchase Order Manager", layout="wide")
    st.title("📋 Purchase Order Management System")

    manager = PurchaseOrderManager()
    menu = st.sidebar.radio("🔍 Navigation", ["➕ Add PO", "📄 View/Edit PO", "📊 Summary"])

    df = manager.get_data()

    if menu == "➕ Add PO":
        st.subheader("📝 Add New Purchase Order")

        col1, col2, col3 = st.columns(3)
        with col1:
            po_number = st.text_input("PO Number")
            date = st.date_input("Date", value=datetime.today())
            vendor_name = st.text_input("Vendor Name")

        with col2:
            status = st.selectbox("Status", ["Pending", "Approved", "Delivered"])
            expected_delivery = st.date_input("Expected Delivery", value=datetime.today())
            payment_terms = st.text_input("Payment Terms")

        with col3:
            mode_of_payment = st.text_input("Mode of Payment")
            contact_person = st.text_input("Contact Person")
            total_amount = st.number_input("Total Amount", min_value=0.0, step=0.01)

        items_ordered = st.text_area("📦 Items Ordered")
        remarks = st.text_area("Remarks")
        attachment = st.file_uploader("📎 Upload Attachment", type=["pdf", "png", "jpg"])
        attachment_path = ""

        if attachment:
            attachment_path = os.path.join(UPLOAD_FOLDER, attachment.name)
            with open(attachment_path, "wb") as f:
                f.write(attachment.read())

        if st.button("🚀 Submit Purchase Order", use_container_width=True):
            if po_number and vendor_name:
                manager.add_po(
                    **{
                        "PO Number": po_number,
                        "Date": date.strftime("%Y-%m-%d"),
                        "Vendor Name": vendor_name,
                        "Items Ordered": items_ordered,
                        "Total Amount": total_amount,
                        "Status": status,
                        "Expected Delivery": expected_delivery.strftime("%Y-%m-%d"),
                        "Payment Terms": payment_terms,
                        "Mode of Payment": mode_of_payment,
                        "Contact Person": contact_person,
                        "Remarks": remarks,
                        "Attachment": attachment_path
                    }
                )
            else:
                st.error("❗ PO Number and Vendor Name are required fields.")

    elif menu == "📄 View/Edit PO":
        st.subheader("🔍 View & Edit Purchase Orders")

        with st.expander("🔎 Filter"):
            po_filter = st.text_input("Search by PO Number")
            vendor_filter = st.text_input("Search by Vendor Name")
            date_filter = st.date_input("Search by Date", value=None)

            if po_filter:
                df = df[df["PO Number"].astype(str).str.contains(po_filter, case=False)]
            if vendor_filter:
                df = df[df["Vendor Name"].str.contains(vendor_filter, case=False)]
            if isinstance(date_filter, datetime):
                df = df[pd.to_datetime(df["Date"]).dt.date == date_filter]

        st.dataframe(df, use_container_width=True)

        if not df.empty:
            index = st.number_input("Enter PO Index to Edit/Delete", min_value=0, max_value=len(df)-1)
            selected = df.iloc[index]

            st.markdown("### ✏️ Edit Selected Purchase Order")
            col1, col2, col3 = st.columns(3)
            with col1:
                po_number = st.text_input("PO Number", value=selected["PO Number"])
                date = st.date_input("Date", value=pd.to_datetime(selected["Date"]))
                vendor_name = st.text_input("Vendor Name", value=selected["Vendor Name"])

            with col2:
                status = st.selectbox("Status", ["Pending", "Approved", "Delivered"], index=["Pending", "Approved", "Delivered"].index(selected["Status"]))
                expected_delivery = st.date_input("Expected Delivery", value=pd.to_datetime(selected["Expected Delivery"]))
                payment_terms = st.text_input("Payment Terms", value=selected["Payment Terms"])

            with col3:
                mode_of_payment = st.text_input("Mode of Payment", value=selected["Mode of Payment"])
                contact_person = st.text_input("Contact Person", value=selected["Contact Person"])
                total_amount = st.number_input("Total Amount", value=float(selected["Total Amount"]))

            items_ordered = st.text_area("Items Ordered", value=selected["Items Ordered"])
            remarks = st.text_area("Remarks", value=selected["Remarks"])
            attachment = selected["Attachment"]

            if st.button("💾 Update PO"):
                updated = {
                    "PO Number": po_number,
                    "Date": date.strftime("%Y-%m-%d"),
                    "Vendor Name": vendor_name,
                    "Items Ordered": items_ordered,
                    "Total Amount": total_amount,
                    "Status": status,
                    "Expected Delivery": expected_delivery.strftime("%Y-%m-%d"),
                    "Payment Terms": payment_terms,
                    "Mode of Payment": mode_of_payment,
                    "Contact Person": contact_person,
                    "Remarks": remarks,
                    "Attachment": attachment
                }
                manager.update_po(index, updated)

            if st.button("🗑️ Delete PO", type="secondary"):
                manager.delete_po(index)

            if st.button("📤 Export as PDF"):
                pdf_path = manager.generate_pdf(selected.to_dict())
                st.success(f"PDF saved at {pdf_path}")

            if st.button("✉️ Send Email"):
                email = st.text_input("Vendor Email")
                if email:
                    pdf_path = manager.generate_pdf(selected.to_dict())
                    manager.send_email_with_attachment(email, "Your Purchase Order", "Attached is your purchase order.", pdf_path)
                    st.success("Email sent successfully!")

    elif menu == "📊 Summary":
        st.subheader("📈 Purchase Order Summary")
        if df.empty:
            st.info("ℹ️ No data to summarize.")
        else:
            status_summary = df.groupby("Status")["Total Amount"].sum()
            st.bar_chart(status_summary)
            st.dataframe(
                status_summary.reset_index().rename(columns={"Total Amount": "Total Value"})
            )

if __name__ == "__main__":
    main()
