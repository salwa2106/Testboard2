pipeline {
  agent any
  options { timestamps() }

  environment {
    PATH = "C:\\Windows\\System32;C:\\Windows;C:\\Windows\\System32\\WindowsPowerShell\\v1.0;C:\\Program Files\\Docker\\Docker\\resources\\bin;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\nasal\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${PATH}"
    BACKEND_BASE = 'http://127.0.0.1:8001'
    PROJECT_ID   = '1'
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
          .venv\\Scripts\\python.exe -m pip install --upgrade pip
          .venv\\Scripts\\python.exe -m pip install -r requirements.txt
          .venv\\Scripts\\pip.exe uninstall -y app || ver >NUL
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
        writeFile file: 'backend/.env', text: 'DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/testboard'
      }
    }

    stage('Wait for Database') {
      steps {
        script {
          echo "Waiting for PostgreSQL..."
          sleep(time: 30, unit: "SECONDS")
        }
      }
    }

    stage('Run migrations') {
    steps {
      bat '''
      if not exist backend\\alembic.ini (echo Missing alembic.ini & exit /b 1)
      cd backend
      ..\\.venv\\Scripts\\alembic.exe -c alembic.ini upgrade head
    '''
  }
}



    stage('Start API') {
      steps {
        bat '''
          del /Q api.pid api.out api.err 2>NUL
          cd backend
          start /B "" "%WORKSPACE%\\.venv\\Scripts\\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --env-file .env
          cd ..
          ping 127.0.0.1 -n 6 > nul
        '''
      }
    }

    stage('Wait for API') {
      steps {
        script {
          def ready = false
          for (int i = 1; i <= 30; i++) {
            def result = bat(script: 'curl -s http://127.0.0.1:8001/docs > nul 2>&1', returnStatus: true)
            if (result == 0) {
              echo "API is ready!"
              ready = true
              break
            }
            echo "Waiting for API... attempt ${i}/30"
            sleep(time: 1, unit: "SECONDS")
          }
          if (!ready) {
            bat 'type api.err || echo No api.err file'
            error("API did not become ready")
          }
        }
      }
    }

    stage('Run pytest') {
      steps {
        bat '''
          cd backend
          ..\\.venv\\Scripts\\python.exe -m pytest --junitxml=..\\report.xml || exit /b 0
        '''
        junit 'report.xml'
      }
    }
    stage('Get token & upload') {
    steps {
     script {
        bat '''
        curl -X POST "http://127.0.0.1:8001/api/auth/login" -H "Content-Type: application/json" -d "{\\"email\\":\\"%API_USER%\\",\\"password\\":\\"%API_PASS%\\"}" -o token.json
        type token.json
      '''
    }
  }
}



  post {
    always {
      bat '''
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill /PID %%a /F 2>NUL
        if exist backend\\docker-compose.db.yml docker compose -f backend\\docker-compose.db.yml down || ver >NUL
      '''
    }
  }
}