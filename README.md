🌍 EcoPredict – AI-Driven ESG Emissions Estimation

EcoPredict is a machine learning-powered web application designed to analyze and estimate environmental waste generation across different regions and locations. The platform leverages data-driven predictive models to identify waste patterns, forecast environmental impact, and support sustainable decision-making. By combining machine learning algorithms with interactive visualizations, EcoPredict helps users understand waste distribution trends, monitor environmental conditions, and gain actionable insights for improving waste management and promoting eco-friendly practices.

🔗 Live Demo: https://ecopredict-26xr.onrender.com/

🚀 Features
Predicts Environmental (E) Scores using AI/ML
Generates ESG-based risk assessment
Supports industry-specific analysis
Real-time prediction interface
Responsive and lightweight web UI
Flask-powered backend API
Random Forest regression model with high accuracy
🧠 Machine Learning

The application uses a Random Forest Regressor trained on ESG containing:

Muncipality Area
Waste type
Waste Quantity in Kg's
Date

The model captures non-linear relationships between financial performance and environmental impact, achieving approximately 96% prediction accuracy during validation.

🛠️ Tech Stack
Backend
Python
Flask
Scikit-learn
Pandas
NumPy
Frontend
HTML5
CSS3
Bootstrap 5
JavaScript
Deployment
Render Cloud Platform
📊 Model Workflow
User inputs company details and ESG indicators
Data preprocessing and feature encoding
ML model predicts Environmental Score
Risk category is generated:
High Risk
Average
Excellent
📌 Challenges Solved
Prevented feature leakage during training
Handled industry imbalance using One-Hot Encoding
Built scalable inference pipeline for deployment
Optimized prediction latency for real-time usage
📷 Preview

Add screenshots here after uploading them to your repository.

![Homepage]<img width="1902" height="922" alt="image" src="https://github.com/user-attachments/assets/23c8a94b-a0e9-4b91-a3e8-0dff9173e42d" />

![Prediction]<img width="1818" height="812" alt="image" src="https://github.com/user-attachments/assets/81ba818f-86ca-4b1b-881a-27df335b1a13" />

⚙️ Installation

Clone the repository:

git clone https://github.com/your-username/ecopredict.git
cd ecopredict

Install dependencies:

pip install -r requirements.txt

Run the Flask application:

python app.py


📂 Project Structure
EcoPredict/
│
├── static/
├── templates/
├── model/
├── app.py
├── requirements.txt
└── README.md
🎯 Future Improvements
Add advanced ESG visualization dashboards
Integrate real-world financial APIs
Support multi-sector ESG forecasting
Add model explainability using SHAP/LIME
Docker and CI/CD deployment pipeline
