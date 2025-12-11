@echo off

echo 🚀 Starting Trading Analysis App...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Install/upgrade requirements
echo 📥 Installing requirements...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.template .env
    echo 📝 Please edit .env file with your API credentials before running the app.
    pause
    exit /b 1
)

REM Start the application
echo 🌟 Starting the application...
echo 📱 Access the app at: http://localhost:5000
python app.py

pause