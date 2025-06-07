# Returns Processing Agent

## Overview

The **Returns Processing Agent** is an AI-powered solution designed to streamline and automate the return management process in e-commerce and retail. This system reduces the need for manual intervention, enhances fraud detection, and improves defect classification accuracy by leveraging **computer vision, large language models (LLMs), and structured database integration**.

## Features

- **QR Code-Based Purchase Verification**: Extracts purchase details from QR codes uploaded by employees.
- **Defect Classification**: Supports **Packaging, Physical, and Working defects**, enabling targeted return processing.
- **AI-Powered Defect Analysis**: Uses **Llama 3.2-11b Vision Preview Model via Groq API** to analyze defect images.
- **Manual Review Support**: Flags complex cases as **Pending**, sending defect images for human verification.
- **Seamless Database Integration**: Uses **MySQL** for structured storage and query execution.
- **Interactive UI**: Built using **Streamlit**, enabling an intuitive and easy-to-use workflow.

## Workflow

1. **Employee Login**: Secure login to access the system.
2. **QR Code Upload**: Retrieves order details from the QR code.
3. **Defect Type Selection**: Employee categorizes the defect.
4. **Defect Image Upload & Analysis**: AI verifies **Packaging** and **Physical defects**, while **Working defects** require manual entry.
5. **Verification & Manual Correction**: AI-generated defect descriptions can be reviewed or overridden.
6. **Final Return Processing**: Approved returns are logged into the system, and pending cases are sent for manual review.

## Installation

### Prerequisites

Ensure the following dependencies are installed:

- Python 3.8+
- Streamlit
- OpenCV
- NumPy
- Pillow
- Pyzbar (for QR code decoding)
- MySQL Connector
- Groq API SDK
- dotenv (for managing environment variables)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/returns-processing-agent.git
   cd returns-processing-agent

   