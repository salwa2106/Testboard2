pipeline {
  agent any
  options { timestamps() }

  environment {
    // Keep system PATH and prepend Docker & Python
    PATH = "C:\\Program Files\\Docker\\Docker\\resources\\bin;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${PATH}"

    // App config
    BACKEND_BASE = 'http://localhost:8000'
    PROJECT_ID   = '1'

    // Jenkins credentials (string/secret text)
    API_USER     = credentials('testboard_user_email')
    API_PASS     = credentials('testboard_user_password')
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Create venv & install deps') {
      steps {
        bat '''
          python --version
          python -m venv .venv
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pip install --upgrade pip
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pip install -r requirements.txt
        '''
      }
    }

    stage('Start DB (Docker)') {
      steps {
        bat '''
          docker compose version || docker-compose version
          docker compose -f backend\\docker-compose.db.yml up -d || docker-compose -f backend\\docker-compose.db.yml up -d
          docker ps
        '''
      }
    }

    stage('Write backend .env') {
      steps {
        // Write only what's needed for your app/alembic.
        // Replace with your real connection or inject via Jenkins credentials.
        writeFile file: 'backend/.env', text: """
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/testboard
""".trim()
      }
    }

    stage('Run migrations') {
      steps {
        bat '''
          cd backend
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m alembic upgrade head
        '''
      }
    }

    stage('Start API') {
      steps {
        // Launch uvicorn with the venv's python and capture PID for clean shutdown
        powershell '''
          $py  = "$env:WORKSPACE\\.venv\\Scripts\\python.exe"
          $pwd = "$env:WORKSPACE\\backend"
          $psi = New-Object System.Diagnostics.ProcessStartInfo
          $psi.FileName         = $py
          $psi.Arguments        = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
          $psi.WorkingDirectory = $pwd
          $psi.UseShellExecute  = $false
          $p = [System.Diagnostics.Process]::Start($psi)
          Set-Content -Path api.pid -Value $p.Id
        '''
      }
    }

    stage('Wait for API') {
      steps {
        powershell '''
          $ok=$false
          for($i=0;$i -lt 60;$i++){
            try{
              Invoke-WebRequest -UseBasicParsing http://localhost:8000/docs | Out-Null
              $ok=$true; break
            }catch{ Start-Sleep -Seconds 1 }
          }
          if(-not $ok){ throw "API did not become ready" }
        '''
      }
    }

    stage('Run pytest (produce JUnit)') {
      steps {
        script {
          def result = bat(script: '''
            "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pytest --junitxml=report.xml
          ''', returnStatus: true)
          if (result != 0) {
            echo "pytest had failures; marking UNSTABLE but continuing"
            currentBuild.result = 'UNSTABLE'
          }
        }
      }
      post {
        always { junit 'report.xml' }
      }
    }

    stage('Get API token') {
      when { expression { currentBuild.result != 'FAILURE' } }
      steps {
        bat '''
          > get_token.py (
            echo import os,requests
            echo u=os.getenv("API_USER"); p=os.getenv("API_PASS")
            echo r=requests.post(os.getenv("BACKEND_BASE") + "/api/auth/login", json={"email":u,"password":p})
            echo print("STATUS", r.status_code); print("BODY", r.text)
            echo r.raise_for_status()
            echo tok=r.json().get("access_token")
            echo assert tok, "No access_token in response"
            echo open("token.txt","w").write(tok)
          )
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" get_token.py
        '''
      }
    }

    stage('Upload JUnit to TestBoard') {
      when { expression { currentBuild.result != 'FAILURE' } }
      steps {
        bat '''
          > upload.py (
            echo import requests,os
            echo t=open("token.txt").read().strip()
            echo u=os.getenv("BACKEND_BASE") + "/api/ingest/junit?project_id=" + os.getenv("PROJECT_ID")
            echo r=requests.post(u, headers={"Authorization": f"Bearer {t}"}, files={"file": open("report.xml","rb")})
            echo print("STATUS", r.status_code); print("BODY", r.text)
            echo r.raise_for_status()
          )
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" upload.py
        '''
      }
    }
  }

  post {
    always {
      // Stop API by PID if still running
      powershell '''
        if (Test-Path api.pid) {
          $pid = Get-Content api.pid
          try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
        }
      '''
      // Bring DB down (compose v2/v1 fallback)
      bat '''
        docker compose -f backend\\docker-compose.db.yml down || docker-compose -f backend\\docker-compose.db.yml down
      '''
      archiveArtifacts artifacts: 'report.xml', onlyIfSuccessful: false
    }
  }
}
