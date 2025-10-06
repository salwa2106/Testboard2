#  TestBoard – QA Management Platform

**TestBoard** is a full-stack QA management system built with **FastAPI**, **React**, and **PostgreSQL**.  
It enables test engineers to create, execute, and track test cases, runs, and results with full visibility.

### Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL  
- **Frontend:** React (TypeScript)  
- **CI/CD:** Jenkins, Docker, GitHub Actions  
- **Testing:** Pytest, Allure, Postman  
- **Infrastructure:** Docker Compose, Virtualenv  

###  CI/CD Pipeline
The Jenkins pipeline automatically:
1. Checks out the repository
2. Creates a virtual environment
3. Installs dependencies
4. Runs database migrations
5. Starts the API
6. Executes Pytest and generates Allure reports
7. Uploads test run data to TestBoard’s backend

### Allure Report Example
(see the image above)
