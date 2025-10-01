pipeline {
  agent any
  options { timestamps() }

  environment {
    // Ensure system dirs, PowerShell, Docker & Python are on PATH (order matters)
    PATH = "C:\\Windows\\System32;C:\\Windows;C:\\Windows\\System32\\WindowsPowerShell\\v1.0;C:\\Program Files\\Docker\\Docker\\resources\\bin;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${PATH}"
    POWERSHELL_EXE = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"

    BACKEND_BASE = 'http://localhost:8001'
    PROJECT_ID   = '1'
    API_USER     = credentials('testboard_user_email')
    API_PASS     = credentials('testboard_user_password')
  }

  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Create venv & install deps') {
      steps {
        bat '''
          python --version
          python -m venv .venv
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pip install --upgrade pip
          "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pip install -r requirements.txt
          rem Just in case: remove wrong PyPI 'app' package if ever installed
          "%WORKSPACE%\\.venv\\Scripts\\pip.exe" uninstall -y app || ver >NUL
        '''
      }
    }

    stage('Ensure DB running') {
      steps {
        bat '''
          if exist backend\\docker-compose.db.yml (
            docker compose -f backend\\docker-compose.db.yml up -d || docker-compose -f backend\\docker-compose.db.yml up -d
          ) else (
            docker inspect backend-db-1 >NUL 2>&1 || docker run -d --name backend-db-1 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=testboard -p 5432:5432 postgres:16
            docker start backend-db-1 >NUL 2>&1
          )
          docker ps
        '''
      }
    }

    stage('Write backend .env') {
      steps {
        writeFile file: 'backend/.env', text: """
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/testboard
""".trim()
      }
    }

    stage('Wait for Database') {
      steps {
        script {
          echo "Waiting for PostgreSQL database to initialize..."
          sleep(time: 30, unit: "SECONDS")
          echo "Database wait complete - proceeding with migrations"
        }
      }
    }

    stage('Run migrations') {
      steps {
        bat '''
          if not exist backend\\alembic.ini (echo "backend\\alembic.ini missing" & exit /b 1)
          echo "Running database migrations..."
          pushd backend
          echo --- Current working dir ---
          cd
          echo --- List files ---
          dir
          echo --- Show alembic.ini content (first lines) ---
          type alembic.ini | findstr /C:"script_location"
          echo --- Show alembic folder ---
          dir alembic
          ..\\.venv\\Scripts\\alembic.exe -c alembic.ini current || ver >NUL
          ..\\.venv\\Scripts\\alembic.exe -c alembic.ini upgrade head
         popd
        '''
      }
    }

    stage('Start API') {
     steps {
      bat 'del /Q api.pid 2>NUL'
      powershell '''
      $port = 8001

      # Free the port if something is already listening (prevents hangs)
      $lines = cmd /c "netstat -ano | findstr :$port"
      if ($lines) {
        Write-Host "Port $port is in use. Offending PIDs:"
        $procIds = ($lines | ForEach-Object { ($_ -split '\\s+')[-1] } | Select-Object -Unique)
        foreach ($procId in $procIds) {
          Write-Host "Killing PID $procId"
          cmd /c "taskkill /PID $procId /F" | Out-Null
        }
      }

      $py  = "$env:WORKSPACE\\.venv\\Scripts\\python.exe"
      $wd  = "$env:WORKSPACE\\backend"
      # Working dir is backend → .env is local here
      $arg = "-m uvicorn app.main:app --host 0.0.0.0 --port $port --env-file .env"

      # Detach and capture logs
      $p = Start-Process -FilePath $py -ArgumentList $arg -WorkingDirectory $wd `
                         -WindowStyle Hidden -PassThru `
                         -RedirectStandardOutput "api.out" -RedirectStandardError "api.err"
      Set-Content -Path "api.pid" -Value $p.Id
      Write-Host "API server started with PID: $($p.Id) on port $port"
    '''
  }
}



    stage('Wait for API') {
    steps {
     powershell '''
      $url = "http://localhost:8001/docs"
      $ok = $false
      for($i=0; $i -lt 60; $i++){
        try { Invoke-WebRequest -UseBasicParsing $url | Out-Null; $ok = $true; break }
        catch { Start-Sleep -Seconds 1; if($i % 10 -eq 0){ Write-Host "Waiting for API... ($i s)" } }
      }
      if(-not $ok){
        Write-Host "---- api.err (last 80) ----"; if(Test-Path api.err){ Get-Content api.err -Tail 80 } else { Write-Host "(no api.err)" }
        Write-Host "---- api.out (last 80) ----"; if(Test-Path api.out){ Get-Content api.out -Tail 80 } else { Write-Host "(no api.out)" }
        throw "API did not become ready at $url"
      } else {
        Write-Host "API is up at $url"
      }
    '''
  }
}


    stage('Run pytest (produce JUnit)') {
      steps {
        script {
          def result = bat(script: '''
            cd backend
            copy .env ..\\backend.env 2>NUL || echo "No .env file to copy"
            "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pytest --junitxml=../report.xml
          ''', returnStatus: true)
          if (result != 0) {
            echo "pytest had failures; marking UNSTABLE but continuing"
            currentBuild.result = 'UNSTABLE'
          }
        }
      }
      post { always { junit 'report.xml' } }
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
     bat '''
        if exist api.pid (
        for /f %%p in (api.pid) do taskkill /PID %%p /F >NUL 2>&1
       )
         if exist backend\\docker-compose.db.yml (
         docker compose -f backend\\docker-compose.db.yml down || docker-compose -f backend\\docker-compose.db.yml down || ver >NUL
       )
    '''
      archiveArtifacts artifacts: 'report.xml', onlyIfSuccessful: false
  }
}

}