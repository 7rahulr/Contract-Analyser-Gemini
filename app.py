import streamlit as st
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv
import os
import io
from docx import Document
from PyPDF2 import PdfReader

# Load API key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Initialize the Gemini Pro model
# Using a stable, recommended model
model = genai.GenerativeModel('gemini-1.5-flash')

def get_gemini_response(input_text):
    """Sends the contract text to the Gemini API and returns the parsed JSON response."""
    
    # Comprehensive prompt for the Gemini model to extract all required information
    # The prompt is updated to specifically ask for the 'End of Contract' field.
    prompt = f"""
    You are an expert contract analyzer. Your task is to analyze the following contract text and extract key insights.
    
    The output should be a single JSON object with the following structure:
    {{
      "Contract Type": "The type of agreement (e.g., Service Agreement, Lease, NDA).",
      "Address": "The address mentioned in the contract.",
      "Entry Date": "The date the contract was entered into.",
      "Contract Party": "The names of the parties involved in the contract.",
      "Termination Date": "Any date or clause specifying when the contract can be terminated.",
      "End of Contract": "The specific end date or duration of the contract.",
      "Executive Summary": "A concise summary of the contract's purpose and key terms.",
      "Scope of Service": "A description of the services or work to be performed.",
      "Responsibilities for Deliverables": "A summary of each party's responsibilities and the deliverables they are accountable for.",
      "Payment Schedule": "Details on how and when payments will be made.",
      "Tax Compliance": "Any clauses related to tax responsibilities and compliance.",
      "Important Dates and Deadlines": "A list of all significant dates and deadlines mentioned in the contract.",
      "Termination Clauses": "Conditions under which the contract can be terminated by either party.",
      "Confidentiality and Non-Compete Clause": "Details of any confidentiality agreements and non-compete restrictions.",
      "Clauses Presence": {{
        "Commercial": {{
          "Payment Terms": "Yes/No",
          "IP": "Yes/No",
          "Delivery Time": "Yes/No",
          "Warranty": "Yes/No"
        }},
        "Legal": {{
          "Indemnification": "Yes/No",
          "Termination": "Yes/No",
          "Confidentiality": "Yes/No",
          "Limitation of Liability": "Yes/No"
        }}
      }}
    }}
    
    Analyze the following contract text:
    ---
    {input_text}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        # The API might sometimes add extra text before/after the JSON.
        json_match = re.search(r'```json\n(.*)\n```', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.text
            
        return json.loads(json_str)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def extract_text_from_pdf(file_obj):
    """Extracts text from a PDF file."""
    reader = PdfReader(file_obj)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_obj):
    """Extracts text from a DOCX file."""
    doc = Document(file_obj)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Streamlit UI
st.set_page_config(page_title="Contract Analyzer 📄🔍")

st.title("Contract Analyzer")
st.markdown("### Powered by Gemini Pro API")

# File uploader widget
uploaded_file = st.file_uploader("Upload a contract file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Button to trigger the analysis
if st.button("Analyze Contract"):
    if uploaded_file is not None:
        # Check file size (200 MB = 200 * 1024 * 1024 bytes)
        if uploaded_file.size > 200 * 1024 * 1024:
            st.error("File size exceeds the 200 MB limit. Please upload a smaller file.")
        else:
            # Read the file content
            file_content = uploaded_file.getvalue()
            contract_text = ""

            # Extract text based on file type
            try:
                if uploaded_file.type == "application/pdf":
                    st.info("Extracting text from PDF...")
                    contract_text = extract_text_from_pdf(io.BytesIO(file_content))
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    st.info("Extracting text from DOCX...")
                    contract_text = extract_text_from_docx(io.BytesIO(file_content))
                elif uploaded_file.type == "text/plain":
                    st.info("Reading text from TXT...")
                    contract_text = file_content.decode("utf-8")
                
                if contract_text:
                    with st.spinner('Analyzing contract... Please wait.⏳'):
                        analysis_data = get_gemini_response(contract_text)
                        
                        if analysis_data:
                            st.success("Analysis Complete! 🎉")
                            
                            # Custom CSS for the colored boxes
                            st.markdown("""
                            <style>
                            .custom-box {
                                border-radius: 5px;
                                padding: 10px;
                                margin-bottom: 10px;
                                border: 1px solid #ddd;
                            }
                            .box-red { background-color: #ffe5e5; }
                            .box-green { background-color: #e5ffe5; }
                            .box-blue { background-color: #e5e5ff; }
                            .box-purple { background-color: #f2e5ff; }
                            .box-orange { background-color: #fff2e5; }
                            .box-pink { background-color: #ffe5f2; }
                            .box-yellow { background-color: #ffffcc; }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            st.header("Key Contract Details")
                            
                            # Create a mapping of key to color class
                            box_colors = {
                                "Contract Type": "box-red",
                                "Address": "box-green",
                                "Entry Date": "box-blue",
                                "Contract Party": "box-purple",
                                "Termination Date": "box-orange",
                                "End of Contract": "box-pink"
                            }
                            
                            # Display key details in colored boxes
                            for key, color_class in box_colors.items():
                                value = analysis_data.get(key, "N/A")
                                # Use columns to create a two-part box for label and value
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.markdown(f'<div class="custom-box {color_class}"><b>{key}</b></div>', unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f'<div class="custom-box {color_class}">{value}</div>', unsafe_allow_html=True)
                                    
                            st.markdown("---")
                            st.header("Full Analysis")
                            
                            # --- General Insights Section ---
                            st.subheader("General Insights")
                            st.info(f"**Executive Summary:** {analysis_data.get('Executive Summary', 'N/A')}")
                            st.info(f"**Scope of Service:** {analysis_data.get('Scope of Service', 'N/A')}")
                            st.info(f"**Responsibilities for Deliverables:** {analysis_data.get('Responsibilities for Deliverables', 'N/A')}")
                            st.info(f"**Payment Schedule:** {analysis_data.get('Payment Schedule', 'N/A')}")
                            st.info(f"**Tax Compliance:** {analysis_data.get('Tax Compliance', 'N/A')}")
                            st.info(f"**Important Dates and Deadlines:** {analysis_data.get('Important Dates and Deadlines', 'N/A')}")
                            st.info(f"**Termination Clauses:** {analysis_data.get('Termination Clauses', 'N/A')}")
                            st.info(f"**Confidentiality and Non-Compete Clause:** {analysis_data.get('Confidentiality and Non-Compete Clause', 'N/A')}")
                            
                            st.markdown("---")
                            
                            # --- Clause Presence Checkboxes ---
                            st.subheader("Clause Presence Check ✅")
                            clauses = analysis_data.get("Clauses Presence", {})
                            
                            # Commercial Clauses
                            st.markdown("##### Commercial Clauses")
                            commercial_clauses = clauses.get("Commercial", {})
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.checkbox("Payment Terms", value=commercial_clauses.get("Payment Terms", "No") == "Yes", disabled=True)
                                st.checkbox("IP (Intellectual Property)", value=commercial_clauses.get("IP", "No") == "Yes", disabled=True)
                            with col2:
                                st.checkbox("Delivery Time", value=commercial_clauses.get("Delivery Time", "No") == "Yes", disabled=True)
                                st.checkbox("Warranty", value=commercial_clauses.get("Warranty", "No") == "Yes", disabled=True)

                            st.markdown("---")
                            
                            # Legal Clauses
                            st.markdown("##### Legal Clauses")
                            legal_clauses = clauses.get("Legal", {})
                            
                            col3, col4 = st.columns(2)
                            with col3:
                                st.checkbox("Indemnification", value=legal_clauses.get("Indemnification", "No") == "Yes", disabled=True)
                                st.checkbox("Termination", value=legal_clauses.get("Termination", "No") == "Yes", disabled=True)
                            with col4:
                                st.checkbox("Confidentiality", value=legal_clauses.get("Confidentiality", "No") == "Yes", disabled=True)
                                st.checkbox("Limitation of Liability", value=legal_clauses.get("Limitation of Liability", "No") == "Yes", disabled=True)
                                
                        else:
                            st.error("Could not analyze the contract. Please check the contract text and your API key.")
                else:
                    st.error("Could not extract any text from the uploaded file. Please ensure the file is not corrupted.")
            
            except Exception as e:
                st.error(f"An error occurred during file processing: {e}")
    else:
        st.warning("Please upload a contract file to analyze.")