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

      # Free the port if needed
      $lines = cmd /c "netstat -ano | findstr :$port"
      if ($lines) {
        Write-Host "Port $port is in use. Offending PIDs:"
        $procIds = ($lines | ForEach-Object { ($_ -split '\\s+')[-1] } | Select-Object -Unique)
        foreach ($procId in $procIds) {
          if ($procId -match '^[0-9]+$') {
            Write-Host "Killing PID $procId"
            cmd /c "taskkill /PID $procId /F" | Out-Null
          }
        }
      }

      $py   = "$env:WORKSPACE\\.venv\\Scripts\\python.exe"
      $wd   = "$env:WORKSPACE\\backend"
      $args = "-m uvicorn app.main:app --host 0.0.0.0 --port $port --env-file .env"

      # Put logs in WORKSPACE root so later stages can read them
      $logOut = Join-Path $env:WORKSPACE "api.out"
      $logErr = Join-Path $env:WORKSPACE "api.err"

      # Start detached + capture logs
      $p = Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $wd `
                         -WindowStyle Hidden -PassThru `
                         -RedirectStandardOutput $logOut -RedirectStandardError $logErr
      Set-Content -Path (Join-Path $env:WORKSPACE "api.pid") -Value $p.Id
      Write-Host "API server started with PID: $($p.Id) on port $port"

      Start-Sleep -Seconds 2
      # Ensure process didn't crash instantly
      try { Get-Process -Id $p.Id | Out-Null }
      catch {
        Write-Host "Process died immediately. api.err tail:"
        if (Test-Path $logErr) { Get-Content $logErr -Tail 80 }
        throw "Uvicorn process exited during startup."
      }

      Write-Host "Netstat after start:"
      cmd /c "netstat -ano | findstr :$port" | Write-Host
    '''
  }
}

stage('Smoke check API') {
  steps {
    powershell '''
      try {
        (Invoke-WebRequest -UseBasicParsing "http://localhost:8001/docs" -TimeoutSec 2) | Out-Null
        Write-Host "Smoke check OK (docs reachable)"
      } catch {
        Write-Host "Smoke check not ready; moving to full wait..."
      }
    '''
  }
}






    stage('Wait for API') {
     options { timeout(time: 90, unit: 'SECONDS') }   // hard cap so it never “hangs”
      steps {
       powershell '''
      $url = "http://localhost:8001/docs"
      $ok = $false
      for($i=0; $i -lt 60; $i++){
        try {
          (Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 2) | Out-Null
          Write-Host "API is up at $url"
          $ok = $true
          break
        } catch {
          if ($i % 5 -eq 0) {
            Write-Host ("Still waiting... ({0}s)" -f $i)
            Write-Host "netstat snapshot:"; cmd /c "netstat -ano | findstr :8001" | Write-Host
            if (Test-Path api.err) { Write-Host "api.err (last 5):"; Get-Content api.err -Tail 5 }
          }
          Start-Sleep -Seconds 1
        }
      }
      if(-not $ok){
        Write-Host "---- api.err (last 100) ----"; if(Test-Path api.err){ Get-Content api.err -Tail 100 } else { Write-Host "(no api.err yet)" }
        Write-Host "---- api.out (last 100) ----"; if(Test-Path api.out){ Get-Content api.out -Tail 100 } else { Write-Host "(no api.out yet)" }
        Write-Host "---- who uses :8001 ----"; cmd /c "netstat -ano | findstr :8001" | Write-Host
        throw "API did not become ready at $url"
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