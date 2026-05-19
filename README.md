🌍 EcoPredict – AI-Driven ESG Emissions Estimation

EcoPredict is a machine learning-powered web application that estimates the Environmental (E) Score of companies using financial and ESG-related indicators. The platform helps ESG analysts and researchers generate actionable sustainability insights even when complete environmental reporting data is unavailable.

🔗 Live Demo: EcoPredict Live App

🚀 Features
Predicts Environmental (E) Scores using AI/ML
Generates ESG-based risk assessment
Supports industry-specific analysis
Real-time prediction interface
Responsive and lightweight web UI
Flask-powered backend API
Random Forest regression model with high accuracy
🧠 Machine Learning

The application uses a Random Forest Regressor trained on ESG and financial datasets containing:

Revenue
Firm Size
Industry Type
Social Score
Governance Score

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

![Homepage](images/homepage.png)
![Prediction](images/prediction.png)
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
👨‍💻 Author

Krishna Koundinya Veeravelly
B.Tech CSE (Data Science)

📄 License

This project is licensed under the MIT License.
